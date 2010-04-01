##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################

import os, sys, unittest

from DocumentTemplate.sequence.SortEx import *
from DocumentTemplate.sequence.tests.ztestlib import *
from DocumentTemplate.sequence.tests.results import *


class TestCase( unittest.TestCase ):
    """
        Test SortEx .
    """

    def setUp( self ):
        """
        """

    def tearDown( self ):
        """
        """

    def test1( self ):
        "test1"
        assert res1==SortEx(wordlist)

    def test2( self ):
        "test2"
        assert res2==SortEx(wordlist, (("key",),), mapping=1)

    def test3( self ):
        "test3"
        assert res3==SortEx(wordlist, (("key", "cmp"),), mapping=1)

    def test4( self ):
        "test4"
        assert res4==SortEx(wordlist, (("key", "cmp", "desc"),), mapping=1)

    def test5( self ):
        "test5"
        assert res5==SortEx(wordlist, (("weight",), ("key",)), mapping=1)

    def test6( self ):
        "test6"
        assert res6==SortEx(wordlist, (("weight",), ("key", "nocase", "desc")), mapping=1)


    def test7(self):
        "test7"

        def myCmp(s1, s2):
            return -cmp(s1, s2)

        # Create namespace...
        from DocumentTemplate.DT_Util import TemplateDict
        md = TemplateDict()

        #... and push out function onto the namespace
        md._push({"myCmp" : myCmp})

        assert res7==SortEx( wordlist
                           , ( ("weight",)
                             , ("key", "myCmp", "desc")
                             )
                           , md
                           , mapping=1
                           )

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest( unittest.makeSuite( TestCase ) )
    return suite

def main():
    unittest.TextTestRunner().run(test_suite())

if __name__ == '__main__':
    main()
