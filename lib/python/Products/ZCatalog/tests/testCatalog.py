#!/usr/bin/env python1.5

"""
    Testsuite for testing Catalogs
    $Id: testCatalog.py,v 1.6 2001/06/15 14:09:57 andreas Exp $
    
    Andreas Jung, andreas@digicool.com
    
    $Log: testCatalog.py,v $
    Revision 1.6  2001/06/15 14:09:57  andreas
    some tweaks for Python 2.1, new ZCatalog/PluginIndexes infrastructure

    Revision 1.5  2001/04/17 17:08:13  chrism
    Merging into trunk.

    Revision 1.1.6.5  2001/04/17 17:01:21  chrism
    More tests.

    Revision 1.1.6.4.2.1  2001/04/17 06:39:45  chrism
    added further tests for catalog object in test_suite.

    Revision 1.1.6.4  2001/04/05 16:18:05  chrism
    Added test for empty mapping returns all.

    Revision 1.4  2001/04/05 16:15:36  chrism
    added test for empty mapping returns all.

    Revision 1.3  2001/03/23 23:34:14  chrism
    Merge from branch.

    Revision 1.1.6.3  2001/03/23 23:32:02  chrism
    Added catalog length test.

    Revision 1.1.6.2  2001/03/23 19:38:52  chrism
    added checkUncatalogTwice test.

    Revision 1.1.6.1  2001/03/15 13:10:32  jim
    Merged changes from Catalog-BTrees-Integration branch.

    Revision 1.1.4.11  2001/03/14 18:43:16  andreas
    rearranged source code

    Revision 1.1.4.10  2001/03/14 15:12:24  andreas
    minor changes

    Revision 1.1.4.9  2001/03/13 22:45:07  andreas
    yet another try/except clause (zope mbox file seems to contain some sloppy
    messages)

    Revision 1.1.4.8  2001/03/13 22:04:20  andreas
    added try/except while reading and parsing the mbox file

    Revision 1.1.4.7  2001/03/13 16:51:07  andreas
    code cleanup

    Revision 1.1.4.6  2001/03/13 14:37:40  andreas
    prelimary version for integration into the Zope testsuites

    Revision 1.1.4.5  2001/03/11 22:33:40  andreas
    commit

    Revision 1.1.2.23  2001/03/09 16:06:10  andreas
    integrated chris unittestCatalog.py

    Revision 1.1.2.22  2001/03/09 15:05:28  andreas
    rewrote testUpdates()

    Revision 1.1.2.21  2001/03/08 18:42:28  andreas
    fixed typo

    Revision 1.1.4.4  2001/03/08 12:14:27  andreas
    minor changes

    Revision 1.1.2.20  2001/03/07 14:58:40  andreas
    *** empty log message ***

    Revision 1.1.2.19  2001/03/07 14:07:51  andreas
    Code cleanup

    Revision 1.1.2.18  2001/03/07 12:46:32  andreas
    added advanced tests

    Revision 1.1.2.17  2001/03/07 10:28:27  andreas
    reworked version now using the new thread dispatcher

    Revision 1.1.2.16  2001/03/05 15:14:51  andreas
    - minor changes in testing catalog/uncatalogObject
    - tests must now be started in the lib/python directory
    - older input sets are no longer valid (must be recreated)

"""

import os,sys
sys.path.insert(0,'.')

try:
    import Testing
except ImportError:
    sys.path[0] = "../../.."
    import Testing

os.environ['STUPID_LOG_FILE']= "debug.log"

here = os.getcwd()

import Zope
import ZODB, ZODB.FileStorage
from Products.ZCatalog import ZCatalog,Vocabulary
from Products.ZCatalog.Catalog import CatalogError
import Persistence
import ExtensionClass
from Testing import dispatcher
import keywords
from zLOG import LOG


import getopt,whrandom,time,string,mailbox,rfc822
from Testing import unittest


# maximum number of files to read for the test suite
maxFiles = 1000

# maximum number of threads for stress testa
numThreads = 4


# number of iterations for searches
searchIterations = 1000

