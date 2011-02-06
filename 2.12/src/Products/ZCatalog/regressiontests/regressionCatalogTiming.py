# XXX: Products.PluginIndexes.TextIndex no longer exists
import os, sys
sys.path.insert(0, '.')
try:
    import Testing
    os.environ['SOFTWARE_HOME']=os.environ.get('SOFTWARE_HOME', '.')
except ImportError:
    sys.path[0]='../../..'
    import Testing
    os.environ['SOFTWARE_HOME']='../../..'

os.environ['INSTANCE_HOME']=os.environ.get(
    'INSTANCE_HOME',
    os.path.join(os.environ['SOFTWARE_HOME'],'..','..')
    )

os.environ['STUPID_LOG_FILE']=os.path.join(os.environ['INSTANCE_HOME'],'var',
                                           'debug.log')
here = os.getcwd()

import Zope2
import mailbox, time, httplib
from string import strip, find, split, lower, atoi, join
from urllib import quote
from Products.ZCatalog import ZCatalog
from unittest import TestCase, TestSuite, JUnitTextTestRunner,\
     VerboseTextTestRunner, makeSuite

import transaction

from Products.PluginIndexes.FieldIndex.FieldIndex import FieldIndex
#from Products.PluginIndexes.TextIndex.TextIndex import TextIndex
#from Products.PluginIndexes.TextIndex.Lexicon import  Lexicon
from Products.PluginIndexes.KeywordIndex.KeywordIndex import KeywordIndex

from Testing.makerequest import makerequest

TextTestRunner = VerboseTextTestRunner

class TestTimeIndex(TestCase):
    def setUp(self):
        self.app = makerequest(Zope2.app())
        try: self.app._delObject('catalogtest')
        except AttributeError: pass
        self.app.manage_addFolder('catalogtest')
        zcatalog = ZCatalog.ZCatalog('catalog', 'a catalog')
        self.app.catalogtest._setObject('catalog', zcatalog)
        c = self.app.catalogtest.catalog
        for x in ('title', 'to', 'from', 'date', 'raw'):
            try: c.manage_delIndex([x])
            except: pass
        c.manage_addIndex('title', 'TextIndex')
        c.manage_addIndex('to', 'TextIndex')
        c.manage_addIndex('from', 'TextIndex')
        c.manage_addIndex('date', 'FieldIndex')
        c.manage_addIndex('raw', 'TextIndex')

    def tearDown(self):
        try: self.app._delObject('catalogtest')
        except AttributeError: pass
        try:
            self.app._p_jar._db.pack()
            self.app._p_jar.close()
        except AttributeError: pass
        self.app = None
        del self.app

    def checkTimeBulkIndex(self):
        print
        c = self.app.catalogtest.catalog
        t = time.time()
        loadmail(self.app.catalogtest, 'zopemail',
                 os.path.join(here, 'zope.mbox'), 500)
        transaction.commit()
        loadtime = time.time() - t
        out("loading data took %s seconds.. " % loadtime)
        t = time.time()
        req = self.app.REQUEST
        parents = [self.app.catalogtest.catalog,
                   self.app.catalogtest, self.app]
        req['PARENTS'] = parents
        rsp = self.app.REQUEST.RESPONSE
        url1 = ''
        c.manage_catalogFoundItems(req, rsp, url1, url1,
                                   obj_metatypes=['DTML Document'])
        indextime = time.time() - t
        out("bulk index took %s seconds.. " % indextime)
        out("total time for load and index was %s seconds.. "
            % (loadtime + indextime))

    def checkTimeIncrementalIndexAndQuery(self):
        print
        c = self.app.catalogtest.catalog
        t = time.time()
        max = 500
        m = loadmail(self.app.catalogtest, 'zopemail',
                     os.path.join(here, 'zope.mbox'), max, c)
        transaction.commit()
        total = time.time() - t
        out("total time for load and index was %s seconds.. " % total)
        t = time.time()
        rs = c() # empty query should return all
        assert len(rs) == max, len(rs)
        dates = m['date']
        froms = m['from']
        tos =m['to']
        titles = m['title']
        assert len(c({'date':'foobarfoo'})) == 0 # should return no results
        for x in dates:
            assert len(c({'date':x})) == 1 # each date should be fieldindexed
        assert len(c({'from':'a'})) == 0 # should be caught by splitter
        assert len(c({'raw':'chris'})) != 0
        assert len(c({'raw':'gghdjkasjdsda'})) == 0
        assert c({'PrincipiaSearchSource':'the*'})

    def checkTimeSubcommit(self):
        print
        for x in (None,100,500,1000,10000):
            out("testing subcommit at theshhold of %s" % x)
            if x is not None:
                self.setUp()
            c = self.app.catalogtest.catalog
            c.threshold = x
            transaction.commit()
            t = time.time()
            loadmail(self.app.catalogtest, 'zopemail',
                     os.path.join(here, 'zope.mbox'), 500, c)
            transaction.commit()
            total = time.time() - t
            out("total time with subcommit thresh %s was %s seconds.. "
                % (x,total))
            self.tearDown()


