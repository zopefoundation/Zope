import os,sys,unittest
execfile(os.path.join(sys.path[0],'framework.py'))

from UnicodeSplitter import UnicodeSplitter

class UnicodeSplitterTests(unittest.TestCase):

    def setUp(self):

        texts = ('The quick brown fox jumps over the lazy dog',
                 'Bei den dreitägigen Angriffen seien auch bis auf einen alle Flugplätze der Taliban zerstört worden',
            )

        self.testdata = []

        for t in texts:
            uniLst = [unicode(x,'latin1') for x in t.lower().split(' ')]
            self.testdata.append( (t, uniLst) )


    def testSimpleSplit(self):
        """ testing splitter functionality """ 

        for t,expected in self.testdata:
            fields = list(UnicodeSplitter(t))
            assert fields == expected, "%s vs %s" % (fields,expected)

        return 0


    def testStopwords(self):
        """ testing splitter with stopwords """

        text = 'The quick brown fox jumps over the lazy dog'
        expected = [ u'quick',u'brown',u'fox',u'jumps',u'over',u'lazy',u'fox']
        sw_dict = {'the':None,'dog':'fox'}

        fields = list(UnicodeSplitter(text,sw_dict))
        if fields != expected:
            for i in range(min(len(fields),len(expected))):
                print fields[i],expected[i]
            
            raise AssertionError
        

framework()
