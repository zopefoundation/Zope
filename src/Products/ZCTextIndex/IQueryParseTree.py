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

"""Query Parser Tree Interface."""

from zope.interface import Interface

class IQueryParseTree(Interface):
    """Interface for parse trees returned by parseQuery()."""

    def nodeType():
        """Return the node type.

        This is one of 'AND', 'OR', 'NOT', 'ATOM', 'PHRASE' or 'GLOB'.
        """

    def getValue():
        """Return a node-type specific value.

        For node type:    Return:
        'AND'             a list of parse trees
        'OR'              a list of parse trees
        'NOT'             a parse tree
        'ATOM'            a string (representing a single search term)
        'PHRASE'          a string (representing a search phrase)
        'GLOB'            a string (representing a pattern, e.g. "foo*")
        """

    def terms():
        """Return a list of all terms in this node, excluding NOT subtrees."""

    def executeQuery(index):
        """Execute the query represented by this node against the index.

        The index argument must implement the IIndex interface.

        Return an IIBucket or IIBTree mapping document ids to scores
        (higher scores mean better results).

        May raise ParseTree.QueryError.
        """
