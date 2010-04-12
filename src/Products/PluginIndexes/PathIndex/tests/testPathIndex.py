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
"""PathIndex unit tests.
"""

import unittest



class Dummy:
    def __init__( self, path):
        self.path = path

    def getPhysicalPath(self):
        return self.path.split('/')

DUMMIES = {
    1 : Dummy("/aa/aa/aa/1.html"),
    2 : Dummy("/aa/aa/bb/2.html"),
    3 : Dummy("/aa/aa/cc/3.html"),
    4 : Dummy("/aa/bb/aa/4.html"),
    5 : Dummy("/aa/bb/bb/5.html"),
    6 : Dummy("/aa/bb/cc/6.html"),
    7 : Dummy("/aa/cc/aa/7.html"),
    8 : Dummy("/aa/cc/bb/8.html"),
    9 : Dummy("/aa/cc/cc/9.html"),
    10 : Dummy("/bb/aa/aa/10.html"),
    11 : Dummy("/bb/aa/bb/11.html"),
    12 : Dummy("/bb/aa/cc/12.html"),
    13 : Dummy("/bb/bb/aa/13.html"),
    14 : Dummy("/bb/bb/bb/14.html"),
    15 : Dummy("/bb/bb/cc/15.html"),
    16 : Dummy("/bb/cc/aa/16.html"),
    17 : Dummy("/bb/cc/bb/17.html"),
    18 : Dummy("/bb/cc/cc/18.html")
}

def _populateIndex(index):
    for k, v in DUMMIES.items():
        index.index_object(k, v)

_marker = object()

