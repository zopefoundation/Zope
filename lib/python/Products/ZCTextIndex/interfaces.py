##############################################################################
#
# Copyright (c) 2005 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""ZCTextIndex z3 interfaces.

$Id$
"""

from zope.interface import Interface


class IZCTextIndex(Interface):

    """Persistent text index.
    """


class ILexicon(Interface):

    """Object responsible for converting text to word identifiers.
    """

    def termToWordIds(text):
        """Return a sequence of ids of the words parsed from the text.

        The input text may be either a string or a list of strings.

        Parse the text as if they are search terms, and skips words
        that aren't in the lexicon.
        """

    def sourceToWordIds(text):
        """Return a sequence of ids of the words parsed from the text.

        The input text may be either a string or a list of strings.

        Parse the text as if they come from a source document, and
        creates new word ids for words that aren't (yet) in the
        lexicon.
        """

    def globToWordIds(pattern):
        """Return a sequence of ids of words matching the pattern.

        The argument should be a single word using globbing syntax,
        e.g. 'foo*' meaning anything starting with 'foo'.

        Return the wids for all words in the lexicon that match the
        pattern.
        """

    def length():
        """Return the number of unique term in the lexicon.
        """

    def get_word(wid):
        """Return the word for the given word id.

        Raise KeyError if the word id is not in the lexicon.
        """

    def get_wid(word):
        """Return the wird id for the given word.

        Return 0 of the word is not in the lexicon.
        """

    def parseTerms(text):
        """Pass the text through the pipeline.

        Return a list of words, normalized by the pipeline
        (e.g. stopwords removed, case normalized etc.).
        """

    def isGlob(word):
        """Return true if the word is a globbing pattern.

        The word should be one of the words returned by parseTerm().
        """


class IZCLexicon(Interface):

    """Lexicon for ZCTextIndex.
    """
