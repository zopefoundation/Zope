##############################################################################
#
# Copyright (c) 2010 Zope Foundation and Contributors.
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

from BTrees.IIBTree import IISet


class Dummy(object):

    def __init__(self, docid, truth):
        self.id = docid
        self.truth = truth


class TestBooleanIndex(unittest.TestCase):

    def _getTargetClass(self):
        from Products.PluginIndexes.BooleanIndex import BooleanIndex
        return BooleanIndex.BooleanIndex

    def _makeOne(self, attr='truth'):
        return self._getTargetClass()(attr)

    def test_index_true(self):
        index = self._makeOne()
        obj = Dummy(1, True)
        index._index_object(obj.id, obj, attr='truth')
        self.failUnless(1 in index._unindex)
        self.failUnless(1 in index._index)

    def test_index_false(self):
        index = self._makeOne()
        obj = Dummy(1, False)
        index._index_object(obj.id, obj, attr='truth')
        self.failUnless(1 in index._unindex)
        self.failIf(1 in index._index)

    def test_search_true(self):
        index = self._makeOne()
        obj = Dummy(1, True)
        index._index_object(obj.id, obj, attr='truth')
        obj = Dummy(2, False)
        index._index_object(obj.id, obj, attr='truth')

        res, idx = index._apply_index({'truth': True})
        self.failUnlessEqual(idx, ('truth', ))
        self.failUnlessEqual(list(res), [1])

    def test_search_false(self):
        index = self._makeOne()
        obj = Dummy(1, True)
        index._index_object(obj.id, obj, attr='truth')
        obj = Dummy(2, False)
        index._index_object(obj.id, obj, attr='truth')

        res, idx = index._apply_index({'truth': False})
        self.failUnlessEqual(idx, ('truth', ))
        self.failUnlessEqual(list(res), [2])

    def test_search_inputresult(self):
        index = self._makeOne()
        obj = Dummy(1, True)
        index._index_object(obj.id, obj, attr='truth')
        obj = Dummy(2, False)
        index._index_object(obj.id, obj, attr='truth')

        res, idx = index._apply_index({'truth': True}, resultset=IISet([]))
        self.failUnlessEqual(idx, ('truth', ))
        self.failUnlessEqual(list(res), [])

        res, idx = index._apply_index({'truth': True}, resultset=IISet([2]))
        self.failUnlessEqual(idx, ('truth', ))
        self.failUnlessEqual(list(res), [])

        res, idx = index._apply_index({'truth': True}, resultset=IISet([1]))
        self.failUnlessEqual(idx, ('truth', ))
        self.failUnlessEqual(list(res), [1])

        res, idx = index._apply_index({'truth': True}, resultset=IISet([1, 2]))
        self.failUnlessEqual(idx, ('truth', ))
        self.failUnlessEqual(list(res), [1])

        res, idx = index._apply_index({'truth': False},
                                      resultset=IISet([1, 2]))
        self.failUnlessEqual(idx, ('truth', ))
        self.failUnlessEqual(list(res), [2])


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestBooleanIndex))
    return suite
