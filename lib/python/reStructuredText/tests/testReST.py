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


    def test_include_directive_raises(self):
        source = 'hello world\n .. include:: /etc/passwd'
        self.assertRaises(NotImplementedError, HTML, source)

    def test_raw_directive_disabled(self):

        EXPECTED = '<h1>HELLO WORLD</h1>'

        source = '.. raw:: html\n\n  %s\n' % EXPECTED
        result = HTML(source)       # don't raise, but don't work either
        self.failIf(EXPECTED in result)

        self.failUnless("&quot;raw&quot; directive disabled" in result)
        from cgi import escape
        self.failUnless(escape(EXPECTED) in result)

    def test_raw_directive_file_option_raises(self):

        source = '.. raw:: html\n  :file: inclusion.txt'
        self.assertRaises(NotImplementedError, HTML, source)

    def test_raw_directive_url_option_raises(self):

        source = '.. raw:: html\n  :url: http://www.zope.org'
        self.assertRaises(NotImplementedError, HTML, source)


    def test_csv_table_file_option_raise(self):

        source = '.. csv-table:: \n  :file: inclusion.txt'
        result = HTML(source)
        self.failUnless('File and URL access deactivated' in result)

    def test_csv_table_file_option_raise(self):

        source = '.. csv-table:: \n  :url: http://www.evil.org'
        result = HTML(source)
        self.failUnless('File and URL access deactivated' in result)


def test_suite():
    from unittest import TestSuite, makeSuite
    return TestSuite((makeSuite(TestReST),))

