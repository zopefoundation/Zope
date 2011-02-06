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
""" Unittests for Catalog.

$Id$
"""

import unittest
import Testing
import Zope2
Zope2.startup()

from itertools import chain
import random

import ExtensionClass
import OFS.Application
from AccessControl.SecurityManagement import setSecurityManager
from AccessControl.SecurityManagement import noSecurityManager
from AccessControl import Unauthorized
from Acquisition import Implicit
from Products.ZCatalog.Catalog import Catalog
from Products.ZCatalog.Catalog import CatalogError
from ZODB.DB import DB
from ZODB.DemoStorage import DemoStorage
import transaction

from Products.PluginIndexes.FieldIndex.FieldIndex import FieldIndex
from Products.PluginIndexes.KeywordIndex.KeywordIndex import KeywordIndex
from Products.ZCTextIndex.OkapiIndex import OkapiIndex
from Products.ZCTextIndex.ZCTextIndex import PLexicon
from Products.ZCTextIndex.ZCTextIndex import ZCTextIndex


def createDatabase():
    # XXX We have to import and init products in order for PluginIndexes to
    # be registered.
    OFS.Application.import_products()

    # Create a DemoStorage and put an Application in it
    db = DB(DemoStorage())
    conn = db.open()
    root = conn.root()
    app = OFS.Application.Application()
    root['Application'] = app
    transaction.commit()

    # Init products
    #OFS.Application.initialize(app)
    OFS.Application.install_products(app) # XXX: this is still icky

    return app

app = createDatabase()

def sort(iterable):
    L = list(iterable)
    L.sort()
    return L

from OFS.Folder import Folder as OFS_Folder
class Folder(OFS_Folder):
    def __init__(self, id):
        self._setId(id)
        OFS_Folder.__init__(self)


class CatalogBase:
    def setUp(self):
        self._catalog = Catalog()

    def tearDown(self):
        self._catalog = None

class TestAddDelColumn(CatalogBase,unittest.TestCase):
    def testAdd(self):
        self._catalog.addColumn('id')
        self.assertEqual(self._catalog.schema.has_key('id'), 1,
                         'add column failed')

    def testAddBad(self):
        from Products.ZCatalog.Catalog import CatalogError
        self.assertRaises(CatalogError, self._catalog.addColumn, '_id')

    def testDel(self):
        self._catalog.addColumn('id')
        self._catalog.delColumn('id')
        self.assert_(self._catalog.schema.has_key('id') != 1,
                     'del column failed')

class TestAddDelIndexes(CatalogBase, unittest.TestCase):
    def testAddFieldIndex(self):
        idx = FieldIndex('id')
        self._catalog.addIndex('id', idx)
        self.assert_(isinstance(self._catalog.indexes['id'],
                                type(FieldIndex('id'))),
                     'add field index failed')

    def testAddTextIndex(self):
        self._catalog.lexicon = PLexicon('lexicon')
        idx = ZCTextIndex('id', caller=self._catalog,
                          index_factory=OkapiIndex, lexicon_id='lexicon')
        self._catalog.addIndex('id', idx)
        i = self._catalog.indexes['id']
        self.assert_(isinstance(i, ZCTextIndex), 'add text index failed')

    def testAddKeywordIndex(self):
        idx = KeywordIndex('id')
        self._catalog.addIndex('id', idx)
        i = self._catalog.indexes['id']
        self.assert_(isinstance(i, type(KeywordIndex('id'))),
                     'add kw index failed')

    def testDelFieldIndex(self):
        idx = FieldIndex('id')
        self._catalog.addIndex('id', idx)
        self._catalog.delIndex('id')
        self.assert_(self._catalog.indexes.has_key('id') != 1,
                     'del index failed')

    def testDelTextIndex(self):
        self._catalog.lexicon = PLexicon('lexicon')
        idx = ZCTextIndex('id', caller=self._catalog,
                          index_factory=OkapiIndex, lexicon_id='lexicon')
        self._catalog.addIndex('id', idx)
        self._catalog.delIndex('id')
        self.assert_(self._catalog.indexes.has_key('id') != 1,
                     'del index failed')

    def testDelKeywordIndex(self):
        idx = KeywordIndex('id')
        self._catalog.addIndex('id', idx)
        self._catalog.delIndex('id')
        self.assert_(self._catalog.indexes.has_key('id') != 1,
                     'del index failed')

