##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""TopicIndex unit tests.

$Id$
"""

import unittest
import Testing
import Zope2
Zope2.startup()

from Products.PluginIndexes.TopicIndex.TopicIndex import TopicIndex


class Obj:

    def __init__(self,id,meta_type=''):
        self.id = id
        self.meta_type = meta_type

    def getId(self): return self.id
    def getPhysicalPath(self):  return self.id


class TestBase(unittest.TestCase):

    def _searchAnd(self,query,expected):
        return self._search(query,'and',expected)

    def _searchOr(self,query,expected):
        return self._search(query,'or',expected)

    def _search(self,query,operator,expected):
        res = self.TI._apply_index({'topic':{'query':query,'operator':operator}})
        rows = list(res[0].keys())
        rows.sort()
        expected.sort()
        self.assertEqual(rows,expected,query)
        return rows


class TestTopicIndex(TestBase):

    def setUp(self):
        self.TI = TopicIndex("topic")
        self.TI.addFilteredSet("doc1","PythonFilteredSet","o.meta_type=='doc1'")
        self.TI.addFilteredSet("doc2","PythonFilteredSet","o.meta_type=='doc2'")

        self.TI.index_object(0 , Obj('0',))
        self.TI.index_object(1 , Obj('1','doc1'))
        self.TI.index_object(2 , Obj('2','doc1'))
        self.TI.index_object(3 , Obj('3','doc2'))
        self.TI.index_object(4 , Obj('4','doc2'))
        self.TI.index_object(5 , Obj('5','doc3'))
        self.TI.index_object(6 , Obj('6','doc3'))

    def test_z3interfaces(self):
        from Products.PluginIndexes.interfaces import ITopicIndex
        from Products.PluginIndexes.interfaces import IPluggableIndex
        from zope.interface.verify import verifyClass

        verifyClass(ITopicIndex, TopicIndex)
        verifyClass(IPluggableIndex, TopicIndex)

    def testOr(self):
        self._searchOr('doc1',[1,2])
        self._searchOr(['doc1'],[1,2])
        self._searchOr('doc2',[3,4]),
        self._searchOr(['doc2'],[3,4])
        self._searchOr(['doc1','doc2'], [1,2,3,4])

    def testAnd(self):
        self._searchAnd('doc1',[1,2])
        self._searchAnd(['doc1'],[1,2])
        self._searchAnd('doc2',[3,4])
        self._searchAnd(['doc2'],[3,4])
        self._searchAnd(['doc1','doc2'],[])

    def testRemoval(self):
        self.TI.index_object(1, Obj('1','doc2'))
        self._searchOr('doc1',[2])
        self._searchOr('doc2', [1,3,4])


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(TestTopicIndex),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
