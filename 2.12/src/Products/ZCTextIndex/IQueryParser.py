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

"""Query Parser Interface."""

from zope.interface import Interface

class IQueryParser(Interface):
    """Interface for Query Parsers."""

    def parseQuery(query):
        """Parse a query string.

        Return a parse tree (which implements IQueryParseTree).

        Some of the query terms may be ignored because they are
        stopwords; use getIgnored() to find out which terms were
        ignored.  But if the entire query consists only of stop words,
        or of stopwords and one or more negated terms, an exception is
        raised.

        May raise ParseTree.ParseError.
        """

    def getIgnored():
        """Return the list of ignored terms.

        Return the list of terms that were ignored by the most recent
        call to parseQuery() because they were stopwords.

        If parseQuery() was never called this returns None.
        """

    def parseQueryEx(query):
        """Parse a query string.

        Return a tuple (tree, ignored) where 'tree' is the parse tree
        as returned by parseQuery(), and 'ignored' is a list of
        ignored terms as returned by getIgnored().

        May raise ParseTree.ParseError.
        """
