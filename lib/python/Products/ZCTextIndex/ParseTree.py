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

from BTrees.IIBTree import difference

from Products.ZCTextIndex.SetOps import mass_weightedIntersection, \
                                        mass_weightedUnion

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
                Nots.append((subnode.getValue().executeQuery(index), 1))
            else:
                L.append((subnode.executeQuery(index), 1))
        assert L
        set = mass_weightedIntersection(L)
        if Nots:
            notset = mass_weightedUnion(Nots)
            set = difference(set, notset)
        return set

class OrNode(ParseTreeNode):

    _nodeType = "OR"

    def executeQuery(self, index):
        weighted = [(node.executeQuery(index), 1)
                    for node in self.getValue()]
        return mass_weightedUnion(weighted)

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