# Removed unittests dealing with catalog instantiation and vocabularies
# since catalog no longer creates/manages vocabularies automatically (Casey)

# Test of the ZCatalog object, as opposed to Catalog

class zdummy(ExtensionClass.Base):
    def __init__(self, num):
        self.num = num

    def title(self):
        return '%d' % self.num

class zdummyFalse(zdummy):

    def __nonzero__(self):
        return False

# make objects with failing __len__ and __nonzero__
class dummyLenFail(zdummy):
    def __init__(self, num, fail):
        zdummy.__init__(self, num)
        self.fail = fail

    def __len__(self):
        self.fail("__len__() was called")

class dummyNonzeroFail(zdummy):
    def __init__(self, num, fail):
        zdummy.__init__(self, num)
        self.fail = fail

    def __nonzero__(self):
        self.fail("__nonzero__() was called")

class FakeTraversalError(KeyError):
    """fake traversal exception for testing"""

class fakeparent(Implicit):
    # fake parent mapping unrestrictedTraverse to
    # catalog.resolve_path as simulated by TestZCatalog
    def __init__(self, d):
        self.d = d

    marker = object()

    def unrestrictedTraverse(self, path, default=marker):
        result = self.d.get(path, default)
        if result is self.marker:
            raise FakeTraversalError(path)
        return result

