##############################################################################
#
# Copyright (c) 2002 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################

"""Plug in text index for ZCatalog with relevance ranking."""

import ZODB
from Persistence import Persistent
import Acquisition
from OFS.SimpleItem import SimpleItem

from Globals import DTMLFile, InitializeClass
from AccessControl.SecurityInfo import ClassSecurityInfo

from Products.PluginIndexes.common.PluggableIndex import \
     PluggableIndexInterface
from Products.PluginIndexes.common.util import parseIndexRequest

from Products.ZCTextIndex.ILexicon import ILexicon
from Products.ZCTextIndex.Lexicon import \
     Lexicon, Splitter, CaseNormalizer, StopWordRemover
from Products.ZCTextIndex.NBest import NBest
from Products.ZCTextIndex.QueryParser import QueryParser
from PipelineFactory import element_factory

from Products.ZCTextIndex.CosineIndex import CosineIndex
from Products.ZCTextIndex.OkapiIndex import OkapiIndex
index_types = {'Okapi BM25 Rank':OkapiIndex,
               'Cosine Measure':CosineIndex}

class ZCTextIndex(Persistent, Acquisition.Implicit, SimpleItem):
    """Persistent TextIndex"""

    __implements__ = PluggableIndexInterface

    ## Magic class attributes ##

    meta_type = 'ZCTextIndex'

    manage_options = (
        {'label': 'Settings', 'action': 'manage_main'},
    )

    query_options = ['query']

    ## Constructor ##

    def __init__(self, id, extra, caller, index_factory=None):
        self.id = id
        self._fieldname = extra.doc_attr
        lexicon = getattr(caller, extra.lexicon_id, None)

        if lexicon is None:
            raise LookupError, 'Lexicon "%s" not found' % extra.lexicon_id

        if not ILexicon.isImplementedBy(lexicon):
            raise ValueError, \
                'Object "%s" does not implement lexicon interface' \
                % lexicon.getId()

        self.lexicon = lexicon

        if index_factory is None:
            if extra.index_type not in index_types.keys():
                raise ValueError, 'Invalid index type "%s"' % extra.index_type
            self._index_factory = index_types[extra.index_type]
            self._index_type = extra.index_type
        else:
            self._index_factory = index_factory

        self.clear()

    ## External methods not in the Pluggable Index API ##

    def query(self, query, nbest=10):
        """Return pair (mapping from docids to scores, num results).

        The num results is the total number of results before trimming
        to the nbest results.
        """
        tree = QueryParser(self.lexicon).parseQuery(query)
        results = tree.executeQuery(self.index)
        if results is None:
            return [], 0
        chooser = NBest(nbest)
        chooser.addmany(results.items())
        return chooser.getbest(), len(results)

    ## Pluggable Index APIs ##

    def index_object(self, docid, obj, threshold=None):
        # XXX We currently ignore subtransaction threshold
        text = getattr(obj, self._fieldname, None)
        if text is None:
            return 0
        if callable(text):
            text = text()
        count = self.index.index_doc(docid, text)
        self._p_changed = 1 # XXX
        return count

    def unindex_object(self, docid):
        self.index.unindex_doc(docid)
        self._p_changed = 1 # XXX

    def _apply_index(self, request, cid=''):
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
        tree = QueryParser(self.lexicon).parseQuery(query_str)
        results = tree.executeQuery(self.index)
        return  results, (self._fieldname,)

    def getEntryForObject(self, documentId, default=None):
        """Return the list of words indexed for documentId"""
        try:
            word_ids = self.index.get_words(documentId)
        except KeyError:
            return default
        get_word = self.lexicon.get_word
        return [get_word(wid) for wid in word_ids]

    def uniqueValues(self):
        raise NotImplementedError

    ## The ZCatalog Index management screen uses these methods ##

    def numObjects(self):
        """Return number of unique words in the index"""
        return self.index.length()

    def clear(self):
        """reinitialize the index (but not the lexicon)"""
        self.index = self._index_factory(self.lexicon)

    ## User Interface Methods ##

    manage_main = DTMLFile('dtml/manageZCTextIndex', globals())

    def getIndexType(self):
        """Return index type string"""
        return getattr(self, '_index_type', self._index_factory.__name__)

InitializeClass(ZCTextIndex)

def manage_addZCTextIndex(self, id, extra=None, REQUEST=None,
                          RESPONSE=None):
    """Add a text index"""
    return self.manage_addIndex(id, 'ZCTextIndex', extra,
                                REQUEST, RESPONSE, REQUEST.URL3)

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

class PLexicon(Lexicon, Acquisition.Implicit, SimpleItem):
    """Lexicon for ZCTextIndex"""

    meta_type = 'ZCTextIndex Lexicon'

    manage_options = ({'label':'Overview', 'action':'manage_main'},) + \
                     SimpleItem.manage_options

    def __init__(self, id, title='', *pipeline):
        self.id = str(id)
        self.title = str(title)
        PLexicon.inheritedAttribute('__init__')(self, *pipeline)

    ## User Interface Methods ##

    def getPipelineNames(self):
        """Return list of names of pipeline element classes"""
        return [element.__class__.__name__ for element in self._pipeline]

    manage_main = DTMLFile('dtml/manageLexicon', globals())

InitializeClass(PLexicon)
