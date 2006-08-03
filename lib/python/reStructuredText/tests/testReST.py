import unittest
from reStructuredText import HTML

class TestReST(unittest.TestCase):

    def testRoman(self):
        # Make sure we can import the rst parser
        from docutils.parsers import rst

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
        self.failUnless('directive disabled' in result)

    def test_csv_table_url_option_raise(self):

        source = '.. csv-table:: \n  :url: http://www.evil.org'
        result = HTML(source)
        self.failUnless('directive disabled' in result)

def test_suite():
    from unittest import TestSuite, makeSuite
    return TestSuite((makeSuite(TestReST),))