class TestZCatalog(unittest.TestCase):

    def setUp(self):
        from Products.ZCatalog.ZCatalog import ZCatalog
        self._catalog = ZCatalog('Catalog')
        self._catalog.resolve_path = self._resolve_num
        self._catalog.addIndex('title', 'KeywordIndex')
        self._catalog.addColumn('title')

        self.upper = 10

        self.d = {}
        for x in range(0, self.upper):
            # make uid a string of the number
            ob = zdummy(x)
            self.d[str(x)] = ob
            self._catalog.catalog_object(ob, str(x))
        
    def _resolve_num(self, num):
        return self.d[num]

    def test_z3interfaces(self):
        from Products.ZCatalog.interfaces import IZCatalog
        from Products.ZCatalog.ZCatalog import ZCatalog
        from zope.interface.verify import verifyClass

        verifyClass(IZCatalog, ZCatalog)

    def testGetMetadataForUID(self):
        testNum = str(self.upper - 3) # as good as any..
        data = self._catalog.getMetadataForUID(testNum)
        self.assertEqual(data['title'], testNum)

    def testGetIndexDataForUID(self):
        testNum = str(self.upper - 3)
        data = self._catalog.getIndexDataForUID(testNum)
        self.assertEqual(data['title'][0], testNum)

    def testSearch(self):
        query = {'title': ['5','6','7']}
        sr = self._catalog.searchResults(query)
        self.assertEqual(len(sr), 3)
        sr = self._catalog.search(query)
        self.assertEqual(len(sr), 3)

    def testUpdateMetadata(self):
        self._catalog.catalog_object(zdummy(1), '1')
        data = self._catalog.getMetadataForUID('1')
        self.assertEqual(data['title'], '1')
        self._catalog.catalog_object(zdummy(2), '1', update_metadata=0)
        data = self._catalog.getMetadataForUID('1')
        self.assertEqual(data['title'], '1')
        self._catalog.catalog_object(zdummy(2), '1', update_metadata=1)
        data = self._catalog.getMetadataForUID('1')
        self.assertEqual(data['title'], '2')
        # update_metadata defaults to true, test that here
        self._catalog.catalog_object(zdummy(1), '1')
        data = self._catalog.getMetadataForUID('1')
        self.assertEqual(data['title'], '1')

    def testReindexIndexDoesntDoMetadata(self):
        self.d['0'].num = 9999
        self._catalog.reindexIndex('title', {})
        data = self._catalog.getMetadataForUID('0')
        self.assertEqual(data['title'], '0')
    
    def testReindexIndexesFalse(self):
        # setup
        false_id = self.upper + 1
        ob = zdummyFalse(false_id)
        self.d[str(false_id)] = ob
        self._catalog.catalog_object(ob, str(false_id))
        # test, object evaluates to false; there was bug which caused the
        # object to be removed from index
        ob.num = 9999
        self._catalog.reindexIndex('title', {})
        result = self._catalog(title='9999')
        self.assertEquals(1, len(result))

    def testBooleanEvalOn_manage_catalogObject(self):
        self.d['11'] = dummyLenFail(11, self.fail)
        self.d['12'] = dummyNonzeroFail(12, self.fail)
        # create a fake response that doesn't bomb on manage_catalogObject()
        class myresponse:
            def redirect(self, url):
                pass
        # this next call should not fail
        self._catalog.manage_catalogObject(None, myresponse(), 'URL1', urls=('11', '12'))

    def testBooleanEvalOn_refreshCatalog_getobject(self):
        # wrap catalog under the fake parent providing unrestrictedTraverse()
        catalog = self._catalog.__of__(fakeparent(self.d))
        # replace entries to test refreshCatalog
        self.d['0'] = dummyLenFail(0, self.fail)
        self.d['1'] = dummyNonzeroFail(1, self.fail)
        # this next call should not fail
        catalog.refreshCatalog()

        for uid in ('0', '1'):
            rid = catalog.getrid(uid)
            # neither should these
            catalog.getobject(rid)

    def test_getobject_doesntMaskTraversalErrorsAndDoesntDelegateTo_resolve_url(self):
        # wrap catalog under the fake parent providing unrestrictedTraverse()
        catalog = self._catalog.__of__(fakeparent(self.d))
        # make resolve_url fail if ZCatalog falls back on it
        def resolve_url(path, REQUEST):
            self.fail(".resolve_url() should not be called by .getobject()")
        catalog.resolve_url = resolve_url

        # traversal should work at first
        rid0 = catalog.getrid('0')
        # lets set it up so the traversal fails
        del self.d['0']
        self.assertRaises(FakeTraversalError, catalog.getobject, rid0, REQUEST=object())
        # and if there is a None at the traversal point, that's where it should return
        self.d['0'] = None
        self.assertEquals(catalog.getobject(rid0), None)

class dummy(ExtensionClass.Base):
    att1 = 'att1'
    att2 = 'att2'
    att3 = ['att3']
    def __init__(self, num):
        self.num = num

    def col1(self):
        return 'col1'

    def col2(self):
        return 'col2'

    def col3(self):
        return ['col3']

