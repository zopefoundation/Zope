# -*- coding: ISO-8859-1 -*-
##############################################################################
#
# Copyright (c) 2001 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################

import os,sys,unittest
from Products.PluginIndexes.TextIndex.Splitter.UnicodeSplitter.UnicodeSplitter \
     import UnicodeSplitter

class UnicodeSplitterTests(unittest.TestCase):

    def setUp(self):

        texts = ('The quick brown fox jumps over the lazy dog',
                 'Bei den dreitägigen Angriffen seien auch bis'
                 ' auf einen alle Flugplätze der Taliban zerstört worden',
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

        text = 'The quick brown fox jumps over The lazy dog'
        expected = [ u'quick',u'brown',u'fox',u'jumps',u'over',u'lazy',u'cat']
        sw_dict = {'the':None,'dog':'cat'}

        splitter = UnicodeSplitter(text,sw_dict)
        fields = list(splitter)
        self.assertEquals(fields, expected)
        self.assertEquals(splitter.indexes('jumps'), [3])


def test_suite():
    return unittest.makeSuite(UnicodeSplitterTests)

def debug():
    return test_suite().debug()

def pdebug():
    import pdb
    pdb.run('debug()')

def main():
    unittest.TextTestRunner().run( test_suite() )

if __name__ == '__main__':
    if len(sys.argv) > 1:
        globals()[sys.argv[1]]()
    else:
        main()