# number of iterations for catalog/uncatalog operations
updateIterations = 100

# input mailbox file
mbox   = os.environ.get("TESTCATALOG_MBOX","/usr/home/andreas/zope.mbox")
mbox2  = os.environ.get("TESTCATALOG_MBOX2", "/usr/home/andreas/python.mbox")

dataDir = ""


#
# Don't change anything below
#


class testZODB:
    """ some wrapper stuff around ZODB """

    def __init__(self, file = "data/work/Data.fs",open=1):
    
        self.db = ZODB.DB( ZODB.FileStorage.FileStorage(file) )

        if open==1:
            self.connection = self.db.open()
            self.root = self.connection.root()

        
    def write(self,name,obj):
        self.root[name] = obj
        get_transaction().commit()

        
    def read(self,name):
        return self.root[name]

        
    def __del__(self):
        self.db.close()

        
        
class testCatalog(Persistence.Persistent,unittest.TestCase):
    """ Wrapper around the catalog stuff """

    def __init__(self,mboxname,maxfiles):
        self.msg_ids = []
        self.num_files = 0
        self.keywords = []
        self.maxfiles = maxfiles
        
        self._vocabulary = Vocabulary.Vocabulary('Vocabulary',
                            'Vocabulary', globbing=1)
        self._catalog    = ZCatalog.ZCatalog("zcatalog")
        self._catalog.addIndex('to',      'TextIndex')
        self._catalog.addIndex('sender',  'TextIndex')
        self._catalog.addIndex('subject', 'TextIndex')
        self._catalog.addIndex('content', 'TextIndex')
        self._catalog.addIndex('file_id', 'TextIndex')
        self._catalog.addColumn('file_id')
        self._catalog.addIndex('length',  'FieldIndex')
        self._catalog.addColumn('length')
        self._catalog.addIndex('date',    'FieldIndex')
        self._catalog.addIndex('keywords', "KeywordIndex")

        self.build_catalog(mboxname)


    def build_catalog(self,mboxname):

        mb = mailbox.UnixMailbox(open(mboxname,"r"))
        i = 0

        msg = mb.next()
        while msg and self.num_files<self.maxfiles:

            try:
                self.catMessage(msg)
                self.msg_ids.append(msg.dict["message-id"])
            except: 
                msg = mb.next()
                continue


            msg = mb.next()
            self.num_files = self.num_files + 1
            if self.num_files % 100==0: print self.num_files

            try:
                sub = string.split(msg.dict.get("subject",""))
            except:
                msg = mb.next()
                continue

            for s in sub: 
                if not s in self.keywords: self.keywords.append(s)
           
        self._catalog.aq_parent = None
        

    def catMessage(self,m):
        self._catalog.catalogObject( testMessage(m) , 
                                    m.dict["message-id"] )
        
    def uncatMessage(self,uid):
        self._catalog.uncatalogObject( uid )
        
            
class testMessage(ExtensionClass.Base):

    def __init__(self,msg,modify_doc=0):

        self.sender  = msg.dict.get("from","")
        self.subject = msg.dict.get("subject","")
        self.to      = msg.dict.get("to","")
        self.content = str(msg)
        self.keywords= string.split(self.subject , " ")

        if modify_doc !=0:
            self.keywords = map(self.reverse,self.keywords)
            

        self.file_id = msg.dict.get("message-id","")
   
        self.length  = len(str(msg))
        date         = msg.dict.get("date","")
        try:
            self.date    =  time.mktime(rfc822.parsedate(date)[:9])
        except: pass  

    def reverse(self,s):
        l = list(s)
        l.reverse()
        return string.join(l,"")

        
    def __del__(self):
       pass 


