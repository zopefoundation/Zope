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
from Interface import verify_class_implementation
from AccessControl.SecurityInfo import ClassSecurityInfo

from Products.PluginIndexes.common.PluggableIndex \
     import PluggableIndexInterface
from Products.PluginIndexes.common.util import parseIndexRequest

from Products.ZCTextIndex.OkapiIndex import Index
from Products.ZCTextIndex.ILexicon import ILexicon
from Products.ZCTextIndex.Lexicon \
     import Lexicon, Splitter, CaseNormalizer, StopWordRemover
from Products.ZCTextIndex.NBest import NBest
from Products.ZCTextIndex.QueryParser import QueryParser

class ZCTextIndex(Persistent, Acquisition.Implicit, SimpleItem):
    """Persistent TextIndex"""

    __implements__ = PluggableIndexInterface

    meta_type = 'ZCTextIndex'

    manage_options= (
        {'label': 'Settings', 'action': 'manage_main'},
    )

    query_options = ['query']

    def __init__(self, id, extra, caller, index_factory=Index):
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
        self.index = index_factory(self.lexicon)

    ## Pluggable Index APIs ##

    def index_object(self, docid, obj, threshold=None):
        # XXX We currently ignore subtransaction threshold
        count = self.index.index_doc(docid, self._get_object_text(obj))
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
        tree = QueryParser().parseQuery(query_str)
        results = tree.executeQuery(self.index)
        return  results, (self._fieldname,)

    def query(self, query, nbest=10):
        # returns a mapping from docids to scores
        tree = QueryParser().parseQuery(query)
        results = tree.executeQuery(self.index)
        chooser = NBest(nbest)
        chooser.addmany(results.items())
        return chooser.getbest()

    def numObjects(self):
        """Return number of object indexed"""
        return self.index.length()

    def getEntryForObject(self, documentId, default=None):
        """Return the list of words indexed for documentId"""
        try:
            word_ids = self.index.get_words(documentId)
        except KeyError:
            return default
        get_word = self.lexicon.get_word
        return [get_word(wid) for wid in word_ids]

    def clear(self):
        """reinitialize the index"""
        self.index = Index(self.lexicon)

    def _get_object_text(self, obj):
        x = getattr(obj, self._fieldname)
        if callable(x):
            return x()
        else:
            return x

    ## User Interface Methods ##

    manage_main = DTMLFile('dtml/manageZCTextIndex', globals())

InitializeClass(ZCTextIndex)

def manage_addZCTextIndex(self, id, extra=None, REQUEST=None,
                          RESPONSE=None):
    """Add a text index"""
    return self.manage_addIndex(id, 'ZCTextIndex', extra,
                                REQUEST, RESPONSE, REQUEST.URL3)

manage_addZCTextIndexForm = DTMLFile('dtml/addZCTextIndex', globals())

manage_addLexiconForm = DTMLFile('dtml/addLexicon', globals())

def manage_addLexicon(self, id, title, splitter=None, normalizer=None,
                      stopwords=None, REQUEST=None):
    """Add ZCTextIndex Lexicon"""
    elements = []
    if splitter:
        elements.append(Splitter())
    if normalizer:
        elements.append(CaseNormalizer())
    if stopwords:
        elements.append(StopWordRemover())
    lexicon = PLexicon(id, title, *elements)
    self._setObject(id, lexicon)
    if REQUEST is not None:
        return self.manage_main(self, REQUEST, update_menu=1)

class PLexicon(Lexicon, Persistent, Acquisition.Implicit, SimpleItem):
    """Persistent Lexcion for ZCTextIndex"""

    meta_type = 'ZCTextIndex Lexicon'

    def __init__(self, id, title='', *pipeline):
        self.id = str(id)
        self.title = str(title)
        PLexicon.inheritedAttribute('__init__')(self, *pipeline)

InitializeClass(PLexicon)
