##############################################################################
# 
# Zope Public License (ZPL) Version 1.0
# -------------------------------------
# 
# Copyright (c) Digital Creations.  All rights reserved.
# 
# This license has been certified as Open Source(tm).
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
# 
# 1. Redistributions in source code must retain the above copyright
#    notice, this list of conditions, and the following disclaimer.
# 
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions, and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
# 
# 3. Digital Creations requests that attribution be given to Zope
#    in any manner possible. Zope includes a "Powered by Zope"
#    button that is installed by default. While it is not a license
#    violation to remove this button, it is requested that the
#    attribution remain. A significant investment has been put
#    into Zope, and this effort will continue if the Zope community
#    continues to grow. This is one way to assure that growth.
# 
# 4. All advertising materials and documentation mentioning
#    features derived from or use of this software must display
#    the following acknowledgement:
# 
#      "This product includes software developed by Digital Creations
#      for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
#    In the event that the product being advertised includes an
#    intact Zope distribution (with copyright and license included)
#    then this clause is waived.
# 
# 5. Names associated with Zope or Digital Creations must not be used to
#    endorse or promote products derived from this software without
#    prior written permission from Digital Creations.
# 
# 6. Modified redistributions of any form whatsoever must retain
#    the following acknowledgment:
# 
#      "This product includes software developed by Digital Creations
#      for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
#    Intact (re-)distributions of any official Zope release do not
#    require an external acknowledgement.
# 
# 7. Modifications are encouraged but must be packaged separately as
#    patches to official Zope releases.  Distributions that do not
#    clearly separate the patches from the original work must be clearly
#    labeled as unofficial distributions.  Modifications which do not
#    carry the name Zope may be packaged in any form, as long as they
#    conform to all of the clauses above.
# 
# 
# Disclaimer
# 
#   THIS SOFTWARE IS PROVIDED BY DIGITAL CREATIONS ``AS IS'' AND ANY
#   EXPRESSED OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
#   IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
#   PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL DIGITAL CREATIONS OR ITS
#   CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
#   SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
#   LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF
#   USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#   ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
#   OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT
#   OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
#   SUCH DAMAGE.
# 
# 
# This software consists of contributions made by Digital Creations and
# many individuals on behalf of Digital Creations.  Specific
# attributions are listed in the accompanying credits file.
# 
##############################################################################
"""ZCatalog product"""

from Globals import DTMLFile, MessageDialog
import Globals, AccessControl.Role
from Acquisition import Implicit
from Persistence import Persistent
from OFS.SimpleItem import Item
from Products.PluginIndexes.TextIndex import Lexicon, GlobbingLexicon
from Products.PluginIndexes.TextIndex.Lexicon import stop_word_dict
from Products.PluginIndexes.TextIndex import Splitter

manage_addVocabularyForm=DTMLFile('dtml/addVocabulary',globals())

def manage_addVocabulary(self, id, title, globbing=None, splitter='', REQUEST=None):
    """Add a Vocabulary object
    """
    id=str(id)
    title=str(title)
    if globbing: globbing=1
    
    c=Vocabulary(id, title, globbing,splitter)
    self._setObject(id, c)
    if REQUEST is not None:
        return self.manage_main(self,REQUEST)


class Vocabulary(Item, Persistent, Implicit,
                 AccessControl.Role.RoleManager,
                 ):
    """
    A Vocabulary is a user-managable realization of a Lexicon object.

    """

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
         ['manage_main', 'manage_vocab', 'manage_query'], 
         ['Manager']),

        ('Query Vocabulary',
         ['query',],
         ['Anonymous', 'Manager']), 
        )

    

    manage_main = DTMLFile('dtml/manage_vocab', globals())
    manage_query = DTMLFile('dtml/vocab_query', globals())

    def __init__(self, id, title='', globbing=None,splitter=None):
        """ create the lexicon to manage... """
        self.id = id
        self.title = title
        self.globbing = not not globbing
            
        self.useSplitter = Splitter.splitterNames[0]    
        if splitter:
            self.useSplitter = splitter

        if globbing:
            self.lexicon = GlobbingLexicon.GlobbingLexicon(useSplitter=self.useSplitter)
        else:
            self.lexicon = Lexicon.Lexicon(stop_word_dict,useSplitter=self.useSplitter)

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
        return result
            

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

    










