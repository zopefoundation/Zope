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
"""Document Template Tests
"""
import unittest

class force_str:
    # A class whose string representation is not always a plain string:
    def __init__(self,s):
        self.s = s
    def __str__(self):
        return self.s

class DTMLUnicodeTests (unittest.TestCase):

    def _get_doc_class(self):
        from DocumentTemplate.DT_HTML import HTML
        return HTML
    doc_class = property(_get_doc_class,)

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

    def testSize(self):
        html=self.doc_class('<dtml-var "_.unichr(200)*4" size=2>')
        expected = unichr(200)*2+'...'
        res = html()
        assert res == expected, `res`

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest( unittest.makeSuite( DTMLUnicodeTests ) )
    return suite