class BuildEnv(dispatcher.Dispatcher,unittest.TestCase):
    """ build environment """        

    def __init__(self,func,*args,**kw):

        unittest.TestCase.__init__(self,func,args,kw)
        dispatcher.Dispatcher.__init__(self,func)

        self.init_phase = 0

        self.setlog( open("dispatcher.log","a") )
        self.logn('treads=%d  searchiterations=%d' % 
                    (numThreads,searchIterations))
        self.logn('updateiterations=%d  maxfiles=%d' % 
                    (updateIterations,maxFiles))

    #############################################################        
    # Build up ZODB
    #############################################################        

        
    def buildTestEnvironment(self,args,kw):
        self.init_phase = 1
        self.dispatcher("funcTestEnvironment",("funcTestEnvironment",1,args,kw))


    def funcTestEnvironment(self,dataDir,maxFiles):

        env = self.th_setup()

        if not os.path.exists(dataDir): os.makedirs(dataDir)
        
        os.system("rm -f %s/*" % dataDir)
        zodb = testZODB("%s/Data_orig.fs" % dataDir)
            
        print "parsing and reading mailbox file %s....please wait" % mbox
        tc = testCatalog( mbox,maxFiles )
            
        print "writing Catalog to ZODB"
        zodb.write("catalog" , tc)

        print "Creating keywords file"
        kw = keywords.Keywords()
        kw.build(mbox,1000)

    
        print tc.num_files, "files read"
        print "Initalization complete"

        self.th_teardown(env)

        
class testSearches(dispatcher.Dispatcher,unittest.TestCase):
    """ test searches """

    def __init__(self,func,*args,**kw):

        unittest.TestCase.__init__(self,func,args,kw) 
        dispatcher.Dispatcher.__init__(self,func)

        self.init_phase = 0

        self.setlog( open("dispatcher.log","a") )
        

    def setUp(self):

        os.system("rm -fr data/work")
        if not os.path.exists("data/work"): os.makedirs("data/work")
        assert os.system("cp %s/Data_orig.fs data/work/Data.fs" % dataDir)==0, \
            "Error while replicating original data"
        
        self.zodb 	 	= testZODB("data/work/Data.fs",open=0)
        self.threads    = {} 
        self.init_zodb_size = self.zodb_size()

        kw = keywords.Keywords()
        kw.reload()
        self.keywords  = kw.keywords()    

        self.logn("-" * 80)
        self.logn('treads=%d  searchiterations=%d' % 
                    (numThreads,searchIterations))
        self.logn('updateiterations=%d  maxfiles=%d' % 
                    (updateIterations,maxFiles))


    def tearDown(self):
        self.log_zodb_size("before",self.init_zodb_size)
        self.log_zodb_size("after ",self.zodb_size())
        del self.zodb
        self.zodb = self.catalog = None		

    def log_zodb_size(self,s,n):
        self.logn("Size of ZODB (data/work/Data.fs) %s test : %s" % (s,n) )

    def zodb_size(self):
        return self.size2size(os.stat("data/work/Data.fs")[6])


    def size2size(self,n):
        import math
        if n <1024.0: return "%8.3lf Bytes" % n
        if n <1024.0*1024.0: return "%8.3lf KB" % (1.0*n/1024.0)
        if n <1024.0*1024.0*1024.0: return "%8.3lf MB" % (1.0*n/1024.0/1024.0)

        

    #############################################################        
    # Fulltext test
    #############################################################        


    def testFulltextIndex(self,args,kw):
        """ benchmark FulltextIndex """
        self.dispatcher('funcFulltextIndex' , 
            ('funcFulltextIndex', kw["numThreads"] , () , {} ) )


    def funcFulltextIndex(self,*args):
        """ benchmark FulltextIndex """

        cat,msg_ids = self.get_catalog()

        env = self.th_setup()

        for kw in self.keywords:
            res = cat.searchResults( {"content" : kw } )

        self.th_teardown(env)


    #############################################################        
    # Field index test
    #############################################################        

    def testFieldIndex(self,args,kw):
        """ benchmark field index"""
        self.dispatcher('funcFieldIndex' , 
            ('funcFieldIndex',kw["numThreads"] , () , {} ) )


    def funcFieldIndex(self,*args):
        """ benchmark FieldIndex """

        cat,msg_ids = self.get_catalog()

        env = self.th_setup()

        for i in range(0,searchIterations):
        
            res = cat.searchResults( {"length" : i } )
            for r in res:
                assert i==r.length , "%s should have size %d but is %s" %  \
                    (r.file_id,i,r.length)

        self.th_teardown(env)
                
    #############################################################        
    # Keyword index test
    #############################################################        

    def testKeywordIndex(self,args,kw):
        """ benchmark Keyword index"""
        self.dispatcher('funcKeywordIndex' , 
            ('funcKeywordIndex', kw["numThreads"] , () , {} ) )


    def funcKeywordIndex(self,*args):
        """ benchmark KeywordIndex """

        cat,msg_ids = self.get_catalog()
        
        env = self.th_setup()

        for kw in self.keywords:
            res = cat.searchResults( {"subject" : kw } )
