#!/usr/bin/env python, unittest

# Unittests for Catalog

import os,sys, unittest

import ZODB, OFS.Application
from ZODB.DemoStorage import DemoStorage
from ZODB.DB import DB
from Products import ZCatalog
from Products.ZCatalog import ZCatalog,Vocabulary
from Products.ZCatalog.Catalog import Catalog, CatalogError
import ExtensionClass

from Products.PluginIndexes.FieldIndex.FieldIndex import FieldIndex
from Products.PluginIndexes.TextIndex.TextIndex import TextIndex
from Products.PluginIndexes.TextIndex.Lexicon import  Lexicon
from Products.PluginIndexes.KeywordIndex.KeywordIndex import KeywordIndex

import whrandom,string, unittest, random


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
    get_transaction().commit()

    # Init products
    #OFS.Application.initialize(app)
    OFS.Application.install_products(app) # XXX: this is still icky

    return app

app = createDatabase()


################################################################################
# Stuff of Chris
################################################################################

from AccessControl.SecurityManagement import newSecurityManager
from AccessControl.SecurityManagement import noSecurityManager

class DummyUser:

    def __init__( self, name ):
        self._name = name

    def getUserName( self ):
        return self._name


class CatalogBase:
    def setUp(self):
        self._vocabulary = Vocabulary.Vocabulary('Vocabulary', 'Vocabulary',
                                                 globbing=1)
        self._catalog = Catalog()

    def tearDown(self):
        self._vocabulary = self._catalog = None

class TestAddDelColumn(CatalogBase,unittest.TestCase):
    def testAdd(self):
        self._catalog.addColumn('id')
        assert self._catalog.schema.has_key('id') == 1, 'add column failed'

    def testAddBad(self):
        try:
            self._catalog.addColumn('_id')
        except:
            pass
        else:
            raise 'invalid metadata column check failed'

    def testDel(self):
        self._catalog.addColumn('id')
        self._catalog.delColumn('id')
        assert self._catalog.schema.has_key('id') != 1, 'del column failed'

class TestAddDelIndexes(CatalogBase, unittest.TestCase):
    def testAddFieldIndex(self):
        idx = FieldIndex('id')
        self._catalog.addIndex('id', idx)
        assert type(self._catalog.indexes['id']) is type(FieldIndex('id')),\
               'add field index failed'

    def testAddTextIndex(self):
        idx = TextIndex('id')
        self._catalog.addIndex('id', idx)
        i = self._catalog.indexes['id']
        assert type(i) is type(TextIndex('id', None, None, Lexicon())),\
               'add text index failed'

    def testAddKeywordIndex(self):
        idx = KeywordIndex('id')
        self._catalog.addIndex('id', idx)
        i = self._catalog.indexes['id']
        assert type(i) is type(KeywordIndex('id')), 'add kw index failed'

    def testDelFieldIndex(self):
        idx = FieldIndex('id')
        self._catalog.addIndex('id', idx)
        self._catalog.delIndex('id')
        assert self._catalog.indexes.has_key('id') != 1, 'del index failed'

    def testDelTextIndex(self):
        idx = TextIndex('id')
        self._catalog.addIndex('id', idx)
        self._catalog.delIndex('id')
        assert self._catalog.indexes.has_key('id') != 1, 'del index failed'

    def testDelKeywordIndex(self):
        idx = KeywordIndex('id')
        self._catalog.addIndex('id', idx)
        self._catalog.delIndex('id')
        assert self._catalog.indexes.has_key('id') != 1, 'del index failed'

# Removed unittests dealing with catalog instantiation and vocabularies
# since catalog no longer creates/manages vocabularies automatically (Casey)

# Test of the ZCatalog object, as opposed to Catalog

