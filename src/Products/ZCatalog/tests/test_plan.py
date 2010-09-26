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

import os
import time
import unittest

from zope.testing import cleanup


class dummy(object):

    def __init__(self, num):
        self.num = num

    def big(self):
        return self.num > 5

    def numbers(self):
        return (self.num, self.num + 1)


TESTMAP = {
    '/folder/catalog': {
        'index1 index2': {
            'index1': (10, 2.0, 3, True),
            'index2': (15, 1.5, 2, False),
        }
    }
}


class TestNestedDict(unittest.TestCase):

    def setUp(self):
        self.nest = self._makeOne()

    def _makeOne(self):
        from ..plan import NestedDict
        return NestedDict

    def test_novalue(self):
        self.assertEquals(getattr(self.nest, 'value', None), None)

    def test_nolock(self):
        self.assertEquals(getattr(self.nest, 'lock', None), None)


class TestPriorityMap(unittest.TestCase):

    def setUp(self):
        self.pmap = self._makeOne()

    def tearDown(self):
        self.pmap.clear()

    def _makeOne(self):
        from ..plan import PriorityMap
        return PriorityMap

    def test_get_value(self):
        self.assertEquals(self.pmap.get_value(), {})

    def test_get(self):
        self.assertEquals(self.pmap.get('foo'), {})

    def test_set(self):
        self.pmap.set('foo', {'bar': 1})
        self.assertEquals(self.pmap.get('foo'), {'bar': 1})

    def test_clear(self):
        self.pmap.set('foo', {'bar': 1})
        self.pmap.clear()
        self.assertEquals(self.pmap.value, {})

    def test_get_entry(self):
        self.assertEquals(self.pmap.get_entry('foo', 'bar'), {})

    def test_set_entry(self):
        self.pmap.set_entry('foo', 'bar', {'baz': 1})
        self.assertEquals(self.pmap.get_entry('foo', 'bar'), {'baz': 1})

    def test_clear_entry(self):
        self.pmap.set('foo', {'bar': 1})
        self.pmap.clear_entry('foo')
        self.assertEquals(self.pmap.get('foo'), {})


class TestPriorityMapDefault(unittest.TestCase):

    def setUp(self):
        self.pmap = self._makeOne()

    def tearDown(self):
        self.pmap.clear()

    def _makeOne(self):
        from ..plan import PriorityMap
        return PriorityMap

    def test_empty(self):
        self.pmap.load_default()
        self.assertEquals(self.pmap.get_value(), {})

    def test_load_failure(self):
        try:
            os.environ['ZCATALOGQUERYPLAN'] = 'Products.ZCatalog.invalid'
            # 'Products.ZCatalog.tests.test_plan.TESTMAP'
            self.pmap.load_default()
            self.assertEquals(self.pmap.get_value(), {})
        finally:
            del os.environ['ZCATALOGQUERYPLAN']

    def test_load(self):
        from ..plan import Benchmark
        try:
            os.environ['ZCATALOGQUERYPLAN'] = \
                'Products.ZCatalog.tests.test_plan.TESTMAP'
            self.pmap.load_default()
            expected = {'/folder/catalog': {'index1 index2': {
                'index1': Benchmark(num=10, duration=2.0, hits=3, limit=True),
                'index2': Benchmark(num=15, duration=1.5, hits=2, limit=False),
            }}}
            self.assertEquals(self.pmap.get_value(), expected)
        finally:
            del os.environ['ZCATALOGQUERYPLAN']


class TestReports(unittest.TestCase):

    def setUp(self):
        self.reports = self._makeOne()

    def tearDown(self):
        self.reports.clear()

    def _makeOne(self):
        from ..plan import Reports
        return Reports

    def test_value(self):
        self.assertEquals(self.reports.value, {})

    def test_lock(self):
        from thread import LockType
        self.assertEquals(type(self.reports.lock), LockType)


class TestValueIndexes(unittest.TestCase):

    def setUp(self):
        self.value = self._makeOne()

    def tearDown(self):
        self.value.clear()

    def _makeOne(self):
        from ..plan import ValueIndexes
        return ValueIndexes

    def test_get(self):
        self.assertEquals(self.value.get(), frozenset())

    def test_set(self):
        indexes = ('index1', 'index2')
        self.value.set(indexes)
        self.assertEquals(self.value.get(), frozenset(indexes))

    def test_clear(self):
        self.value.set(('index1', ))
        self.value.clear()
        self.assertEquals(self.value.get(), frozenset())

    def test_determine_already_set(self):
        self.value.set(('index1', ))
        self.assertEquals(self.value.determine(()), frozenset(('index1', )))


# class TestValueIndexesDetermination(unittest.TestCase):
# Test the actual logic for determining value indexes

# class TestMakeKey(unittest.TestCase):

