##############################################################################
#
# Copyright (c) 2001, 2002 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################

"""Generic parser support: exception and parse tree nodes."""

from BTrees.IIBTree import difference, weightedIntersection, weightedUnion
from Products.ZCTextIndex.NBest import NBest

class QueryError(Exception):
    pass

class ParseError(Exception):
    pass

class ParseTreeNode:

    _nodeType = None

    def __init__(self, value):
        self._value = value

    def nodeType(self):
        return self._nodeType

    def getValue(self):
        return self._value

    def __repr__(self):
        return "%s(%r)" % (self.__class__.__name__, self.getValue())

    def terms(self):
        t = []
        for v in self.getValue():
            t.extend(v.terms())
        return t

    def executeQuery(self, index):
        raise NotImplementedError

class NotNode(ParseTreeNode):

    _nodeType = "NOT"

    def terms(self):
        return []

    def executeQuery(self, index):
        raise QueryError, "NOT operator must occur right after AND"

class AndNode(ParseTreeNode):

    _nodeType = "AND"

    def executeQuery(self, index):
        L = []
        Nots = []
        for subnode in self.getValue():
            if subnode.nodeType() == "NOT":
                Nots.append(subnode.getValue().executeQuery(index))
            else:
                L.append(subnode.executeQuery(index))
        assert L
        L.sort(lambda x, y: cmp(len(x), len(y)))
        set = L[0]
        for x in L[1:]:
            dummy, set = weightedIntersection(set, x)
        if Nots:
            Nots.sort(lambda x, y: cmp(len(x), len(y)))
            notset = Nots[0]
            for x in Nots[1:]:
                dummy, notset = weightedUnion(notset, x)
            set = difference(set, notset)
        return set

class OrNode(ParseTreeNode):

    _nodeType = "OR"

    def executeQuery(self, index):
        # Balance unions as closely as possible, smallest to largest.
        allofem = self.getValue()
        merge = NBest(len(allofem))
        for subnode in allofem:
            result = subnode.executeQuery(index)
            merge.add(result, len(result))
        while len(merge) > 1:
            # Merge the two smallest so far, and add back to the queue.
            x, dummy = merge.pop_smallest()
            y, dummy = merge.pop_smallest()
            dummy, z = weightedUnion(x, y)
            merge.add(z, len(z))
        result, dummy = merge.pop_smallest()
        return result

class AtomNode(ParseTreeNode):

    _nodeType = "ATOM"

    def terms(self):
        return [self.getValue()]

    def executeQuery(self, index):
        return index.search(self.getValue())

class PhraseNode(AtomNode):

    _nodeType = "PHRASE"

    def executeQuery(self, index):
        return index.search_phrase(self.getValue())

class GlobNode(AtomNode):

    _nodeType = "GLOB"

    def executeQuery(self, index):
        return index.search_glob(self.getValue())
