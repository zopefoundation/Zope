import os,sys
import unittest

import Zope
from Products.ZCatalog.ZCatalog import ZCatalog


from Products.PluginIndexes.TextIndex import Splitter

# This patch pretends the ZCatalog is using the Unicode Splitter
# but by default the ZCatalog/TextIndexes uses the standard
# non-unicode-aware ZopeSplitter

Splitter.availableSplitters =    [ ("UnicodeSplitter" , "Unicode-aware splitter")]
Splitter.splitterNames =    [ "UnicodeSplitter" ]



class TO:

    def __init__(self,txt,kw=''):
        self.text = txt
        self.kw   = kw


class UnicodeTextIndexCatalogTest(unittest.TestCase):

    def setUp(self):

        self.cat = ZCatalog("catalog")
        self.cat.addIndex('text',"TextIndex")
        self.cat.addColumn('text')
        self.cat.addIndex('kw','KeywordIndex')
        self.cat.addColumn('kw')

        t1 = TO('the quick brown fox jumps over the lazy dog',['quick','fox'])
        t2 = TO('i am the nice alien from the future',['alien','future'])
        t3 = TO('i am a brown fox dancing with a future alien',['zerstört','könnten'])
        t4 = TO('i am a brown ' + unicode('fox') + ' dancing with a future alien',[])
        t5 = TO("""
        Die USA und Großbritannien können nach der Zerstörung der
        afghanischen Luftabwehr nun rund um die Uhr Angriffe fliegen. Das gab 
        Verteidigungsminister Donald Rumsfeld bekannt. Bei den dreitägigen Angriffen
        seien auch bis auf einen alle Flugplätze der Taliban zerstört worden. Rumsfeld
        erklärte weiter, er könne die Berichte nicht bestätigen, wonach bei den 
        amerikanischen Angriffen vier afghanische Mitarbeiter einer von den UN
        finanzierten Hilfsorganisation getötet wurden. Diese könnten auch durch
        Gegenfeuer der Taliban getötet worden sein.
        """,[unicode('dreitägigen','latin1')])
                                                                                                            

        self.cat.catalog_object(t1,"o1")
        self.cat.catalog_object(t2,"o2")
        self.cat.catalog_object(t3,"o3")
        self.cat.catalog_object(t4,"o4")
        self.cat.catalog_object(t5,"o5")

        self.tests = [('quick',('o1',)),
              ('fox',('o1','o2','o3','o4')),
              ('afghanischen', ('o5',)),
              ('dreitägigen',('o5',))
            ]

        
        self.kw_tests = [ ('quick',('o1',) ),
                          ('zerstört',('o3',)),
                          ('dreitägigen',('o5',))
                        ]


    def testAsciiQuery(self):
        """ simple query test """

        for q,objs in self.tests:
            res=self.cat.searchResults({'text':{'query':q}})

            for r in res:
                assert r.getURL() in objs,\
                    "%s: %s vs %s" % (q,str(r.getURL()),str(objs)) 


    def testUnicodeQuery(self):
        """ unicode query test """

        for q,objs in self.tests:
            res=self.cat.searchResults({'text':{'query':unicode(q,'latin1')}})

            for r in res:
                assert r.getURL() in objs, \
                    "%s: %s vs %s" % (q,str(r.getURL()),str(objs)) 


    def testAsciiKeywords(self):
        """ test keyword index """

        for q,objs in self.kw_tests:
            res=self.cat.searchResults({'kw':{'query':q}})

            for r in res:
                assert r.getURL() in objs, \
                    "%s: %s vs %s" % (q,str(r.getURL()),str(objs)) 


    def testUnicodeKeywords(self):
        """ test unicode keyword index """

        for q,objs in self.kw_tests:
            res=self.cat.searchResults({'kw':{'query':unicode(q,'latin1')}})

            for r in res:
                assert r.getURL() in objs, \
                    "%s: %s vs %s" % (q,str(r.getURL()),str(objs)) 





def test_suite():
    return unittest.makeSuite(UnicodeTextIndexCatalogTest)
    
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
                raise "Error reading from host %s" % server
            f = h.getfile()
            out=open(mb,'w')
            print "this is going to take a while..."
            print "downloading mbox from %s" % server
            while 1:
                l = f.readline()
                if not l: break
                out.write(l)

    alltests=test_suite()
    runner = unittest.TextTestRunner()
    runner.run(alltests)

def debug():
    test_suite().debug()

if __name__=='__main__':
   if len(sys.argv) > 1:
      globals()[sys.argv[1]]()
   else:
      main()

