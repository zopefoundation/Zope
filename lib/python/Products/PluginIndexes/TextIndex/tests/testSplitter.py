# -*- coding: ISO-8859-1 -*-
##############################################################################
#
# Copyright (c) 2002 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################

import os,sys

import unittest,locale
from Products.PluginIndexes.TextIndex import Splitter


class TestCase( unittest.TestCase ):
    """
        Test our Splitters
    """

    def setUp( self ):
        self.testdata = (
        ('The quick brown fox jumps over the lazy dog',
          ['the','quick','brown','fox','jumps','over','the','lazy','dog']),
        (  'öfters   Österreichische   herüber   Überfall   daß   Ärger   verärgert',
          ['öfters','österreichische','herüber','überfall','daß','ärger','verärgert'])
        )


        pass

    def tearDown( self ):
        """
        """


    def testAvailableSplitters( self ):
        "Test available splitters"

        assert len(Splitter.availableSplitters) >0
        assert len(Splitter.splitterNames)>0
        assert len(Splitter.availableSplitters)==len(Splitter.splitterNames)



    def _test(self,sp_name,text,splitted):

        splitter = Splitter.getSplitter(sp_name)
        result = list(splitter(text))

        assert result==splitted, "%s: %s vs %s" % (sp_name,result,splitted)


#    def testZopeSplitter(self):
#        """test ZopeSplitter (this test is known to fail because it does not support ISO stuff) """
#
#        for text,splitted in self.testdata:
#            self._test("ZopeSplitter",text,splitted)

    def testISOSplitter(self):
        """test ISOSplitter"""
        for text,splitted in self.testdata:
            self._test("ISO_8859_1_Splitter",text,splitted)



def test_suite():
    return unittest.makeSuite( TestCase )

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
