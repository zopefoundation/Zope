##############################################################################
#
# Copyright (c) 2001 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################

import Zope
import unittest

from DateTime import DateTime
from Products.PluginIndexes.DateIndex.DateIndex import DateIndex
from types import IntType, FloatType
import time

class Dummy:

    def __init__(self, name, date):

        self._name  = name
        self._date = date

    def name(self):
        return self._name

    def date(self):
        return self._date

    def __str__(self):
        return "<Dummy %s, date %s>" % (self._name, str(self._date))

class DI_Tests(unittest.TestCase):
    def setUp(self):
        self._values = (
            (0, Dummy('a', None)),
            (1, Dummy('b', DateTime(0))),
            (2, Dummy('c', DateTime('2002-05-08 15:16:17'))),
            (3, Dummy('d', DateTime('2032-05-08 15:16:17'))),
            (4, Dummy('e', DateTime('2062-05-08 15:16:17'))),
            (5, Dummy('e', DateTime('2062-05-08 15:16:17'))),
            (6, Dummy('f', 1072742620.0)),
            (7, Dummy('f', 1072742900)),
        )
        self._index = DateIndex('date')
        self._noop_req  = {'bar': 123}
        self._request   = {'date': DateTime(0)}
        self._min_req   = {'date': DateTime('2032-05-08 15:16:17'),
            'date_usage': 'range:min'}
        self._max_req   = {'date': DateTime('2032-05-08 15:16:17'),
            'date_usage': 'range:max'}
        self._range_req = {'date': (DateTime('2002-05-08 15:16:17'),
                                    DateTime('2062-05-08 15:16:17')),
                           'date_usage': 'range:min:max'}
        self._zero_req  = {'date': 0}
        self._none_req  = {'date': None}
        self._float_req = {'date': 1072742620.0}
        self._int_req   = {'date': 1072742900}

    def _populateIndex( self ):
        for k, v in self._values:
            self._index.index_object(k, v)

    def _checkApply(self, req, expectedValues):
        result, used = self._index._apply_index(req)
        if hasattr(result, 'keys'):
            result = result.keys()
        self.failUnlessEqual(used, ('date',))
        self.failUnlessEqual(len(result), len(expectedValues),
            '%s | %s' % (map(None, result), expectedValues))
        for k, v in expectedValues:
            self.failUnless(k in result)

    def _convert(self, date):
        if type(date) in (FloatType, IntType):
            yr, mo, dy, hr, mn = time.gmtime(date)[:5]
        else:
            yr, mo, dy, hr, mn = date.parts()[:5]
        return (((yr * 12 + mo) * 31 + dy) * 24 + hr) * 60 + mn

    def test_empty(self):
        empty = self._index

        self.failUnlessEqual(len(empty), 0)
        self.failUnlessEqual(len(empty.referencedObjects()), 0)

        self.failUnless(empty.getEntryForObject(1234) is None)
        marker = []
        self.failUnless(empty.getEntryForObject(1234, marker) is marker)
        empty.unindex_object(1234) # shouldn't throw

        self.failUnless(empty.hasUniqueValuesFor('date'))
        self.failIf(empty.hasUniqueValuesFor('foo'))
        self.failUnlessEqual(len(empty.uniqueValues('date')), 0)

        self.failUnless(empty._apply_index({'zed': 12345}) is None)

        self._checkApply(self._request, [])
        self._checkApply(self._min_req, [])
        self._checkApply(self._max_req, [])
        self._checkApply(self._range_req, [])

    def test_retrieval( self ):
        self._populateIndex()
        values = self._values
        index = self._index

        self.failUnlessEqual(len(index), len(values) - 2) # One dupe, one empty
        self.failUnlessEqual(len(index.referencedObjects()), len(values) - 1)
            # One empty

        self.failUnless(index.getEntryForObject(1234) is None)
        marker = []
        self.failUnless(index.getEntryForObject(1234, marker) is marker)
        index.unindex_object(1234) # shouldn't throw

        for k, v in values:
            if v.date():
                self.failUnlessEqual(self._index.getEntryForObject(k),
                    self._convert(v.date()))

        self.failUnlessEqual(len(index.uniqueValues('date')), len(values) - 2)
        self.failUnless(index._apply_index(self._noop_req) is None)

        self._checkApply(self._request, values[1:2])
        self._checkApply(self._min_req, values[3:6])
        self._checkApply(self._max_req, values[1:4] + values[6:])
        self._checkApply(self._range_req, values[2:6] + values[6:] )
        self._checkApply(self._float_req, [values[6]] )
        self._checkApply(self._int_req, [values[7]] )

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest( unittest.makeSuite( DI_Tests ) )
    return suite

def run():
    unittest.TextTestRunner().run(test_suite())

if __name__ == '__main__':
    run()