class TestCatalogObject(unittest.TestCase):

    upper = 1000

    nums = range(upper)
    for i in range(upper):
        j = random.randrange(0, upper)
        tmp = nums[i]
        nums[i] = nums[j]
        nums[j] = tmp

    def setUp(self):
        self._catalog = Catalog()
        self._catalog.lexicon = PLexicon('lexicon')
        col1 = FieldIndex('col1')
        col2 = ZCTextIndex('col2', caller=self._catalog,
                          index_factory=OkapiIndex, lexicon_id='lexicon')
        col3 = KeywordIndex('col3')

        self._catalog.addIndex('col1', col1)
        self._catalog.addIndex('col2', col2)
        self._catalog.addIndex('col3', col3)
        self._catalog.addColumn('col1')
        self._catalog.addColumn('col2')
        self._catalog.addColumn('col3')

        att1 = FieldIndex('att1')
        att2 = ZCTextIndex('att2', caller=self._catalog,
                          index_factory=OkapiIndex, lexicon_id='lexicon')
        att3 = KeywordIndex('att3')
        num  = FieldIndex('num')

        self._catalog.addIndex('att1', att1)
        self._catalog.addIndex('att2', att2)
        self._catalog.addIndex('att3', att3)
        self._catalog.addIndex('num', num)
        self._catalog.addColumn('att1')
        self._catalog.addColumn('att2')
        self._catalog.addColumn('att3')
        self._catalog.addColumn('num')

        for x in range(0, self.upper):
            self._catalog.catalogObject(dummy(self.nums[x]), `x`)
        self._catalog.aq_parent = dummy('foo') # fake out acquisition

    def tearDown(self):
        self._catalog = None

    def testResultLength(self):
        a = self._catalog()
        self.assertEqual(len(a), self.upper,
                         'length should be %s, its %s' % (self.upper, len(a)))

    def testEmptyMappingReturnsAll(self):
        upper = self.upper
        a = self._catalog({})
        self.assertEqual(len(a), upper,
                         'length should be %s, its %s' % (upper, len(a)))
        # Queries consisting of empty strings should do the same
        a = self._catalog({'col1':'', 'col2':'', 'col3':''})
        self.assertEqual(len(a), upper,
                         'length should be %s, its %s' % (upper, len(a)))

    def testFieldIndexLength(self):
        a = self._catalog(att1='att1')
        self.assertEqual(len(a), self.upper,
                         'should be %s, but is %s' % (self.upper, len(a)))

    def testTextIndexLength(self):
        a = self._catalog(att2='att2')
        self.assertEqual(len(a), self.upper,
                         'should be %s, but is %s' % (self.upper, len(a)))

    def testKeywordIndexLength(self):
        a = self._catalog(att3='att3')
        self.assertEqual(len(a), self.upper,
                         'should be %s, but is %s' % (self.upper, len(a)))

    def testUncatalogFieldIndex(self):
        self.uncatalog()
        a = self._catalog(att1='att1')
        self.assertEqual(len(a), 0, 'len: %s' % len(a))

    def testUncatalogTextIndex(self):
        self.uncatalog()
        a = self._catalog(att2='att2')
        self.assertEqual(len(a), 0, 'len: %s' % len(a))

    def testUncatalogKeywordIndex(self):
        self.uncatalog()
        a = self._catalog(att3='att3')
        self.assertEqual(len(a), 0, 'len: %s' % len(a))

    def testBadUncatalog(self):
        try:
            self._catalog.uncatalogObject('asdasdasd')
        except:
            self.fail('uncatalogObject raised exception on bad uid')

    def testUniqueValuesForLength(self):
        a = self._catalog.uniqueValuesFor('att1')
        self.assertEqual(len(a), 1, 'bad number of unique values %s' % a)

    def testUniqueValuesForContent(self):
        a = self._catalog.uniqueValuesFor('att1')
        self.assertEqual(a[0], 'att1', 'bad content %s' % a[0])

    def testUncatalogTwice(self):
        self._catalog.uncatalogObject(`0`)
        self.assertRaises(Exception, '_second')

    def testCatalogLength(self):
        for x in range(0, self.upper):
            self._catalog.uncatalogObject(`x`)
        self.assertEqual(len(self._catalog), 0)

    def _second(self):
        self._catalog.uncatalogObject(`0`)

    def uncatalog(self):
        for x in range(0, self.upper):
            self._catalog.uncatalogObject(`x`)

    def testGoodSortIndex(self):
        upper = self.upper
        a = self._catalog(sort_on='num')
        self.assertEqual(len(a), upper,
                         'length should be %s, its %s' % (upper, len(a)))
        for x in range(self.upper):
            self.assertEqual(a[x].num, x)

    def testBadSortIndex(self):
        self.assertRaises(CatalogError, self.badsortindex)

    def badsortindex(self):
        a = self._catalog(sort_on='foofaraw')

    def testWrongKindOfIndexForSort(self):
        self.assertRaises(CatalogError, self.wrongsortindex)

    def wrongsortindex(self):
        a = self._catalog(sort_on='att2')

    def testTextIndexQWithSortOn(self):
        upper = self.upper
        a = self._catalog(sort_on='num', att2='att2')
        self.assertEqual(len(a), upper,
                         'length should be %s, its %s' % (upper, len(a)))
        for x in range(self.upper):
            self.assertEqual(a[x].num, x)

    def testTextIndexQWithoutSortOn(self):
        upper = self.upper
        a = self._catalog(att2='att2')
        self.assertEqual(len(a), upper,
                         'length should be %s, its %s' % (upper, len(a)))
