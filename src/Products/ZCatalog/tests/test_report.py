##############################################################################
#
# Copyright (c) 2002 Zope Corporation and Contributors. All Rights Reserved.
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

from Products.ZCatalog import Vocabulary


class dummy(object):

    def __init__(self, num):
        self.num = num

    def title(self):
        return '%d' % self.num


class TestCatalogReport(unittest.TestCase):

    def setUp(self):
        from Products.ZCatalog.ZCatalog import ZCatalog
        vocabulary = Vocabulary.Vocabulary(
            'Vocabulary','Vocabulary', globbing=1)

        self.zcat = ZCatalog('catalog')
        self.zcat.long_query_time = 0.0
 
        self.zcat.addIndex('num', 'FieldIndex')
        self.zcat.addIndex('big', 'FieldIndex')
        self.zcat.addIndex('title', 'TextIndex')
        self.zcat._catalog.vocabulary = vocabulary

        for i in range(9):
            obj = dummy(i)
            obj.big = i > 5
            self.zcat.catalog_object(obj, str(i))

    def tearDown(self):
        from Products.ZCatalog.report import clear_value_indexes
        clear_value_indexes()

    def test_ReportLength(self):
        """ tests the report aggregation """
        self.zcat.manage_resetCatalogReport()

        self.zcat.searchResults(title='4 or 5 or 6',sort_on='num')
        self.zcat.searchResults(title='1 or 6 or 7',sort_on='num')
        self.zcat.searchResults(title='3 or 8 or 9',sort_on='num')
 
        self.zcat.searchResults(big=True,sort_on='num')
        self.zcat.searchResults(big=True,sort_on='num')
        self.zcat.searchResults(big=False,sort_on='num')
 
        self.zcat.searchResults(num=[5,4,3],sort_on='num')
        self.zcat.searchResults(num=(3,4,5),sort_on='num')
        self.assertEqual(4, len(self.zcat.getCatalogReport()))

    def test_ReportCounter(self):
        """ tests the counter of equal queries """
        self.zcat.manage_resetCatalogReport()

        self.zcat.searchResults(title='4 or 5 or 6',sort_on='num')
        self.zcat.searchResults(title='1 or 6 or 7',sort_on='num')
        self.zcat.searchResults(title='3 or 8 or 9',sort_on='num')

        r = self.zcat.getCatalogReport()[0]
        self.assertEqual(r['counter'],3)

    def test_ReportKey(self):
        """ tests the query keys for uniqueness """
        # query key 1
        key = ('sort_on', ('big', 'True'))
        self.zcat.manage_resetCatalogReport()

        self.zcat.searchResults(big=True,sort_on='num')
        self.zcat.searchResults(big=True,sort_on='num')
        r = self.zcat.getCatalogReport()[0]

        self.assertEqual(r['query'],key)
        self.assertEqual(r['counter'],2)

        # query key 2
        key = ('sort_on', ('big', 'False'))
        self.zcat.manage_resetCatalogReport()

        self.zcat.searchResults(big=False,sort_on='num')
        r = self.zcat.getCatalogReport()[0]

        self.assertEqual(r['query'],key)
        self.assertEqual(r['counter'], 1)

        # query key 3
        key = ('sort_on', ('num', '[3, 4, 5]'))
        self.zcat.manage_resetCatalogReport()

        self.zcat.searchResults(num=[5,4,3], sort_on='num')
        self.zcat.searchResults(num=(3,4,5), sort_on='num')
        r = self.zcat.getCatalogReport()[0]

        self.assertEqual(r['query'], key)
        self.assertEqual(r['counter'], 2)


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestCatalogReport))
    return suite
