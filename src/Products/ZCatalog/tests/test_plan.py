##############################################################################
#
# Copyright (c) 2010 Zope Foundation and Contributors. All Rights Reserved.
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


class dummy(object):

    def __init__(self, num):
        self.num = num

    def big(self):
        return self.num > 5

    def numbers(self):
        return (self.num, self.num + 1)


class TestCatalogPlan(unittest.TestCase):

    def setUp(self):
        from Products.ZCatalog.ZCatalog import ZCatalog
        self.zcat = ZCatalog('catalog')
        self.zcat.long_query_time = 0.0
        self.zcat.addIndex('num', 'FieldIndex')
        self.zcat.addIndex('big', 'FieldIndex')
        self.zcat.addIndex('numbers', 'KeywordIndex')

        for i in range(9):
            obj = dummy(i)
            self.zcat.catalog_object(obj, str(i))

    def tearDown(self):
        from Products.ZCatalog.plan import ValueIndexes
        ValueIndexes.clear()

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


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestCatalogPlan))
    return suite