# XXX: don't know how to adjust this test for ZCTextIndex
#        for x in range(self.upper):
#            self.assertEqual(a[x].data_record_score_, 1)

    def testKeywordIndexWithMinRange(self):
        a = self._catalog(att3={'query': 'att', 'range': 'min'})
        self.assertEqual(len(a), self.upper)

    def testKeywordIndexWithMaxRange(self):
        a = self._catalog(att3={'query': 'att35', 'range': ':max'})
        self.assertEqual(len(a), self.upper)

    def testKeywordIndexWithMinMaxRangeCorrectSyntax(self):
        a = self._catalog(att3={'query': ['att', 'att35'], 'range': 'min:max'})
        self.assertEqual(len(a), self.upper)

    def testKeywordIndexWithMinMaxRangeWrongSyntax(self):
        # checkKeywordIndex with min/max range wrong syntax.
        a = self._catalog(att3={'query': ['att'], 'range': 'min:max'})
        self.assert_(len(a) != self.upper)

    def testCombinedTextandKeywordQuery(self):
        a = self._catalog(att3='att3', att2='att2')
        self.assertEqual(len(a), self.upper)

    def testLargeSortedResultSetWithSmallIndex(self):
        # This exercises the optimization in the catalog that iterates
        # over the sort index rather than the result set when the result
        # set is much larger than the sort index.
        a = self._catalog(sort_on='att1')
        self.assertEqual(len(a), self.upper)

    def testBadSortLimits(self):
        self.assertRaises(
            AssertionError, self._catalog, sort_on='num', sort_limit=0)
        self.assertRaises(
            AssertionError, self._catalog, sort_on='num', sort_limit=-10)

    def testSortLimit(self):
        full = self._catalog(sort_on='num')
        a = self._catalog(sort_on='num', sort_limit=10)
        self.assertEqual([r.num for r in a], [r.num for r in full[:10]])
        self.assertEqual(a.actual_result_count, self.upper)
        a = self._catalog(sort_on='num', sort_limit=10, sort_order='reverse')
        rev = [r.num for r in full[-10:]]
        rev.reverse()
        self.assertEqual([r.num for r in a], rev)
        self.assertEqual(a.actual_result_count, self.upper)

    def testBigSortLimit(self):
        a = self._catalog(sort_on='num', sort_limit=self.upper*3)
        self.assertEqual(a.actual_result_count, self.upper)
        self.assertEqual(a[0].num, 0)
        a = self._catalog(
            sort_on='num', sort_limit=self.upper*3, sort_order='reverse')
        self.assertEqual(a.actual_result_count, self.upper)
        self.assertEqual(a[0].num, self.upper - 1)

    def testUpdateMetadataFalse(self):
        ob = dummy(9999)
        self._catalog.catalogObject(ob, `9999`)
        brain = self._catalog(num=9999)[0]
        self.assertEqual(brain.att1, 'att1')
        ob.att1 = 'foobar'
        self._catalog.catalogObject(ob, `9999`, update_metadata=0)
        brain = self._catalog(num=9999)[0]
        self.assertEqual(brain.att1, 'att1')
        self._catalog.catalogObject(ob, `9999`)
        brain = self._catalog(num=9999)[0]
        self.assertEqual(brain.att1, 'foobar')