class PathIndexTests(unittest.TestCase):
    """ Test PathIndex objects """

    def _getTargetClass(self):
        from Products.PluginIndexes.PathIndex.PathIndex import PathIndex
        return PathIndex

    def _makeOne(self, id='path', caller=_marker):
        if caller is not _marker:
            return self._getTargetClass()(id, caller)
        return self._getTargetClass()(id)

    def test_class_conforms_to_IPathIndex(self):
        from Products.PluginIndexes.interfaces import IPathIndex
        from zope.interface.verify import verifyClass
        verifyClass(IPathIndex, self._getTargetClass())

    def test_instance_conforms_to_IPathIndex(self):
        from Products.PluginIndexes.interfaces import IPathIndex
        from zope.interface.verify import verifyObject
        verifyObject(IPathIndex, self._makeOne())

    def test_class_conforms_to_IUniqueValueIndex(self):
        from Products.PluginIndexes.interfaces import IUniqueValueIndex
        from zope.interface.verify import verifyClass
        verifyClass(IUniqueValueIndex, self._getTargetClass())

    def test_instance_conforms_to_IUniqueValueIndex(self):
        from Products.PluginIndexes.interfaces import IUniqueValueIndex
        from zope.interface.verify import verifyObject
        verifyObject(IUniqueValueIndex, self._makeOne())

    def test_numObjects_empty(self):
        index = self._makeOne()
        self.assertEqual(index.numObjects(), 0)

    def test_numObjects_filled(self):
        index = self._makeOne()
        _populateIndex(index)
        self.assertEqual(index.numObjects(), len(DUMMIES))

    def test_getEntryForObject_miss(self):
        index = self._makeOne()
        self.assertEqual(index.getEntryForObject(1234), None)

    def test_getEntryForObject_hit(self):
        index = self._makeOne()
        _populateIndex(index)
        self.assertEqual(index.getEntryForObject(1), DUMMIES[1].path)

    def test_unindex_object_nonesuch(self):
        index = self._makeOne()
        index.unindex_object( 1234 ) # nothrow

    def test_unindex_object_broken_path(self):
        index = self._makeOne()
        _populateIndex(index)
        index._unindex[1] = "/broken/thing"
        index.unindex_object(1) # nothrow

    def test_unindex_object_found(self):
        index = self._makeOne()
        _populateIndex(index)

        for k in DUMMIES.keys():
            index.unindex_object(k)

        self.assertEqual(index.numObjects(), 0)
        self.assertEqual(len(index._index), 0)
        self.assertEqual(len(index._unindex), 0)

    def test_index_object_again(self):
        index = self._makeOne()
        _populateIndex(index)
        before = index.numObjects()
        o = Dummy('/foo/bar')
        index.index_object(1234, o)
        self.assertEqual(index.numObjects(), before + 1)
        index.index_object(1234, o)
        self.assertEqual(index.numObjects(), before + 1)

    def test__apply_index_no_match_in_query(self):
        index = self._makeOne()
        self.assertEqual(index._apply_index({'foo': 'xxx'}), None)

    def test__apply_index_nonesuch(self):
        index = self._makeOne()
        res = index._apply_index({'path': 'xxx'})
        self.assertEqual(len(res[0]), 0)
        self.assertEqual(res[1], ('path',))

    def test___apply_index_root_levelO_dict(self):
        index = self._makeOne()
        _populateIndex(index)
        query = {'path': {'query': '/', 'level': 0}}
        res = index._apply_index(query)
        self.assertEqual(list(res[0].keys()), range(1,19))

    def test___apply_index_root_levelO_tuple(self):
        index = self._makeOne()
        _populateIndex(index)
        query = {'path': (('/', 0),)}
        res = index._apply_index(query)
        self.assertEqual(list(res[0].keys()), range(1,19))

    def test__apply_index_simple(self):
        index = self._makeOne()
        _populateIndex(index)
        tests = [
            # component, level, expected results
            ("aa", 0, [1,2,3,4,5,6,7,8,9]),
            ("aa", 1, [1,2,3,10,11,12] ),
            ("bb", 0, [10,11,12,13,14,15,16,17,18]),
            ("bb", 1, [4,5,6,13,14,15]),
            ("bb/cc", 0, [16,17,18]),
            ("bb/cc", 1, [6,15]),
            ("bb/aa", 0, [10,11,12]),
            ("bb/aa", 1, [4,13]),
            ("aa/cc", -1, [3,7,8,9,12]),
            ("bb/bb", -1, [5,13,14,15]),
            ("18.html", 3, [18]),
            ("18.html", -1, [18]),
            ("cc/18.html", -1, [18]),
            ("cc/18.html", 2, [18]),
        ]

        for comp, level, expected in tests:
            for path in [comp, "/"+comp, "/"+comp+"/"]:
                # Test with the level passed in as separate parameter
                query = {'path': {'query':path, 'level': level}}
                res = index._apply_index(query)
                self.assertEqual(list(res[0].keys()), expected)

                # Test with the level passed in as part of the path parameter
                query = {'path': ((path, level),)}
                res = index._apply_index(query)
                self.assertEqual(list(res[0].keys()), expected)

    def test__apply_index_ComplexOrTests(self):
        index = self._makeOne()
        _populateIndex(index)
        tests = [
            (['aa','bb'],1,[1,2,3,4,5,6,10,11,12,13,14,15]),
            (['aa','bb','xx'],1,[1,2,3,4,5,6,10,11,12,13,14,15]),
            ([('cc',1),('cc',2)],0,[3,6,7,8,9,12,15,16,17,18]),
        ]

        for lst, level, expected in tests:
            query = {'path': {'query': lst, 'level': level, 'operator': 'or'}}
            res = index._apply_index(query)
            lst = list(res[0].keys())
            self.assertEqual(lst, expected)

    def test__apply_index_ComplexANDTests(self):
        index = self._makeOne()
        _populateIndex(index)
        tests = [
            # Path query (as list or (path, level) tuple), level, expected
            (['aa','bb'], 1, []),
            ([('aa',0), ('bb',1)], 0, [4,5,6]),
            ([('aa',0), ('cc',2)], 0, [3,6,9]),
        ]

        for lst, level, expected in tests:
            query = {'path': {'query': lst, 'level': level, 'operator': 'and'}}
            res = index._apply_index(query)
            lst = list(res[0].keys())
            self.assertEqual(lst, expected)

    def test__apply_index_QueryPathReturnedInResult(self):
        index = self._makeOne()
        index.index_object(1, Dummy("/ff"))
        index.index_object(2, Dummy("/ff/gg"))
        index.index_object(3, Dummy("/ff/gg/3.html"))
        index.index_object(4, Dummy("/ff/gg/4.html"))
        res = index._apply_index({'path': {'query': '/ff/gg'}})
        lst = list(res[0].keys())
        self.assertEqual(lst, [2, 3, 4])


def test_suite():
    return unittest.TestSuite((
            unittest.makeSuite(PathIndexTests),
        ))
