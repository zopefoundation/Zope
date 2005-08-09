##############################################################################
#
# Copyright (c) 2001 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Vocabulary for deprecated text index.

$Id$
"""

from Globals import DTMLFile, MessageDialog
import Globals, AccessControl.Role
from Acquisition import Implicit
from Persistence import Persistent
from OFS.SimpleItem import Item
from zope.interface import implements

from Products.PluginIndexes.interfaces import IVocabulary
from Products.PluginIndexes.TextIndex import Lexicon, GlobbingLexicon
from Products.PluginIndexes.TextIndex.Lexicon import stop_word_dict
from Products.PluginIndexes.TextIndex import Splitter

manage_addVocabularyForm=DTMLFile('dtml/addVocabulary',globals())

def manage_addVocabulary(self, id, title, globbing=None, extra=None,
                         splitter='', REQUEST=None):
    """Add a Vocabulary object
    """
    id=str(id)
    title=str(title)
    if globbing: globbing=1

    c=Vocabulary(id, title, globbing,splitter,extra)
    self._setObject(id, c)
    if REQUEST is not None:
        return self.manage_main(self,REQUEST,update_menu=1)

class _extra: pass


class Vocabulary(Item, Persistent, Implicit, AccessControl.Role.RoleManager):

    """A Vocabulary is a user-managable realization of a Lexicon object.
    """

    implements(IVocabulary)

    meta_type = "Vocabulary"
    _isAVocabulary = 1

    manage_options=(
        (
        {'label': 'Vocabulary', 'action': 'manage_main',
         'help' : ('ZCatalog', 'Vocabulary_Vocabulary.stx')},
        {'label': 'Query', 'action': 'manage_query',
         'help': ('ZCatalog', 'Vocabulary_Query.stx')},
        )
        +Item.manage_options
        +AccessControl.Role.RoleManager.manage_options
        )

    __ac_permissions__=(

        ('Manage Vocabulary',
         ['manage_main', 'manage_query'],
         ['Manager']),

        ('Query Vocabulary',
         ['query',],
         ['Anonymous', 'Manager']),
        )

    manage_main = DTMLFile('dtml/manage_vocab', globals())
    manage_query = DTMLFile('dtml/vocab_query', globals())

    def __init__(self, id, title='', globbing=None,splitter=None,extra=None):
        """ create the lexicon to manage... """
        self.id = id
        self.title = title
        self.globbing = not not globbing

        self.useSplitter = Splitter.splitterNames[0]
        if splitter:
            self.useSplitter = splitter

        if not extra:
            extra = _extra()
            extra.splitterIndexNumbers = 0
            extra.splitterSingleChars  = 0
            extra.splitterCasefolding  = 1

        if globbing:
            self.lexicon = GlobbingLexicon.GlobbingLexicon(
                                useSplitter=self.useSplitter,extra=extra)
        else:
            self.lexicon = Lexicon.Lexicon(stop_word_dict,
                                useSplitter=self.useSplitter,extra=extra)

    def getLexicon(self):
        return self.lexicon

    def query(self, pattern):
        """ """
        result = []
        for x in self.lexicon.get(pattern):
            if self.globbing:
                result.append(self.lexicon._inverseLex[x])
            else:
                result.append(pattern)

        return str(result)

    def manage_insert(self, word='', URL1=None, RESPONSE=None):
        """ doc string """
        self.insert(word)

        if RESPONSE:
            RESPONSE.redirect(URL1 + '/manage_main')

    def manage_stop_syn(self, stop_syn, REQUEST=None):
        pass

    def insert(self, word=''):
        self.lexicon.set(word)

    def words(self):
        return self.lexicon._lexicon.items()