#            assert len(res) != 0 , "Search result for keyword '%s' is empty" % kw
        
        self.th_teardown(env)
       
    #############################################################        
    # Field range index test
    #############################################################        

    def testFieldRangeIndex(self,args,kw):
        """ benchmark field range index"""
        self.dispatcher('funcFieldRangeIndex' , 
            ('funcFieldRangeIndex', kw["numThreads"] , () , {} ) )


    def funcFieldRangeIndex(self,*args):
        """ benchmark FieldRangeIndex """

        cat,msg_ids = self.get_catalog()

        env = self.th_setup()

        rg = []
        for i in range(searchIterations):
            m = whrandom.randint(0,10000) 
            n = m + 200
            rg.append((m,n))


        for i in range(searchIterations):
            for r  in cat.searchResults( {"length" : rg[i],"length_usage" : "range:min:max" } ):
                size = r.length
                assert rg[i][0]<=size and size<=rg[i][1] , \
                "Filesize of %s is out of range (%d,%d) %d" % (r.file_id,rg[i][0],rg[i][1],size)

        self.th_teardown(env)



    #############################################################        
    # Keyword + range index test
    #############################################################        

    def testKeywordRangeIndex(self,args,kw):
        """ benchmark Keyword range index"""
        self.dispatcher('funcKeywordRangeIndex' , 
            ('funcKeywordRangeIndex', kw["numThreads"] , () , {} ) )


    def funcKeywordRangeIndex(self,*args):
        """ benchmark Keyword & IndexRange search """

        cat,msg_ids = self.get_catalog()

        rg = []
        for i in range(len(self.keywords)):
            m = whrandom.randint(0,10000) 
            n = m + 200
            rg.append( (m,n) )

        env = self.th_setup()

        results = []            
        for i in range(len(self.keywords)):
            results.append( cat.searchResults( {"keywords":self.keywords[i], 
                                                "length" : rg[i],
                                                "length_usage" : "range:min:max" } )
                                            )

        self.th_teardown(env)


    #############################################################        
    # Test full reindexing
    #############################################################        

    def testUpdates(self,args,kw):
        """ benchmark concurrent catalog/uncatalog operations """
        self.dispatcher("testUpdates" , 
            ("funcUpdates", kw["numThreads"] , args, kw ))


    def funcUpdates(self,*args,**kw):
        """ benchmark concurrent catalog/uncatalog operations """

        uncat_conflicts = cat_conflicts = 0
        cat,msg_ids = self.get_catalog()


        msgs = self.setupUpdatesMethod(kw["numUpdates"])
        keys = msgs.keys()

        rdgen = whrandom.whrandom()
        rdgen.seed(int(time.time()) % 256,int(time.time()) % 256,int(time.time()) % 256)

        env = self.th_setup()

        for i in range(len(keys)):

            r = rdgen.randint(0,len(msgs)-1)

            mid = keys[r]
            obj = msgs[mid]

            try:
                cat.uncatalog_object(mid)

                if kw.get("commit",1)==1:
                    get_transaction().commit()            
                    time.sleep(0.1)
            except ZODB.POSException.ConflictError:
                uncat_conflicts = uncat_conflicts + 1

            try:
                cat.catalog_object(obj,mid)

                if kw.get("commit",1)==1:
                    get_transaction().commit()            
                    time.sleep(0.1)

            except ZODB.POSException.ConflictError:
                cat_conflicts = cat_conflicts + 1

        try:
            get_transaction().commit()            
        except: pass


        self.th_teardown(env,cat_conflicts=cat_conflicts,uncat_conflicts=uncat_conflicts)


    def setupUpdatesMethod(self,numUpdates):
        """ this method prepares a datastructure for the updates test.
            we are reading the first n mails from the primary mailbox.
            they are used for the update test
        """

        i = 0
        dict = {}

        mb = mailbox.UnixMailbox(open(mbox,"r"))

        msg = mb.next()
        while msg and i<numUpdates:

            obj = testMessage(msg)
   
            mid = msg.dict.get("message-id",None)
            if mid:
                dict[mid] = obj 
                i = i+1

            msg = mb.next()
       
        return dict 
    


    #############################################################        
    # Test full reindexing
    #############################################################        

    def testReindexing(self,args,kw):
        """ test reindexing of existing data """
        self.dispatcher("testReindexing" , 
            ("funcReindexing",kw["numThreads"] , (mbox,1000) , {} ))

    def testReindexingAndModify(self,args,kw):
        """ test reindexing of existing data but with modifications"""
        self.dispatcher("testReindexing" , 
            ("funcReindexing",kw["numThreads"] , (mbox,1000,1) , {} ))


    def funcReindexing(self,mbox,numfiles=100,modify_doc=0):
        """ test reindexing of existing data """

        cat_conflicts = 0
        cat,msg_ids = self.get_catalog()

        env = self.th_setup()

        mb = mailbox.UnixMailbox(open(mbox,"r"))
        i = 0

        msg = mb.next()

        while msg and i<numfiles:

            obj = testMessage(msg,modify_doc)
            if msg.dict.has_key("message-id"):
                mid = msg.dict["message-id"]
            else:
                msg = mb.next()
                continue

            try:
                cat.catalogObject(obj,mid)
                get_transaction().commit()
            except:
                cat_conflicts = cat_conflicts + 1

            msg = mb.next()
            i = i+1
            if i%100==0: print i

        self.th_teardown(env,cat_conflicts=cat_conflicts)


    #############################################################        
    # Test full reindexing
    #############################################################        
    
    def testIncrementalIndexing(self,args,kw):
        """ testing incremental indexing """
        self.dispatcher("testIncrementalIndexing" , 
            ("funcReindexing",kw["numThreads"], (mbox2,1000) , {}))


    def get_catalog(self):
        """ return a catalog object """

        # depended we are running in multithreaded mode we must take
        # care how threads open the ZODB

        connection  = self.zodb.db.open()
        root        = connection.root()
        cat	        = root["catalog"]._catalog
        msg_ids     = root['catalog'].msg_ids

        return cat,msg_ids

