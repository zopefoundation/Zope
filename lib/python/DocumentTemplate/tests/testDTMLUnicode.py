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
"""Document Template Tests
"""

__rcs_id__='$Id: testDTMLUnicode.py,v 1.2 2002/03/27 10:14:02 htrd Exp $'
__version__='$Revision: 1.2 $'[11:-2]

import sys, os
import unittest

from DocumentTemplate.DT_HTML import HTML, String
from ExtensionClass import Base

class force_str:
    # A class whose string representation is not always a plain string:
    def __init__(self,s):
        self.s = s
    def __str__(self):
        return self.s

class DTMLUnicodeTests (unittest.TestCase):

    doc_class = HTML

    def testAA(self):
        html=self.doc_class('<dtml-var a><dtml-var b>')
        expected = 'helloworld'
        res = html(a='hello',b='world')
        assert res == expected, `res`

    def testUU(self):
        html=self.doc_class('<dtml-var a><dtml-var b>')
        expected = u'helloworld'
        res = html(a=u'hello',b=u'world')
        assert res == expected, `res`

    def testAU(self):
        html=self.doc_class('<dtml-var a><dtml-var b>')
        expected = u'helloworld'
        res = html(a='hello',b=u'world')
        assert res == expected, `res`

    def testAB(self):
        html=self.doc_class('<dtml-var a><dtml-var b>')
        expected = 'hello\xc8'
        res = html(a='hello',b=chr(200))
        assert res == expected, `res`

    def testUB(self):
        html=self.doc_class('<dtml-var a><dtml-var b>')
        expected = u'hello\xc8'
        res = html(a=u'hello',b=chr(200))
        assert res == expected, `res`

    def testUB2(self):
        html=self.doc_class('<dtml-var a><dtml-var b>')
        expected = u'\u07d0\xc8'
        res = html(a=unichr(2000),b=chr(200))
        assert res == expected, `res`

    def testUnicodeStr(self):
        html=self.doc_class('<dtml-var a><dtml-var b>')
        expected = u'\u07d0\xc8'
        res = html(a=force_str(unichr(2000)),b=chr(200))
        assert res == expected, `res`

    def testUqB(self):
        html=self.doc_class('<dtml-var a html_quote><dtml-var b>')
        expected = u'he&gt;llo\xc8'
        res = html(a=u'he>llo',b=chr(200))
        assert res == expected, `res`

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest( unittest.makeSuite( DTMLUnicodeTests ) )
    return suite

def main():
    unittest.TextTestRunner().run(test_suite())

if __name__ == '__main__':
    main()