class objRS(ExtensionClass.Base):

    def __init__(self,num):
        self.number = num

class TestRS(unittest.TestCase):

    def setUp(self):
        self._catalog    = Catalog()
        index = FieldIndex('number')
        self._catalog.addIndex('number',  index)
        self._catalog.addColumn('number')

        for i in range(5000):
            obj = objRS(random.randrange(0,20000))
            self._catalog.catalogObject(obj,i)

        self._catalog.aq_parent = objRS(200)

    def testRangeSearch(self):
        for i in range(1000):
            m = random.randrange(0,20000)
            n = m + 1000

            for r  in self._catalog.searchResults(
                 number= {'query': (m,n) , 'range' : 'min:max' } ):
                size = r.number
                self.assert_(m<=size and size<=n,
                             "%d vs [%d,%d]" % (r.number,m,n))

class TestMerge(unittest.TestCase):
    # Test merging results from multiple catalogs

    def setUp(self):
        self.catalogs = []
        for i in range(3):
            cat = Catalog()
            cat.lexicon = PLexicon('lexicon')
            cat.addIndex('num', FieldIndex('num'))
            cat.addIndex('big', FieldIndex('big'))
            i = ZCTextIndex('title', caller=cat, index_factory=OkapiIndex,
                            lexicon_id='lexicon')
            cat.addIndex('title', i)
            cat.aq_parent = zdummy(16336)
            for i in range(10):
                obj = zdummy(i)
                obj.big = i > 5
                cat.catalogObject(obj, str(i))
            self.catalogs.append(cat)

    def testNoFilterOrSort(self):
        from Products.ZCatalog.Catalog import mergeResults
        results = [cat.searchResults(_merge=0) for cat in self.catalogs]
        merged_rids = [r.getRID() for r in mergeResults(
            results, has_sort_keys=False, reverse=False)]
        expected = [r.getRID() for r in chain(*results)]
        self.assertEqual(sort(merged_rids), sort(expected))

    def testSortedOnly(self):
        from Products.ZCatalog.Catalog import mergeResults
        results = [cat.searchResults(sort_on='num', _merge=0)
                   for cat in self.catalogs]
        merged_rids = [r.getRID() for r in mergeResults(
            results, has_sort_keys=True, reverse=False)]
        expected = sort(chain(*results))
        expected = [rid for sortkey, rid, getitem in expected]
        self.assertEqual(merged_rids, expected)

    def testSortReverse(self):
        from Products.ZCatalog.Catalog import mergeResults
        results = [cat.searchResults(sort_on='num', _merge=0)
                   for cat in self.catalogs]
        merged_rids = [r.getRID() for r in mergeResults(
            results, has_sort_keys=True, reverse=True)]
        expected = sort(chain(*results))
        expected.reverse()
        expected = [rid for sortkey, rid, getitem in expected]
        self.assertEqual(merged_rids, expected)

    def testLimitSort(self):
        from Products.ZCatalog.Catalog import mergeResults
        results = [cat.searchResults(sort_on='num', sort_limit=2, _merge=0)
                   for cat in self.catalogs]
        merged_rids = [r.getRID() for r in mergeResults(
            results, has_sort_keys=True, reverse=False)]
        expected = sort(chain(*results))
        expected = [rid for sortkey, rid, getitem in expected]
        self.assertEqual(merged_rids, expected)

    def testScored(self):
        from Products.ZCatalog.Catalog import mergeResults
        results = [cat.searchResults(title='4 or 5 or 6', _merge=0)
                   for cat in self.catalogs]
        merged_rids = [r.getRID() for r in mergeResults(
            results, has_sort_keys=True, reverse=False)]
        expected = sort(chain(*results))
        expected = [rid for sortkey, (nscore, score, rid), getitem in expected]
        self.assertEqual(merged_rids, expected)

    def testSmallIndexSort(self):
        # Test that small index sort optimization is not used for merging
        from Products.ZCatalog.Catalog import mergeResults
        results = [cat.searchResults(sort_on='big', _merge=0)
                   for cat in self.catalogs]
        merged_rids = [r.getRID() for r in mergeResults(
            results, has_sort_keys=True, reverse=False)]
        expected = sort(chain(*results))
        expected = [rid for sortkey, rid, getitem in expected]
        self.assertEqual(merged_rids, expected)