class TestCatalogPlan(cleanup.CleanUp, unittest.TestCase):

    def setUp(self):
        cleanup.CleanUp.setUp(self)
        from Products.ZCatalog.Catalog import Catalog
        self.cat = Catalog('catalog')

    def _makeOne(self, catalog=None, query=None):
        from ..plan import CatalogPlan
        if catalog is None:
            catalog = self.cat
        return CatalogPlan(catalog, query=query)

    def test_get_id(self):
        plan = self._makeOne()
        self.assertEquals(plan.get_id(), ('', 'NonPersistentCatalog'))

    def test_get_id_persistent(self):
        from Products.ZCatalog.ZCatalog import ZCatalog
        zcat = ZCatalog('catalog')
        plan = self._makeOne(zcat._catalog)
        self.assertEquals(plan.get_id(), ('catalog',))

    def test_plan_empty(self):
        plan = self._makeOne()
        self.assertEquals(plan.plan(), None)

    def test_start(self):
        plan = self._makeOne()
        plan.start()
        self.assert_(plan.start_time <= time.time())

    def test_start_split(self):
        plan = self._makeOne()
        plan.start_split('index1')
        self.assert_('index1' in plan.interim)

    def test_stop_split(self):
        plan = self._makeOne()
        plan.start_split('index1')
        plan.stop_split('index1')
        self.assert_('index1' in plan.interim)
        i1 = plan.interim['index1']
        self.assert_(i1.start <= i1.end)
        self.assert_('index1' in plan.benchmark)

    def test_stop_split_sort_on(self):
        plan = self._makeOne()
        plan.start_split('sort_on')
        plan.stop_split('sort_on')
        self.assert_('sort_on' in plan.interim)
        so = plan.interim['sort_on']
        self.assert_(so.start <= so.end)
        self.assert_('sort_on' not in plan.benchmark)

    def test_stop(self):
        plan = self._makeOne(query={'index1': 1, 'index2': 2})
        plan.start()
        plan.start_split('index1')
        plan.stop_split('index1')
        plan.start_split('index1')
        plan.stop_split('index1')
        plan.start_split('sort_on')
        plan.stop_split('sort_on')
        time.sleep(0.02) # wait at least one Windows clock tick
        plan.stop()

        self.assert_(plan.duration > 0)
        self.assert_('index1' in plan.benchmark)
        self.assertEquals(plan.benchmark['index1'].hits, 2)
        self.assert_('index2' in plan.benchmark)
        self.assertEquals(plan.benchmark['index2'].hits, 0)
        self.assertEquals(set(plan.plan()), set(('index1', 'index2')))

    def test_log(self):
        plan = self._makeOne(query={'index1': 1})
        plan.threshold = 0.0
        plan.start()
        plan.start_split('index1')
        plan.stop_split('index1')
        plan.stop()
        plan.log()
        report = plan.report()
        self.assertEquals(len(report), 1)
        self.assertEquals(report[0]['counter'], 2)
        plan.reset()
        self.assertEquals(len(plan.report()), 0)


class TestCatalogReport(cleanup.CleanUp, unittest.TestCase):

    def setUp(self):
        cleanup.CleanUp.setUp(self)
        from Products.ZCatalog.ZCatalog import ZCatalog
        self.zcat = ZCatalog('catalog')
        self.zcat.long_query_time = 0.0
        self._add_indexes()
        for i in range(9):
            obj = dummy(i)
            self.zcat.catalog_object(obj, str(i))

    def _add_indexes(self):
        from Products.PluginIndexes.FieldIndex.FieldIndex import FieldIndex
        from Products.PluginIndexes.KeywordIndex.KeywordIndex import \
            KeywordIndex
        num = FieldIndex('num')
        self.zcat._catalog.addIndex('num', num)
        big = FieldIndex('big')
        self.zcat._catalog.addIndex('big', big)
        numbers = KeywordIndex('numbers')
        self.zcat._catalog.addIndex('numbers', numbers)

    def test_ReportLength(self):
        """ tests the report aggregation """
        self.zcat.manage_resetCatalogReport()

        self.zcat.searchResults(numbers=4, sort_on='num')
        self.zcat.searchResults(numbers=1, sort_on='num')
        self.zcat.searchResults(numbers=3, sort_on='num')

        self.zcat.searchResults(big=True, sort_on='num')
        self.zcat.searchResults(big=True, sort_on='num')
        self.zcat.searchResults(big=False, sort_on='num')

        self.zcat.searchResults(num=[5, 4, 3], sort_on='num')
        self.zcat.searchResults(num=(3, 4, 5), sort_on='num')
        self.assertEqual(4, len(self.zcat.getCatalogReport()))

    def test_ReportCounter(self):
        """ tests the counter of equal queries """
        self.zcat.manage_resetCatalogReport()

        self.zcat.searchResults(numbers=5, sort_on='num')
        self.zcat.searchResults(numbers=6, sort_on='num')
        self.zcat.searchResults(numbers=8, sort_on='num')

        r = self.zcat.getCatalogReport()[0]
        self.assertEqual(r['counter'], 3)

    def test_ReportKey(self):
        """ tests the query keys for uniqueness """
        # query key 1
        key = ('sort_on', ('big', 'True'))
        self.zcat.manage_resetCatalogReport()

        self.zcat.searchResults(big=True, sort_on='num')
        self.zcat.searchResults(big=True, sort_on='num')
        r = self.zcat.getCatalogReport()[0]

        self.assertEqual(r['query'], key)
        self.assertEqual(r['counter'], 2)

        # query key 2
        key = ('sort_on', ('big', 'False'))
        self.zcat.manage_resetCatalogReport()

        self.zcat.searchResults(big=False, sort_on='num')
        r = self.zcat.getCatalogReport()[0]

        self.assertEqual(r['query'], key)
        self.assertEqual(r['counter'], 1)

        # query key 3
        key = ('sort_on', ('num', '[3, 4, 5]'))
        self.zcat.manage_resetCatalogReport()

        self.zcat.searchResults(num=[5, 4, 3], sort_on='num')
        self.zcat.searchResults(num=(3, 4, 5), sort_on='num')
        r = self.zcat.getCatalogReport()[0]

        self.assertEqual(r['query'], key)
        self.assertEqual(r['counter'], 2)
