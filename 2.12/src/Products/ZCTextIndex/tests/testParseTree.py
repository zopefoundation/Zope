##############################################################################
#
# Copyright (c) 2008 Zope Foundation and Contributors.
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

import unittest

class ParseTreeTests(unittest.TestCase):

    def _conforms(self, klass):
        from zope.interface.verify import verifyClass
        from Products.ZCTextIndex.IQueryParseTree import IQueryParseTree
        verifyClass(IQueryParseTree, klass)

    def test_ParseTreeNode_conforms_to_IQueryParseTree(self):
        from Products.ZCTextIndex.ParseTree import ParseTreeNode
        self._conforms(ParseTreeNode)

    def test_OrNode_conforms_to_IQueryParseTree(self):
        from Products.ZCTextIndex.ParseTree import OrNode
        self._conforms(OrNode)

    def test_AndNode_conforms_to_IQueryParseTree(self):
        from Products.ZCTextIndex.ParseTree import AndNode
        self._conforms(AndNode)

    def test_NotNode_conforms_to_IQueryParseTree(self):
        from Products.ZCTextIndex.ParseTree import NotNode
        self._conforms(NotNode)

    def test_GlobNode_conforms_to_IQueryParseTree(self):
        from Products.ZCTextIndex.ParseTree import GlobNode
        self._conforms(GlobNode)

    def test_AtomNode_conforms_to_IQueryParseTree(self):
        from Products.ZCTextIndex.ParseTree import AtomNode
        self._conforms(AtomNode)

    def test_PhraseNode_conforms_to_IQueryParseTree(self):
        from Products.ZCTextIndex.ParseTree import PhraseNode
        self._conforms(PhraseNode)


def test_suite():
    return unittest.TestSuite((
            unittest.makeSuite(ParseTreeTests),
        ))

if __name__=="__main__":
    unittest.main(defaultTest='test_suite')
