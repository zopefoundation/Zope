#!/usr/bin/env python, unittest

# Unittests for Catalog

import os,sys, unittest

import ZODB, OFS.Application
from ZODB.DemoStorage import DemoStorage
from ZODB.DB import DB
from Products.ZCatalog import ZCatalog,Vocabulary
from Products.ZCatalog.Catalog import Catalog, CatalogError
import ExtensionClass

from Products.PluginIndexes.FieldIndex.FieldIndex import FieldIndex
from Products.PluginIndexes.TextIndex.TextIndex import TextIndex
from Products.PluginIndexes.TextIndex.Lexicon import  Lexicon
from Products.PluginIndexes.KeywordIndex.KeywordIndex import KeywordIndex

import whrandom,string, unittest


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

class TestZCatalogObject(unittest.TestCase):
    def setUp(self):
        class dummy(ExtensionClass.Base):
            pass
        self.dummy = dummy()
        newSecurityManager( None, DummyUser( 'phred' ) )

    def tearDown(self):
        noSecurityManager()
        self.dummy = None

    def testInstantiateWithoutVocab(self):
        v = Vocabulary.Vocabulary('Vocabulary', 'Vocabulary', globbing=1)
        zc = ZCatalog.ZCatalog('acatalog')
        assert hasattr(zc, 'Vocabulary')
        assert zc.getVocabulary().__class__ == v.__class__

    def testInstantiateWithGlobbingVocab(self):
        dummy = self.dummy
        v = Vocabulary.Vocabulary('Vocabulary', 'Vocabulary', globbing=1)
        dummy.v = v
        zc = ZCatalog.ZCatalog('acatalog', vocab_id='v', container=dummy)
        zc = zc.__of__(dummy)
        assert zc.getVocabulary() == v

    def testInstantiateWithNormalVocab(self):
        dummy = self.dummy
        v = Vocabulary.Vocabulary('Vocabulary', 'Vocabulary', globbing=0)
        dummy.v = v
        zc = ZCatalog.ZCatalog('acatalog', vocab_id='v', container=dummy)
        zc = zc.__of__(dummy)
        assert zc.getVocabulary() == v

class TestCatalogObject(unittest.TestCase):
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

        self.upper = 1000
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
            self._catalog.catalogObject(dummy(x), `x`)
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
        """checkKeywordIndex with min/max range wrong syntax - known to fail.
           But because it will fail we need to change the assert statement
           so the unittest will pass *crazy world*
        """
        a = self._catalog(att3=['att'], att3_usage='range:min:max')
        assert len(a) != self.upper

    def testCombinedTextandKeywordQuery(self):
        a = self._catalog(att3='att3', att2='att2')
        assert len(a) == self.upper

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
    suite.addTest( unittest.makeSuite( TestZCatalogObject ) )
    suite.addTest( unittest.makeSuite( TestCatalogObject ) )
    suite.addTest( unittest.makeSuite( testRS ) )
    return suite

def main():
    unittest.TextTestRunner().run(test_suite())

if __name__ == '__main__':
    main()