################################################################################
# Stuff of Chris
################################################################################


class CatalogBase:
    def setUp(self):
        self._vocabulary = Vocabulary.Vocabulary('Vocabulary', 'Vocabulary',
                                                 globbing=1)
        self._catalog = Catalog.Catalog()

    def tearDown(self):
        self._vocabulary = self._catalog = None

class TestAddDelColumn(CatalogBase, unittest.TestCase):
    def checkAdd(self):
        self._catalog.addColumn('id')
        assert self._catalog.schema.has_key('id') == 1, 'add column failed'

    def checkAddBad(self):
        try:
            self._catalog.addColumn('_id')
        except:
            pass
        else:
            raise 'invalid metadata column check failed'

    def checkDel(self):
        self._catalog.addColumn('id')
        self._catalog.delColumn('id')
        assert self._catalog.schema.has_key('id') != 1, 'del column failed'

class TestAddDelIndexes(CatalogBase, unittest.TestCase):
    def checkAddFieldIndex(self):
        self._catalog.addIndex('id', 'FieldIndex')
        assert type(self._catalog.indexes['id']) is type(UnIndex('id')),\
               'add field index failed'

    def checkAddTextIndex(self):
        self._catalog.addIndex('id', 'TextIndex')
        i = self._catalog.indexes['id']
        assert type(i) is type(UnTextIndex('id', None, None, Lexicon())),\
               'add text index failed'

    def checkAddKeywordIndex(self):
        self._catalog.addIndex('id', 'KeywordIndex')
        i = self._catalog.indexes['id']
        assert type(i) is type(UnKeywordIndex('id')), 'add kw index failed'

    def checkDelFieldIndex(self):
        self._catalog.addIndex('id', 'FieldIndex')
        self._catalog.delIndex('id')
        assert self._catalog.indexes.has_key('id') != 1, 'del index failed'
        
    def checkDelTextIndex(self):
        self._catalog.addIndex('id', 'TextIndex')
        self._catalog.delIndex('id')
        assert self._catalog.indexes.has_key('id') != 1, 'del index failed'
        
    def checkDelKeywordIndex(self):
        self._catalog.addIndex('id', 'KeywordIndex')
        self._catalog.delIndex('id')
        assert self._catalog.indexes.has_key('id') != 1, 'del index failed'

