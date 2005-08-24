##############################################################################
#
# Copyright (c) 2001 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""DateIndex unit tests.

$Id$
"""

import unittest
import Testing
import Zope2
Zope2.startup()

from datetime import date, datetime, tzinfo, timedelta
import time
from types import IntType, FloatType

from DateTime import DateTime

from Products.PluginIndexes.DateIndex.DateIndex import DateIndex, Local


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

###############################################################################
# excerpted from the Python module docs
###############################################################################
ZERO = timedelta(0)
HOUR = timedelta(hours=1)
def first_sunday_on_or_after(dt):
    days_to_go = 6 - dt.weekday()
    if days_to_go:
        dt += timedelta(days_to_go)
    return dt

# In the US, DST starts at 2am (standard time) on the first Sunday in April.
DSTSTART = datetime(1, 4, 1, 2)
# and ends at 2am (DST time; 1am standard time) on the last Sunday of Oct.
# which is the first Sunday on or after Oct 25.
DSTEND = datetime(1, 10, 25, 1)

class USTimeZone(tzinfo):

    def __init__(self, hours, reprname, stdname, dstname):
        self.stdoffset = timedelta(hours=hours)
        self.reprname = reprname
        self.stdname = stdname
        self.dstname = dstname

    def __repr__(self):
        return self.reprname

    def tzname(self, dt):
        if self.dst(dt):
            return self.dstname
        else:
            return self.stdname

    def utcoffset(self, dt):
        return self.stdoffset + self.dst(dt)

    def dst(self, dt):
        if dt is None or dt.tzinfo is None:
            # An exception may be sensible here, in one or both cases.
            # It depends on how you want to treat them.  The default
            # fromutc() implementation (called by the default astimezone()
            # implementation) passes a datetime with dt.tzinfo is self.
            return ZERO
        assert dt.tzinfo is self

        # Find first Sunday in April & the last in October.
        start = first_sunday_on_or_after(DSTSTART.replace(year=dt.year))
        end = first_sunday_on_or_after(DSTEND.replace(year=dt.year))

        # Can't compare naive to aware objects, so strip the timezone from
        # dt first.
        if start <= dt.replace(tzinfo=None) < end:
            return HOUR
        else:
            return ZERO

Eastern  = USTimeZone(-5, "Eastern",  "EST", "EDT")
###############################################################################


class DI_Tests(unittest.TestCase):
    def setUp(self):
        self._values = (
            (0, Dummy('a', None)),                            # None
            (1, Dummy('b', DateTime(0))),                     # 1055335680
            (2, Dummy('c', DateTime('2002-05-08 15:16:17'))), # 1072667236
            (3, Dummy('d', DateTime('2032-05-08 15:16:17'))), # 1088737636
            (4, Dummy('e', DateTime('2062-05-08 15:16:17'))), # 1018883325
            (5, Dummy('e', DateTime('2062-05-08 15:16:17'))), # 1018883325
            (6, Dummy('f', 1072742620.0)),                    # 1073545923
            (7, Dummy('f', 1072742900)),                      # 1073545928
            (8, Dummy('g', date(2034,2,5))),                  # 1073599200
            (9, Dummy('h', datetime(2034,2,5,15,20,5))),      # (varies)
            (10, Dummy('i', datetime(2034,2,5,10,17,5,
                                     tzinfo=Eastern))),       # 1073600117
        )
        self._index = DateIndex('date')
        self._noop_req  = {'bar': 123}
        self._request   = {'date': DateTime(0)}
        self._min_req   = {'date': {'query': DateTime('2032-05-08 15:16:17'),
            'range': 'min'}}
        self._max_req   = {'date': {'query': DateTime('2032-05-08 15:16:17'),
            'range': 'max'}}
        self._range_req = {'date': {'query':(DateTime('2002-05-08 15:16:17'),
                                    DateTime('2062-05-08 15:16:17')),
                           'range': 'min:max'}}
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
            '%s | %s' % (result, expectedValues))
        for k, v in expectedValues:
            self.failUnless(k in result)

    def _convert(self, dt):
        if type(dt) in (FloatType, IntType):
            yr, mo, dy, hr, mn = time.gmtime(dt)[:5]
        elif type(dt) is date:
            yr, mo, dy, hr, mn = dt.timetuple()[:5]
        elif type(dt) is datetime:
            if dt.tzinfo is None: # default behavior of index
                dt = dt.replace(tzinfo=Local)
            yr, mo, dy, hr, mn = dt.utctimetuple()[:5]
        else:
            yr, mo, dy, hr, mn = dt.toZone('UTC').parts()[:5]
        return (((yr * 12 + mo) * 31 + dy) * 24 + hr) * 60 + mn

    def test_z3interfaces(self):
        from Products.PluginIndexes.interfaces import IDateIndex
        from Products.PluginIndexes.interfaces import IPluggableIndex
        from Products.PluginIndexes.interfaces import ISortIndex
        from Products.PluginIndexes.interfaces import IUniqueValueIndex
        from zope.interface.verify import verifyClass

        verifyClass(IDateIndex, DateIndex)
        verifyClass(IPluggableIndex, DateIndex)
        verifyClass(ISortIndex, DateIndex)
        verifyClass(IUniqueValueIndex, DateIndex)

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
        self._checkApply(self._min_req, values[3:6] + values[8:])
        self._checkApply(self._max_req, values[1:4] + values[6:8])
        self._checkApply(self._range_req, values[2:] )
        self._checkApply(self._float_req, [values[6]] )
        self._checkApply(self._int_req, [values[7]] )

    def test_naive_convert_to_utc(self):
        values = self._values
        index = self._index
        index.index_naive_time_as_local = False
        self._populateIndex()
        for k, v in values[9:]:
            # assert that the timezone is effectively UTC for item 9,
            # and still correct for item 10
            yr, mo, dy, hr, mn = v.date().utctimetuple()[:5]
            val = (((yr * 12 + mo) * 31 + dy) * 24 + hr) * 60 + mn
            self.failUnlessEqual(self._index.getEntryForObject(k), val)

    def test_removal(self):
        """ DateIndex would hand back spurious entries when used as a
            sort_index, because it previously was not removing entries
            from the _unindex when indexing an object with a value of
            None. The catalog consults a sort_index's
            documentToKeyMap() to build the brains.
        """
        values = self._values
        index = self._index
        self._populateIndex()
        self._checkApply(self._int_req, [values[7]])
        index.index_object(7, None)
        self.failIf(7 in index.documentToKeyMap().keys())


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest( unittest.makeSuite( DI_Tests ) )
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