class TestZCatalog(unittest.TestCase):
    def setUp(self):
        self._catalog = ZCatalog.ZCatalog('Catalog')
        self._catalog.addIndex('title', 'KeywordIndex')
        self._catalog.addColumn('title')
        
        self.upper = 10

        class dummy(ExtensionClass.Base):
            def __init__(self, num):
                self.num = num
    
            def title(self):
                return '%d' % self.num

        for x in range(0, self.upper):
            # make uid a string of the number
            self._catalog.catalog_object(dummy(x), str(x))


    def testGetMetadataForUID(self):
        testNum = str(self.upper - 3) # as good as any..
        data = self._catalog.getMetadataForUID(testNum)
        assert data['title'] == testNum

    def testGetIndexDataForUID(self):
        testNum = str(self.upper - 3) 
        data = self._catalog.getIndexDataForUID(testNum)
        assert data['title'][0] == testNum
        
    def testSearch(self):
        query = {'title': ['5','6','7']}
        sr = self._catalog.searchResults(query)
        self.assertEqual(len(sr), 3)
        sr = self._catalog.search(query)
        self.assertEqual(len(sr), 3)

class TestCatalogObject(unittest.TestCase):
    
    upper = 1000
    
    nums = range(upper)
    for i in range(upper):
        j = random.randint(0, upper-1)
        tmp = nums[i]
        nums[i] = nums[j]
        nums[j] = tmp
        
    def setUp(self):
        self._vocabulary = Vocabulary.Vocabulary('Vocabulary','Vocabulary',
                                                 globbing=1)

        col1 = FieldIndex('col1')
        col2 = TextIndex('col2')
        col3 = KeywordIndex('col3')

        self._catalog = Catalog()
        self._catalog.addIndex('col1', col1)
        self._catalog.addIndex('col2', col2)
        self._catalog.addIndex('col3', col3)
        self._catalog.addColumn('col1')
        self._catalog.addColumn('col2')
        self._catalog.addColumn('col3')

        att1 = FieldIndex('att1')
        att2 = TextIndex('att2')
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

        
        for x in range(0, self.upper):
            self._catalog.catalogObject(dummy(self.nums[x]), `x`)
        self._catalog.aq_parent = dummy('foo') # fake out acquisition

    def tearDown(self):
        self._vocabulary = self._catalog = None

    def testResultLength(self):
        upper = self.upper
        a = self._catalog()
        assert len(a) == upper, 'length should be %s, its %s'%(upper, len(a))

    def testEmptyMappingReturnsAll(self):
        upper = self.upper
        a = self._catalog({})
        assert len(a) == upper, 'length should be %s, its %s'%(upper, len(a))
        # Queries consisting of empty strings should do the same
        a = self._catalog({'col1':'', 'col2':'', 'col3':''})
        assert len(a) == upper, 'length should be %s, its %s'%(upper, len(a))

    def testFieldIndexLength(self):
        a = self._catalog(att1='att1')
        assert len(a) == self.upper, 'should be %s, but is %s' % (self.upper,
                                                                  len(a))
    def testTextIndexLength(self):
        a = self._catalog(att2='att2')
        assert len(a) == self.upper, 'should be %s, but is %s' % (self.upper,
                                                                  len(a))

    def testKeywordIndexLength(self):
        a = self._catalog(att3='att3')
        assert len(a) == self.upper, 'should be %s, but is %s' % (self.upper,
                                                                  len(a))

    def testUncatalogFieldIndex(self):
        self.uncatalog()
        a = self._catalog(att1='att1')
        assert len(a) == 0, 'len: %s' % (len(a))

    def testUncatalogTextIndex(self):
        self.uncatalog()
        a = self._catalog(att2='att2')
        assert len(a) == 0, 'len: %s' % (len(a))

    def testUncatalogKeywordIndex(self):
        self.uncatalog()
        a = self._catalog(att3='att3')
        assert len(a) == 0, 'len: %s'%(len(a))

    def testBadUncatalog(self):
        try:
            self._catalog.uncatalogObject('asdasdasd')
        except:
            assert 1==2, 'uncatalogObject raised exception on bad uid'

    def testUniqueValuesForLength(self):
        a = self._catalog.uniqueValuesFor('att1')
        assert len(a) == 1, 'bad number of unique values %s' % str(a)

    def testUniqueValuesForContent(self):
        a = self._catalog.uniqueValuesFor('att1')
        assert a[0] == 'att1', 'bad content %s' % str(a[0])

    def testUncatalogTwice(self):
        self._catalog.uncatalogObject(`0`)
        self.assertRaises(Exception, '_second')

    def testCatalogLength(self):
        for x in range(0, self.upper):
            self._catalog.uncatalogObject(`x`)
        assert len(self._catalog) == 0

    def _second(self):
        self._catalog.uncatalogObject(`0`)

    def uncatalog(self):
        for x in range(0, self.upper):
            self._catalog.uncatalogObject(`x`)

    def testGoodSortIndex(self):
        upper = self.upper
        a = self._catalog(sort_on='num')
        assert len(a) == upper, 'length should be %s, its %s'%(upper, len(a))
        for x in range(self.upper):
            assert a[x].num == x, x

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
        assert len(a) == upper, 'length should be %s, its %s'%(upper, len(a))
        for x in range(self.upper):
            assert a[x].num == x, x

    def testTextIndexQWithoutSortOn(self):
        upper = self.upper
        a = self._catalog(att2='att2')
        assert len(a) == upper, 'length should be %s, its %s'%(upper, len(a))
        for x in range(self.upper):
            assert a[x].data_record_score_ == 1, a[x].data_record_score_

    def testKeywordIndexWithMinRange(self):
        a = self._catalog(att3='att', att3_usage='range:min')
        assert len(a) == self.upper

    def testKeywordIndexWithMaxRange(self):
        a = self._catalog(att3='att35', att3_usage='range:max')
        assert len(a) == self.upper

    def testKeywordIndexWithMinMaxRangeCorrectSyntax(self):
        a = self._catalog(att3=['att', 'att35'], att3_usage='range:min:max')
        assert len(a) == self.upper

    def testKeywordIndexWithMinMaxRangeWrongSyntax(self):
        # checkKeywordIndex with min/max range wrong syntax.
        a = self._catalog(att3=['att'], att3_usage='range:min:max')
        assert len(a) != self.upper

    def testCombinedTextandKeywordQuery(self):
        a = self._catalog(att3='att3', att2='att2')
        assert len(a) == self.upper

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
        