class TestZCatalogObject(unittest.TestCase):
    def setUp(self):
        class dummy(ExtensionClass.Base):
            pass
        self.dummy = dummy()

    def tearDown(self):
        self.dummy = None

    def checkInstantiateWithoutVocab(self):
        v = Vocabulary.Vocabulary('Vocabulary', 'Vocabulary', globbing=1)
        zc = ZCatalog.ZCatalog('acatalog')
        assert hasattr(zc, 'Vocabulary')
        assert zc.getVocabulary().__class__ == v.__class__

    def checkInstantiateWithGlobbingVocab(self):
        dummy = self.dummy
        v = Vocabulary.Vocabulary('Vocabulary', 'Vocabulary', globbing=1)
        dummy.v = v
        zc = ZCatalog.ZCatalog('acatalog', vocab_id='v', container=dummy)
        zc = zc.__of__(dummy)
        assert zc.getVocabulary() == v

    def checkInstantiateWithNormalVocab(self):
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
        self._catalog = Catalog.Catalog()
        self._catalog.addIndex('col1', 'FieldIndex')
        self._catalog.addIndex('col2', 'TextIndex')
        self._catalog.addIndex('col3', 'KeywordIndex')
        self._catalog.addColumn('col1') 
        self._catalog.addColumn('col2')
        self._catalog.addColumn('col3')
        
        self._catalog.addIndex('att1', 'FieldIndex')
        self._catalog.addIndex('att2', 'TextIndex')
        self._catalog.addIndex('att3', 'KeywordIndex')
        self._catalog.addIndex('num', 'FieldIndex')
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

    def checkResultLength(self):
        upper = self.upper
        a = self._catalog()
        assert len(a) == upper, 'length should be %s, its %s'%(upper, len(a))

    def checkEmptyMappingReturnsAll(self):
        upper = self.upper
        a = self._catalog({})
        assert len(a) == upper, 'length should be %s, its %s'%(upper, len(a))

    def checkFieldIndexLength(self):
        a = self._catalog(att1='att1')
        assert len(a) == self.upper, 'should be %s, but is %s' % (self.upper,
                                                                  len(a))
    def checkTextIndexLength(self):
        a = self._catalog(att2='att2')
        assert len(a) == self.upper, 'should be %s, but is %s' % (self.upper,
                                                                  len(a))

    def checkKeywordIndexLength(self):
        a = self._catalog(att3='att3')
        assert len(a) == self.upper, 'should be %s, but is %s' % (self.upper,
                                                                  len(a))

    def checkUncatalogFieldIndex(self):    
        self.uncatalog()
        a = self._catalog(att1='att1')
        assert len(a) == 0, 'len: %s' % (len(a))
        
    def checkUncatalogTextIndex(self):
        self.uncatalog()
        a = self._catalog(att2='att2')
        assert len(a) == 0, 'len: %s' % (len(a))

    def checkUncatalogKeywordIndex(self):
        self.uncatalog()
        a = self._catalog(att3='att3')
        assert len(a) == 0, 'len: %s'%(len(a))

    def checkBadUncatalog(self):
        try:
            self._catalog.uncatalogObject('asdasdasd')
        except:
            assert 1==2, 'uncatalogObject raised exception on bad uid'

    def checkUniqueValuesForLength(self):
        a = self._catalog.uniqueValuesFor('att1')
        assert len(a) == 1, 'bad number of unique values %s' % str(a)

    def checkUniqueValuesForContent(self):
        a = self._catalog.uniqueValuesFor('att1')
        assert a[0] == 'att1', 'bad content %s' % str(a[0])

    def checkUncatalogTwice(self):
        self._catalog.uncatalogObject(`0`)
        self.assertRaises(Exception, '_second')

    def checkCatalogLength(self):
        for x in range(0, self.upper):
            self._catalog.uncatalogObject(`x`)
        assert len(self._catalog) == 0

    def _second(self):
        self._catalog.uncatalogObject(`0`)

    def uncatalog(self):
        for x in range(0, self.upper):
            self._catalog.uncatalogObject(`x`)

    def checkGoodSortIndex(self):
        upper = self.upper
        a = self._catalog(sort_on='num')
        assert len(a) == upper, 'length should be %s, its %s'%(upper, len(a))
        for x in range(self.upper):
            assert a[x].num == x, x
            
    def checkBadSortIndex(self):
        self.assertRaises(CatalogError, self.badsortindex)

    def badsortindex(self):
        a = self._catalog(sort_on='foofaraw')

    def checkWrongKindOfIndexForSort(self):
        self.assertRaises(CatalogError, self.wrongsortindex)

    def wrongsortindex(self):
        a = self._catalog(sort_on='att2')

    def checkTextIndexQWithSortOn(self):
        upper = self.upper
        a = self._catalog(sort_on='num', att2='att2')
        assert len(a) == upper, 'length should be %s, its %s'%(upper, len(a))
        for x in range(self.upper):
            assert a[x].num == x, x

    def checkTextIndexQWithoutSortOn(self):
        upper = self.upper
        a = self._catalog(att2='att2')
        assert len(a) == upper, 'length should be %s, its %s'%(upper, len(a))
        for x in range(self.upper):
            assert a[x].data_record_score_ == 1, a[x].data_record_score_

    def checkKeywordIndexWithMinRange(self):
        a = self._catalog(att3='att', att3_usage='range:min')
        assert len(a) == self.upper

    def checkKeywordIndexWithMaxRange(self):
        a = self._catalog(att3='att35', att3_usage='range:max')
        assert len(a) == self.upper

    def checkKeywordIndexWithMinMaxRangeCorrectSyntax(self):
        a = self._catalog(att3=['att', 'att35'], att3_usage='range:min:max')
        assert len(a) == self.upper

    def checkKeywordIndexWithMinMaxRangeWrongSyntax(self):
        "checkKeywordIndex with min/max range wrong syntax - known to fail"
        a = self._catalog(att3=['att'], att3_usage='range:min:max')
        assert len(a) == self.upper

    def checkCombinedTextandKeywordQuery(self):
        a = self._catalog(att3='att3', att2='att2')
        assert len(a) == self.upper

