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

from Interface import Base as Interface

class ILexicon(Interface):
    """Object responsible for converting text to word identifiers."""

    def termToWordIds(text):
        """Return a sequence of ids of the words parsed from the text.

        The input text may be either a string or a list of strings.

        Parses the text as if they are search terms, and skips words that
        aren't in the lexicon.
        """

    def sourceToWordIds(text):
        """Return a sequence of ids of the words parsed from the text.

        The input text may be either a string or a list of strings.

        Parses the text as if they come from a source document, and creates
        new word ids for words that aren't (yet) in the lexicon.
        """

    def globToWordIds(pattern):
        """Return a sequence of ids of words matching the pattern.

        The argument should be a single word using globbing syntax,
        e.g. 'foo*' meaning anything starting with 'foo'.

        NOTE: Currently only a single trailing * is supported.

        Returns the wids for all words in the lexicon that match the
        pattern.
        """

    def length():
        """Return the number of unique term in the lexicon."""