class objRS(ExtensionClass.Base):

    def __init__(self,num):
        self.number = num

class testRS(unittest.TestCase):

    def setUp(self):
        self._vocabulary = Vocabulary.Vocabulary('Vocabulary','Vocabulary'
                                                , globbing=1)
        self._catalog    = Catalog()
        index = FieldIndex('number')
        self._catalog.addIndex('number',  index)
        self._catalog.addColumn('number')

        for i in range(5000):
            obj = objRS(whrandom.randint(0,20000))
            self._catalog.catalogObject(obj,i)

        self._catalog.aq_parent = objRS(200)

    def testRangeSearch(self):
        for i in range(10000):

            m = whrandom.randint(0,20000)
            n = m + 1000

            for r  in self._catalog.searchResults(
                { "number" : (m,n) ,
                  "length_usage" : "range:min:max" } ):
                size = r.number
                assert m<=size and size<=n , "%d vs [%d,%d]" % (r.number,m,n)



def test_suite():
    suite = unittest.TestSuite()
    suite.addTest( unittest.makeSuite( TestAddDelColumn ) )
    suite.addTest( unittest.makeSuite( TestAddDelIndexes ) )
    suite.addTest( unittest.makeSuite( TestZCatalog ) )
    suite.addTest( unittest.makeSuite( TestCatalogObject ) )
    suite.addTest( unittest.makeSuite( testRS ) )
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
    
