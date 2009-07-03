#!/usr/bin/env python
# XXX: Products.PluginIndexes.TextIndex and Vocabulary no longer exist

# Regression test for ZCatalog


import os,sys
sys.path.insert(0,'.')

try:
    import Testing
except ImportError:
    sys.path[0] = "../../.."
    import Testing

os.environ['STUPID_LOG_FILE']= "debug.log"

here = os.getcwd()

import Zope2
import ZODB, ZODB.FileStorage
import transaction

from Products.ZCatalog import ZCatalog #,Vocabulary
from Products.ZCatalog.Catalog import CatalogError
import Persistence
import ExtensionClass
from Testing import dispatcher
import keywords


import getopt,random,time,string,mailbox,rfc822
import unittest_patched as unittest

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
        transaction.commit()


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

#        self._vocabulary = Vocabulary.Vocabulary('Vocabulary',
#                            'Vocabulary', globbing=1)
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

        self.zodb               = testZODB("data/work/Data.fs",open=0)
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
            m = random.randint(0,10000)
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
            m = random.randint(0,10000)
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

        rdgen = random.Random()

        env = self.th_setup()

        for i in range(len(keys)):

            r = rdgen.randint(0,len(msgs)-1)

            mid = keys[r]
            obj = msgs[mid]

            try:
                cat.uncatalog_object(mid)

                if kw.get("commit",1)==1:
                    transaction.commit()
                    time.sleep(0.1)
            except ZODB.POSException.ConflictError:
                uncat_conflicts = uncat_conflicts + 1

            try:
                cat.catalog_object(obj,mid)

                if kw.get("commit",1)==1:
                    transaction.commit()
                    time.sleep(0.1)

            except ZODB.POSException.ConflictError:
                cat_conflicts = cat_conflicts + 1

        try:
            transaction.commit()
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
                transaction.commit()
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
        cat         = root["catalog"]._catalog
        msg_ids     = root['catalog'].msg_ids

        return cat,msg_ids



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
