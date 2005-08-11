##############################################################################
#
# Copyright (c) 2001 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################

def manage_addVocabulary(id, title, globbing=None, REQUEST=None):
    """

    Add a Vocabulary object to an ObjectManager.

    """





class Vocabulary:
    """

    A Vocabulary manages words and language rules for text indexing.
    Text indexing is done by the ZCatalog and other third party
    Products.

    """

    __constructor__=manage_addVocabulary

    def query(pattern):
        """

        Query Vocabulary for words matching pattern.

        """


    def insert(word):
        """

        Insert a word in the Vocabulary.

        """

    def words():
        """

        Return list of words.

        """
