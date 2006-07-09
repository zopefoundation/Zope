# -*- coding: iso-8859-15 -*-

import unittest

from reStructuredText import HTML


txt = """Hello World
============

text text

Von Vögeln und Öfen
===================

- some
- more
- text

"""


class TestReST(unittest.TestCase):

    def testRoman(self):
        # Make sure we can import the rst parser
        from docutils.parsers import rst

    def testEncodings(self):

        def _test(txt, in_enc, out_enc):
            return HTML(txt,
                        input_encoding=in_enc,
                        output_encoding=out_enc)

        encoding = 'iso-8859-15'
        html = _test(txt, encoding, encoding)
        self.assertEqual('Vögel' in html, True)
        self.assertEqual('Öfen' in html, True)

        html = _test(txt, encoding, 'unicode')
        self.assertEqual(unicode('Vögel', encoding) in html, True)
        self.assertEqual(unicode('Öfen', encoding) in html, True)

        html = _test(unicode(txt, encoding), 'unicode', encoding)
        self.assertEqual('Vögel' in html, True)
        self.assertEqual('Öfen' in html, True)

        html = _test(unicode(txt, encoding), 'unicode', 'unicode')
        self.assertEqual(unicode('Vögel', encoding) in html, True)
        self.assertEqual(unicode('Öfen', encoding) in html, True)

    def testHeaderLevel(self):

        encoding = 'iso-8859-15'
        for level in range(0, 5):
            html = HTML(txt, input_encoding=encoding, 
                             output_encoding=encoding, 
                             initial_header_level=level)

            expected = '<h%d><a id="hello-world" name="hello-world">Hello World</a></h%d>' %\
                        (level+1, level+1) 
            self.assertEqual(expected in html, True)

            expected = '<h%d><a id="von-v-geln-und-fen" name="von-v-geln-und-fen">Von Vögeln und Öfen</a></h%d>' %\
                        (level+1, level+1) 
            self.assertEqual(expected in html, True)

    def testWithSingleSubtitle(self):
        input = '''
title
-----
subtitle
++++++++
text
'''
        expected='''<h3 class="title">title</h3>
<h4 class="subtitle">subtitle</h4>
<p>text</p>
'''
        output = HTML(input)
        self.assertEquals(output, expected) 


    def testFileInclusion(self):
        source = 'hello world\n .. include:: /etc/passwd'
        self.assertRaises(NotImplementedError, HTML, source)


    def testRawPassthrough(self):

        source = '.. raw:: html\n  <h1>HELLO WORLD</h1>'
        result = HTML(source)       # don't raise

        source = '.. raw:: html\n  :file: inclusion.txt'
        self.assertRaises(NotImplementedError, HTML, source)

        source = '.. raw:: html\n  :url: http://www.zope.org'
        self.assertRaises(NotImplementedError, HTML, source)

def test_suite():
    from unittest import TestSuite, makeSuite
    return TestSuite((makeSuite(TestReST),))

