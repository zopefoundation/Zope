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

from StructuredText import ST
from StructuredText import DocumentClass
from StructuredText import ClassicDocumentClass
from StructuredText import StructuredText
from StructuredText import HTMLClass
from StructuredText.StructuredText import HTML
import sys, os, unittest, cStringIO
from OFS import ndiff

"""
This tester first ensures that all regression files
can at least parse all files.
Secondly, the tester will compare the output between
StructuredText and ClassicDocumentClass->HTMLClass
to help ensure backwards compatability.
"""

package_dir = os.path.split(ST.__file__)[0]
regressions=os.path.join(package_dir, 'regressions')

files = ['index.stx','Acquisition.stx','ExtensionClass.stx',
        'MultiMapping.stx','examples.stx','Links.stx','examples1.stx',
        'table.stx','InnerLinks.stx']

def readFile(dirname,fname):

    myfile  = open(os.path.join(dirname, fname),"r")
    lines   = myfile.readlines()
    myfile.close()
    return  ''.join(lines)


class StructuredTextTests(unittest.TestCase):

    def testStructuredText(self):
        """ testing StructuredText """

        for f in files:
            raw_text = readFile(regressions,f)
            assert StructuredText.StructuredText(raw_text),\
                'StructuredText failed on %s' % f

    def testStructuredTextNG(self):
        """ testing StructuredTextNG """

        for f in files:
            raw_text = readFile(regressions,f)
            assert ST.StructuredText(raw_text),\
                'StructuredText failed on %s' % f


    def testDocumentClass(self):
        """ testing DocumentClass"""

        for f in files:
            Doc = DocumentClass.DocumentClass()
            raw_text = readFile(regressions,f)
            text = ST.StructuredText(raw_text)
            assert Doc(text),\
                'DocumentClass failed on %s' % f

    def testClassicDocumentClass(self):
        """ testing ClassicDocumentClass"""

        for f in files:
            Doc = ClassicDocumentClass.DocumentClass()
            raw_text = readFile(regressions,f)
            text = ST.StructuredText(raw_text)
            assert Doc(text),\
                'ClassicDocumentClass failed on %s' % f

    def testClassicHTMLDocumentClass(self):
        """ testing HTML ClassicDocumentClass"""

        for f in files:
            Doc = ClassicDocumentClass.DocumentClass()
            HTML = HTMLClass.HTMLClass()
            raw_text = readFile(regressions,f)
            text = Doc(ST.StructuredText(raw_text))
            assert HTML(text),\
                'HTML ClassicDocumentClass failed on %s' % f


    def testRegressionsTests(self):
        """ HTML regression test """

        for f in files:
            Doc  = DocumentClass.DocumentClass()
            HTML = HTMLClass.HTMLClass()
            raw_text = readFile(regressions,f)
            text = Doc(ST.StructuredText(raw_text))
            html = HTML(text)

            reg_fname = f.replace('.stx','.ref')
            reg_html  = readFile(regressions , reg_fname)

            if reg_html.strip()!= html.strip():

                IO = cStringIO.StringIO()

                oldStdout = sys.stdout
                sys.stdout = IO

                try:
                    open('_tmpout','w').write(html)
                    ndiff.fcompare(os.path.join(regressions,reg_fname),
                                   '_tmpout')
                    os.unlink('_tmpout')
                finally:
                    sys.stdout = oldStdout

                raise AssertionError, \
                    'HTML regression test failed on %s\nDiff:\n%s\n' % (f,
                     IO.getvalue())


class BasicTests(unittest.TestCase):

    def _test(self,stxtxt , expected):

        res = HTML(stxtxt,level=1,header=0)
        if res.find(expected)==-1:
            print "Text:     ",stxtxt
            print "Converted:",res
            print "Expected: ",expected
            raise AssertionError,"basic test failed for '%s'" % stxtxt


    def testUnderline(self):
        self._test("xx _this is html_ xx",
                   "xx <u>this is html</u> xx")

    def testUnderline1(self):
        self._test("xx _this is html_",
                   "<u>this is html</u>")

    def testEmphasis(self):
        self._test("xx *this is html* xx",
                   "xx <em>this is html</em> xx")

    def testStrong(self):
        self._test("xx **this is html** xx",
                   "xx <strong>this is html</strong> xx")

    def testUnderlineThroughoutTags(self):
        self._test('<a href="index_html">index_html</a>',
                   '<a href="index_html">index_html</a>')


    def testUnderscoresInLiteral1(self):

        self._test("def __init__(self)",
                   "def __init__(self)")

    def testUnderscoresInLiteral2(self):

        self._test("this is '__a_literal__' eh",
                   "<code>__a_literal__</code>")


    def testUnderlinesWithoutWithspaces(self):

        self._test("Zopes structured_text is sometimes a night_mare",
                   "Zopes structured_text is sometimes a night_mare")


    def testAsterisksInLiteral(self):
        self._test("this is a '*literal*' eh",
        "<code>*literal*</code>")


    def testDoubleAsterisksInLiteral(self):
        self._test("this is a '**literal**' eh",
        "<code>**literal**</code>")


    def testLinkInLiteral(self):
        self._test("this is a '\"literal\":http://www.zope.org/.' eh",
        '<code>"literal":http://www.zope.org/.</code>')


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest( unittest.makeSuite( StructuredTextTests ) )
    suite.addTest( unittest.makeSuite( BasicTests ) )
    return suite

def main():
    unittest.TextTestRunner().run(test_suite())

if __name__ == '__main__':
    main()
