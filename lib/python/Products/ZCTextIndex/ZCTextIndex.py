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

from Products.PluginIndexes.common.PluggableIndex \
     import PluggableIndexInterface

from Products.ZCTextIndex.Index import Index
from Products.ZCTextIndex.ILexicon import ILexicon
from Products.ZCTextIndex.NBest import NBest
from Products.ZCTextIndex.QueryParser import QueryParser
from Globals import DTMLFile
from Interface import verify_class_implementation

class ZCTextIndex(Persistent, Acquisition.Implicit, SimpleItem):
    __implements__ = PluggableIndexInterface
    
    meta_type = 'ZCTextIndex'
    
    manage_options= (
        {'label': 'Settings', 'action': 'manage_main'},
    )

    def __init__(self, id, extra, caller):
        self.id = id
        self._fieldname = extra.doc_attr
        lexicon = getattr(caller, extra.lexicon_id, None)
        
        if lexicon is None:
            raise LookupError, 'Lexicon "%s" not found' % extra.lexicon_id
            
        verify_class_implementation(ILexicon, lexicon.__class__)
            
        self.lexicon = lexicon
        self.index = Index(self.lexicon)
        self.parser = QueryParser()

    def index_object(self, docid, obj):
        self.index.index_doc(docid, self._get_object_text(obj))
        self._p_changed = 1 # XXX

    def unindex_object(self, docid):
        self.index.unindex_doc(docid)
        self._p_changed = 1 # XXX

    def _apply_index(self, req):
        pass # XXX

    def query(self, query, nbest=10):
        # returns a mapping from docids to scores
        tree = self.parser.parseQuery(query)
        results = tree.executeQuery(self.index)
        chooser = NBest(nbest)
        chooser.addmany(results.items())
        return chooser.getbest()

    def _get_object_text(self, obj):
        x = getattr(obj, self._fieldname)
        if callable(x):
            return x()
        else:
            return x
            
    ## User Interface Methods ##
    
    manage_main = DTMLFile('dtml/manageZCTextIndex', globals())

def manage_addZCTextIndex(self, id, extra=None, REQUEST=None, 
                          RESPONSE=None):
    """Add a text index"""
    return self.manage_addIndex(id, 'ZCTextIndex', extra, 
                                REQUEST, RESPONSE, REQUEST.URL3)

manage_addZCTextIndexForm = DTMLFile('dtml/addZCTextIndex', globals())

manage_addLexiconForm = DTMLFile('dtml/addLexicon', globals())

def manage_addLexicon(self, id, title, splitter=None, normalizer=None,
                      stopword=None, REQUEST=None):
    elements = []
    if splitter:
        elements.append(Lexicon.Splitter())
    if normalizer:
        elements.append(CaseNormalizer())
    if stopwords:
        elements.append(StopWordRemover())
    lexicon = Lexicon(*elements)
    self._setObject(id, lexicon)
    if REQUEST is not None:
        return self.manage_main(self, REQUEST, update_menu=1)
