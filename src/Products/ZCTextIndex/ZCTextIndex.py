##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Plug in text index for ZCatalog with relevance ranking.

$Id$
"""

from cgi import escape

from AccessControl.Permissions import manage_vocabulary
from AccessControl.Permissions import manage_zcatalog_indexes
from AccessControl.Permissions import query_vocabulary
from AccessControl.Permissions import search_zcatalog
from AccessControl.SecurityInfo import ClassSecurityInfo
from Acquisition import aq_base
from Acquisition import aq_inner
from Acquisition import aq_parent
from Acquisition import Implicit
from App.class_init import InitializeClass
from App.special_dtml import DTMLFile
from OFS.SimpleItem import SimpleItem
from Persistence import Persistent
from zope.interface import implements

from Products.PluginIndexes.common.util import parseIndexRequest
from Products.PluginIndexes.common import safe_callable
from Products.PluginIndexes.interfaces import IPluggableIndex

from Products.ZCTextIndex.Lexicon import CaseNormalizer
from Products.ZCTextIndex.Lexicon import Lexicon
from Products.ZCTextIndex.Lexicon import Splitter
from Products.ZCTextIndex.Lexicon import StopWordRemover
from Products.ZCTextIndex.NBest import NBest
from Products.ZCTextIndex.QueryParser import QueryParser
from Products.ZCTextIndex.CosineIndex import CosineIndex
from Products.ZCTextIndex.interfaces import ILexicon
from Products.ZCTextIndex.interfaces import IZCLexicon
from Products.ZCTextIndex.interfaces import IZCTextIndex
from Products.ZCTextIndex.OkapiIndex import OkapiIndex
from Products.ZCTextIndex.PipelineFactory import element_factory

index_types = {'Okapi BM25 Rank':OkapiIndex,
               'Cosine Measure':CosineIndex}


class ZCTextIndex(Persistent, Implicit, SimpleItem):

    """Persistent text index.
    """
    implements(IZCTextIndex, IPluggableIndex)

    ## Magic class attributes ##

    meta_type = 'ZCTextIndex'
    query_options = ('query',)

    manage_options = (
        {'label': 'Overview', 'action': 'manage_main'},
    )

    security = ClassSecurityInfo()
    security.declareObjectProtected(manage_zcatalog_indexes)

    ## Constructor ##

    def __init__(self, id, extra=None, caller=None, index_factory=None,
                 field_name=None, lexicon_id=None):
        self.id = id

        # Arguments can be passed directly to the constructor or
        # via the silly "extra" record.
        self._fieldname = field_name or getattr(extra, 'doc_attr', '') or id
        self._indexed_attrs = self._fieldname.split(',')
        self._indexed_attrs = [ attr.strip()
                                for attr in self._indexed_attrs if attr ]

        lexicon_id = lexicon_id or getattr(extra, 'lexicon_id', '')
        lexicon = getattr(caller, lexicon_id, None)

        if lexicon is None:
            raise LookupError, 'Lexicon "%s" not found' % escape(lexicon_id)

        if not ILexicon.providedBy(lexicon):
            raise ValueError('Object "%s" does not implement '
                             'ZCTextIndex Lexicon interface'
                             % lexicon.getId())

        self.lexicon_id = lexicon.getId()
        self._v_lexicon = lexicon

        if index_factory is None:
            if extra.index_type not in index_types.keys():
                raise ValueError, 'Invalid index type "%s"' % escape(
                    extra.index_type)
            self._index_factory = index_types[extra.index_type]
            self._index_type = extra.index_type
        else:
            self._index_factory = index_factory

        self.index = self._index_factory(aq_base(self.getLexicon()))

    ## Private Methods ##

    security.declarePrivate('getLexicon')

    def getLexicon(self):
        """Get the lexicon for this index
        """
        if hasattr(aq_base(self), 'lexicon'):
            # Fix up old ZCTextIndexes by removing direct lexicon ref
            # and changing it to an ID
            lexicon = getattr(aq_parent(aq_inner(self)), self.lexicon.getId())
            self.lexicon_id = lexicon.getId()
            del self.lexicon

        if getattr(aq_base(self), 'lexicon_path', None):
            # Fix up slightly less old ZCTextIndexes by removing
            # the physical path and changing it to an ID.
            # There's no need to use a physical path, which otherwise
            # makes it difficult to move or rename ZCatalogs.
            self.lexicon_id = self.lexicon_path[-1]
            del self.lexicon_path

        try:
            return self._v_lexicon
        except AttributeError:
            lexicon = getattr(aq_parent(aq_inner(self)), self.lexicon_id)
            if not ILexicon.providedBy(lexicon):
                raise TypeError('Object "%s" is not a ZCTextIndex Lexicon'
                                % repr(lexicon))
            self._v_lexicon = lexicon
            return lexicon

    ## External methods not in the Pluggable Index API ##

    security.declareProtected(search_zcatalog, 'query')

    def query(self, query, nbest=10):
        """Return pair (mapping from docids to scores, num results).

        The num results is the total number of results before trimming
        to the nbest results.
        """
        tree = QueryParser(self.getLexicon()).parseQuery(query)
        results = tree.executeQuery(self.index)
        if results is None:
            return [], 0
        chooser = NBest(nbest)
        chooser.addmany(results.items())
        return chooser.getbest(), len(results)

    ## Pluggable Index APIs ##

    def index_object(self, documentId, obj, threshold=None):
        """Wrapper for  index_doc()  handling indexing of multiple attributes.

        Enter the document with the specified documentId in the index
        under the terms extracted from the indexed text attributes,
        each of which should yield either a string or a list of
        strings (Unicode or otherwise) to be passed to index_doc().
        """
        # XXX We currently ignore subtransaction threshold

        # needed for backward compatibility
        try: fields = self._indexed_attrs
        except: fields  = [ self._fieldname ]

        res = 0
        all_texts = []
        for attr in fields:
            text = getattr(obj, attr, None)
            if text is None:
                continue
            if safe_callable(text):
                text = text()
            if text is None:
                continue
            if text:
                if isinstance(text, (list, tuple, )):
                    all_texts.extend(text)
                else:
                    all_texts.append(text)

        # Check that we're sending only strings
        all_texts = filter(lambda text: isinstance(text, basestring), \
                           all_texts)
        if all_texts:
            return self.index.index_doc(documentId, all_texts)
        return res

    def unindex_object(self, docid):
        if self.index.has_doc(docid):
            self.index.unindex_doc(docid)

    def _apply_index(self, request):
        """Apply query specified by request, a mapping containing the query.

        Returns two object on success, the resultSet containing the
        matching record numbers and a tuple containing the names of
        the fields used

        Returns None if request is not valid for this index.
        """
        record = parseIndexRequest(request, self.id, self.query_options)
        if record.keys is None:
            return None

        query_str = ' '.join(record.keys)
        if not query_str:
            return None
        tree = QueryParser(self.getLexicon()).parseQuery(query_str)
        results = tree.executeQuery(self.index)
        return  results, (self.id,)

    def getEntryForObject(self, documentId, default=None):
        """Return the list of words indexed for documentId"""
        try:
            word_ids = self.index.get_words(documentId)
        except KeyError:
            return default
        get_word = self.getLexicon().get_word
        return [get_word(wid) for wid in word_ids]

    def uniqueValues(self, name=None, withLengths=0):
        raise NotImplementedError

    ## The ZCatalog Index management screen uses these methods ##

    def numObjects(self):
        """Return number of unique words in the index"""
        return self.index.length()

    def indexSize(self):
        """Return the number of indexes objects """
        return self.index.document_count()

    def clear(self):
        """reinitialize the index (but not the lexicon)"""
        try:
            # Remove the cached reference to the lexicon
            # So that it is refreshed
            del self._v_lexicon
        except (AttributeError, KeyError):
            pass
        self.index = self._index_factory(aq_base(self.getLexicon()))

    ## User Interface Methods ##

    manage_main = DTMLFile('dtml/manageZCTextIndex', globals())

    def getIndexSourceNames(self):
        """Return sequence of names of indexed attributes"""
        try:
            return self._indexed_attrs
        except:
            return [self._fieldname]

    def getIndexType(self):
        """Return index type string"""
        return getattr(self, '_index_type', self._index_factory.__name__)

    def getLexiconURL(self):
        """Return the url of the lexicon used by the index"""
        try:
            lex = self.getLexicon()
        except (KeyError, AttributeError):
            return None
        else:
            return lex.absolute_url()

InitializeClass(ZCTextIndex)

def manage_addZCTextIndex(self, id, extra=None, REQUEST=None,
                          RESPONSE=None):
    """Add a text index"""
    if REQUEST is None:
        URL3 = None
    else:
        URL3 = REQUEST.URL3
    return self.manage_addIndex(id, 'ZCTextIndex', extra,
                                REQUEST, RESPONSE, URL3)

manage_addZCTextIndexForm = DTMLFile('dtml/addZCTextIndex', globals())

manage_addLexiconForm = DTMLFile('dtml/addLexicon', globals())

def manage_addLexicon(self, id, title='', elements=[], REQUEST=None):
    """Add ZCTextIndex Lexicon"""

    pipeline = []
    for el_record in elements:
        if not hasattr(el_record, 'name'):
            continue # Skip over records that only specify element group
        element = element_factory.instantiate(el_record.group, el_record.name)
        if element is not None:
            if el_record.group == 'Word Splitter':
                # I don't like hardcoding this, but its a simple solution
                # to get the splitter element first in the pipeline
                pipeline.insert(0, element)
            else:
                pipeline.append(element)

    lexicon = PLexicon(id, title, *pipeline)
    self._setObject(id, lexicon)
    if REQUEST is not None:
        return self.manage_main(self, REQUEST, update_menu=1)

# I am borrowing the existing vocabulary permissions for now to avoid
# adding new permissions. This may change when old style Vocabs go away
LexiconQueryPerm = query_vocabulary
LexiconMgmtPerm = manage_vocabulary


class PLexicon(Lexicon, Implicit, SimpleItem):

    """Lexicon for ZCTextIndex.
    """

    implements(IZCLexicon)

    meta_type = 'ZCTextIndex Lexicon'

    manage_options = ({'label':'Overview', 'action':'manage_main'},
                      {'label':'Query', 'action':'queryLexicon'},
                     ) + SimpleItem.manage_options

    security = ClassSecurityInfo()
    security.declareObjectProtected(LexiconQueryPerm)

    def __init__(self, id, title='', *pipeline):
        self.id = str(id)
        self.title = str(title)
        PLexicon.inheritedAttribute('__init__')(self, *pipeline)

    ## User Interface Methods ##

    def getPipelineNames(self):
        """Return list of names of pipeline element classes"""
        return [element.__class__.__name__ for element in self._pipeline]

    _queryLexicon = DTMLFile('dtml/queryLexicon', globals())

    security.declareProtected(LexiconQueryPerm, 'queryLexicon')

    def queryLexicon(self, REQUEST, words=None, page=0, rows=20, cols=4):
        """Lexicon browser/query user interface
        """
        if words:
            wids = []
            for word in self.parseTerms(words):
                wids.extend(self.globToWordIds(word))
            words = [self.get_word(wid) for wid in wids]
        else:
            words = self.words()

        word_count = len(words)
        rows = max(min(rows, 500), 1)
        cols = max(min(cols, 12), 1)
        page_count = word_count / (rows * cols) + \
                     (word_count % (rows * cols) > 0)
        page = max(min(page, page_count - 1), 0)
        start = rows * cols * page
        end = min(rows * cols * (page + 1), word_count)

        if word_count:
            words = list(words[start:end])
        else:
            words = []

        columns = []
        i = 0
        while i < len(words):
            columns.append(words[i:i + rows])
            i += rows

        info = dict(page=page,
                    rows=rows,
                    cols=cols,
                    start_word=start+1,
                    end_word=end,
                    word_count=word_count,
                    page_count=page_count,
                    page_range=xrange(page_count),
                    page_columns=columns)

        if REQUEST is not None:
            return self._queryLexicon(self, REQUEST, **info)

        return info

    security.declareProtected(LexiconMgmtPerm, 'manage_main')
    manage_main = DTMLFile('dtml/manageLexicon', globals())

InitializeClass(PLexicon)