class objRS(ExtensionClass.Base):

    def __init__(self,num):
        self.number = num

class testRS(unittest.TestCase):

    def setUp(self):
        self._vocabulary = Vocabulary.Vocabulary('Vocabulary','Vocabulary', globbing=1)
        self._catalog    = Catalog.Catalog()
        self._catalog.addIndex('number',  'FieldIndex')
        self._catalog.addColumn('number')

        for i in range(50000): 
            if i%1000==0: print i
            obj = objRS(whrandom.randint(0,20000))
            self._catalog.catalogObject(obj,i)
           
        self._catalog.aq_parent = objRS(200)

    def testRangeSearch(self):
        for i in range(1000000): 

            m = whrandom.randint(0,20000) 
            n = m + 1000

            for r  in self._catalog.searchResults( {"number" : (m,n) ,
                                                    "length_usage" : "range:min:max" } 
                                            ):
                size = r.number
                assert m<=size and size<=n , "%d vs [%d,%d]" % (r.number,m,n)





def usage(program):
    print "Usage: "
    print
    print "initalize the test catalog:   %s -i -f <maximum number files to use> " % program
    print "to run the basic tests:       %s -b -f <maximum number files to use> " % program
    print "to run the advanced tests:    %s -a -f <maximum number files to use> " % program
                