class PickySecurityManager:
    def __init__(self, badnames=[]):
        self.badnames = badnames
    def validateValue(self, value):
        return 1
    def validate(self, accessed, container, name, value):
        if name not in self.badnames:
            return 1
        raise Unauthorized(name)


class TestZCatalogGetObject(unittest.TestCase):
    # Test what objects are returned by brain.getObject()

    _old_flag = None

    def setUp(self):
        from Products.ZCatalog.ZCatalog import ZCatalog
        catalog = ZCatalog('catalog')
        catalog.addIndex('id', 'FieldIndex')
        root = Folder('')
        root.getPhysicalRoot = lambda: root
        self.root = root
        self.root.catalog = catalog

    def tearDown(self):
        noSecurityManager()
        if self._old_flag is not None:
            self._restore_getObject_flag()
    
    def _init_getObject_flag(self, flag):
        from Products.ZCatalog import CatalogBrains
        self._old_flag = CatalogBrains.GETOBJECT_RAISES
        CatalogBrains.GETOBJECT_RAISES = flag

    def _restore_getObject_flag(self):
        from Products.ZCatalog import CatalogBrains
        CatalogBrains.GETOBJECT_RAISES = self._old_flag

    def test_getObject_found(self):
        # Check normal traversal
        root = self.root
        catalog = root.catalog
        root.ob = Folder('ob')
        catalog.catalog_object(root.ob)
        brain = catalog.searchResults()[0]
        self.assertEqual(brain.getPath(), '/ob')
        self.assertEqual(brain.getObject().getId(), 'ob')

    def test_getObject_missing_raises_NotFound(self):
        # Check that if the object is missing we raise
        from zExceptions import NotFound
        self._init_getObject_flag(True)
        root = self.root
        catalog = root.catalog
        root.ob = Folder('ob')
        catalog.catalog_object(root.ob)
        brain = catalog.searchResults()[0]
        del root.ob
        self.assertRaises((NotFound, AttributeError, KeyError), brain.getObject)

    def test_getObject_restricted_raises_Unauthorized(self):
        # Check that if the object's security does not allow traversal,
        # None is returned
        from zExceptions import NotFound
        self._init_getObject_flag(True)
        root = self.root
        catalog = root.catalog
        root.fold = Folder('fold')
        root.fold.ob = Folder('ob')
        catalog.catalog_object(root.fold.ob)
        brain = catalog.searchResults()[0]
        # allow all accesses
        pickySecurityManager = PickySecurityManager()
        setSecurityManager(pickySecurityManager)
        self.assertEqual(brain.getObject().getId(), 'ob')
        # disallow just 'ob' access
        pickySecurityManager = PickySecurityManager(['ob'])
        setSecurityManager(pickySecurityManager)
        self.assertRaises(Unauthorized, brain.getObject)
        # disallow just 'fold' access
        pickySecurityManager = PickySecurityManager(['fold'])
        setSecurityManager(pickySecurityManager)
        ob = brain.getObject()
        self.failIf(ob is None)
        self.assertEqual(ob.getId(), 'ob')

    def test_getObject_missing_returns_None(self):
        # Check that if the object is missing None is returned
        self._init_getObject_flag(False)
        root = self.root
        catalog = root.catalog
        root.ob = Folder('ob')
        catalog.catalog_object(root.ob)
        brain = catalog.searchResults()[0]
        del root.ob
        self.assertEqual(brain.getObject(), None)

    def test_getObject_restricted_returns_None(self):
        # Check that if the object's security does not allow traversal,
        # None is returned
        self._init_getObject_flag(False)
        root = self.root
        catalog = root.catalog
        root.fold = Folder('fold')
        root.fold.ob = Folder('ob')
        catalog.catalog_object(root.fold.ob)
        brain = catalog.searchResults()[0]
        # allow all accesses
        pickySecurityManager = PickySecurityManager()
        setSecurityManager(pickySecurityManager)
        self.assertEqual(brain.getObject().getId(), 'ob')
        # disallow just 'ob' access
        pickySecurityManager = PickySecurityManager(['ob'])
        setSecurityManager(pickySecurityManager)
        self.assertEqual(brain.getObject(), None)
        # disallow just 'fold' access
        pickySecurityManager = PickySecurityManager(['fold'])
        setSecurityManager(pickySecurityManager)
        ob = brain.getObject()
        self.failIf(ob is None)
        self.assertEqual(ob.getId(), 'ob')

    # Now test _unrestrictedGetObject

    def test_unrestrictedGetObject_found(self):
        # Check normal traversal
        root = self.root
        catalog = root.catalog
        root.ob = Folder('ob')
        catalog.catalog_object(root.ob)
        brain = catalog.searchResults()[0]
        self.assertEqual(brain.getPath(), '/ob')
        self.assertEqual(brain._unrestrictedGetObject().getId(), 'ob')

    def test_unrestrictedGetObject_restricted(self):
        # Check that if the object's security does not allow traversal,
        # it's still is returned
        root = self.root
        catalog = root.catalog
        root.fold = Folder('fold')
        root.fold.ob = Folder('ob')
        catalog.catalog_object(root.fold.ob)
        brain = catalog.searchResults()[0]
        # allow all accesses
        pickySecurityManager = PickySecurityManager()
        setSecurityManager(pickySecurityManager)
        self.assertEqual(brain._unrestrictedGetObject().getId(), 'ob')
        # disallow just 'ob' access
        pickySecurityManager = PickySecurityManager(['ob'])
        setSecurityManager(pickySecurityManager)
        self.assertEqual(brain._unrestrictedGetObject().getId(), 'ob')
        # disallow just 'fold' access
        pickySecurityManager = PickySecurityManager(['fold'])
        setSecurityManager(pickySecurityManager)
        self.assertEqual(brain._unrestrictedGetObject().getId(), 'ob')

    def test_unrestrictedGetObject_missing_raises_NotFound(self):
        # Check that if the object is missing we raise
        from zExceptions import NotFound
        self._init_getObject_flag(True)
        root = self.root
        catalog = root.catalog
        root.ob = Folder('ob')
        catalog.catalog_object(root.ob)
        brain = catalog.searchResults()[0]
        del root.ob
        self.assertRaises((NotFound, AttributeError, KeyError),
                          brain._unrestrictedGetObject)

    def test_unrestrictedGetObject_missing_returns_None(self):
        # Check that if the object is missing None is returned
        self._init_getObject_flag(False)
        root = self.root
        catalog = root.catalog
        root.ob = Folder('ob')
        catalog.catalog_object(root.ob)
        brain = catalog.searchResults()[0]
        del root.ob
        self.assertEqual(brain._unrestrictedGetObject(), None)


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest( unittest.makeSuite( TestAddDelColumn ) )
    suite.addTest( unittest.makeSuite( TestAddDelIndexes ) )
    suite.addTest( unittest.makeSuite( TestZCatalog ) )
    suite.addTest( unittest.makeSuite( TestCatalogObject ) )
    suite.addTest( unittest.makeSuite( TestRS ) )
    suite.addTest( unittest.makeSuite( TestMerge ) )
    suite.addTest( unittest.makeSuite( TestZCatalogGetObject ) )
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