# utility

def loadmail(folder, name, mbox, max=None, catalog=None):
    """
    creates a folder inside object 'folder' named 'name', opens
    filename 'mbox' and adds 'max' mail messages as DTML documents to
    the ZODB inside the folder named 'name'.  If 'catalog' (which
    should be a ZCatalog object) is passed in, call catalog_object on it
    with the document while we're iterating.  If 'max' is not None,
    only do 'max' messages, else do all messages in the mbox archive.
    """
    m = {'date':[],'from':[],'to':[],'title':[]}
    folder.manage_addFolder(name)
    folder=getattr(folder, name)
    mb=mailbox.UnixMailbox(open(mbox))
    i=0
    every=100
    message=mb.next()
    while message:
        part = `i/every * 100`
        try:
            dest = getattr(folder, part)
        except AttributeError:
            folder.manage_addFolder(part)
            dest = getattr(folder, part)
        dest.manage_addDTMLDocument(str(i), file=message.fp.read())
        doc=getattr(dest, str(i))
        i=i+1
        for h in message.headers:
            h=strip(h)
            l=find(h,':')
            if l <= 0: continue
            name=lower(h[:l])
            if name=='subject': name='title'
            h=strip(h[l+1:])
            type='string'
            if 0 and name=='date': type='date'
            elif 0:
                try: atoi(h)
                except: pass
                else: type=int
            if name=='title':
                doc.manage_changeProperties(title=h)
                m[name].append(h)
            elif name in ('to', 'from', 'date'):
                try: doc.manage_addProperty(name, h, type)
                except: pass
                m[name].append(h)
        if catalog:
            path = join(doc.getPhysicalPath(), '/')
            catalog.catalog_object(doc, path)
        if max is not None:
            if i >= max: break
        message=mb.next()
    return m

def out(s):
    print "   %s" % s

def test_suite():
    s1 = makeSuite(TestTimeIndex, 'check')

    testsuite = TestSuite((s1,))
    return testsuite

def main():
    mb = os.path.join(here, 'zope.mbox')
    if not os.path.isfile(mb):
        print "do you want to get the zope.mbox file from lists.zope.org?"
        print "it's required for testing (98MB, ~ 30mins on fast conn)"
        print "it's also available at korak:/home/chrism/zope.mbox"
        print "-- type 'Y' or 'N'"
        a = raw_input()
        if lower(a[:1]) == 'y':
            server = 'lists.zope.org:80'
            method = '/pipermail/zope.mbox/zope.mbox'
            h = httplib.HTTP(server)
            h.putrequest('GET', method)
            h.putheader('User-Agent', 'silly')
            h.putheader('Accept', 'text/html')
            h.putheader('Accept', 'text/plain')
            h.putheader('Host', server)
            h.endheaders()
            errcode, errmsg, headers = h.getreply()
            if errcode != 200:
                f = h.getfile()
                data = f.read()
                print data
                class HTTPRequestError(Exception):
                    pass
                raise HTTPRequestError, "Error reading from host %s" % server
            f = h.getfile()
            out=open(mb,'w')
            print "this is going to take a while..."
            print "downloading mbox from %s" % server
            while 1:
                l = f.readline()
                if not l: break
                out.write(l)

    alltests=test_suite()
    runner = TextTestRunner()
    runner.run(alltests)

def debug():
    test_suite().debug()

if __name__=='__main__':
    if len(sys.argv) > 1:
        globals()[sys.argv[1]]()
    else:
        main()