def main():

    global dataDir,maxFiles

    opts,args = getopt.getopt(sys.argv[1:],"hiabf:xp",['help'])
    opts.sort()

    optsLst = map(lambda x: x[0],opts)

    if optsLst==[]: usage(os.path.basename(sys.argv[0])); sys.exit(0)
    
    for k,v in opts:
        if k in ['-h','--help'] : usage(os.path.basename(sys.argv[0])); sys.exit(0)
        if k == "-f":   maxFiles    = string.atoi(v)

    dataDir = os.path.join("data",str(maxFiles))

    if '-i' in optsLst:
        unittest.TextTestRunner().run(get_tests('init'))

            
    if '-b' in optsLst:
        unittest.TextTestRunner().run(get_tests('bench1'))


    if '-a' in optsLst:
        unittest.TextTestRunner().run(get_tests('bench2'))


    if '-x' in optsLst:
        unittest.TextTestRunner().run(get_tests('exp'))



    if '-p' in optsLst:
        unittest.TextTestRunner().run(test_suite())

def test_suite():

    return get_tests('basic')


def get_tests(what):
    global dataDir,maxFiles

    if what=='basic':
        maxFiles = 100
        dataDir = 'data/%d' % maxFiles

    ts_cm= (
         unittest.makeSuite(TestAddDelIndexes,  'check'),
         unittest.makeSuite(TestCatalogObject,  'check'),
         unittest.makeSuite(TestAddDelColumn,   'check'),
         unittest.makeSuite(TestZCatalogObject, 'check')
    )

    t_aj = (
         BuildEnv('buildTestEnvironment',dataDir,maxFiles),
         testSearches("testFulltextIndex",numThreads=1),
         testSearches("testFieldIndex",numThreads= 1),
         testSearches("testFieldRangeIndex",numThreads=1),
         testSearches("testKeywordIndex",numThreads= 1),
         testSearches("testKeywordRangeIndex",numThreads= 1)
    )

    bench1_tests = (
         testSearches("testFulltextIndex",numThreads=1),
         testSearches("testFulltextIndex",numThreads= 4),
         testSearches("testFieldIndex",numThreads= 1),
         testSearches("testFieldIndex",numThreads= 4),
         testSearches("testFieldRangeIndex",numThreads=1),
         testSearches("testFieldRangeIndex",numThreads= 4),
         testSearches("testKeywordIndex",numThreads= 1),
         testSearches("testKeywordIndex",numThreads= 4),
         testSearches("testKeywordRangeIndex",numThreads= 1),
         testSearches("testKeywordRangeIndex",numThreads=4)
    )

    bench2_tests = (
#       testSearches("testReindexing",numThreads=1),
#        testSearches("testIncrementalIndexing",numThreads=1),
        testSearches("testUpdates",numThreads=2,numUpdates=200),
#        testSearches("testUpdates",numThreads=4,numUpdates=200)
    )

    exp_tests = (
#        testRS("testRangeSearch"),
#       testSearches("testReindexing",numThreads=1),
         testSearches("testReindexingAndModify",numThreads=1),
#        testSearches("testUpdates",numThreads=10,numUpdates=100),
    )
            
    init_tests = ( 
        BuildEnv("buildTestEnvironment",dataDir,maxFiles) ,
    )

    if what=='basic':    
        ts = unittest.TestSuite(ts_cm)
#        for x in t_aj: ts.addTest(x)
        return ts

    else:
        ts = unittest.TestSuite()
        for x in eval('%s_tests' % what): ts.addTest(x)
        return ts

    return



def pdebug():
    import pdb
    test_suite()

def debug():
   test_suite().debug()
 
def pdebug():
    import pdb
    pdb.run('debug()')


if __name__ == '__main__':
       main()

