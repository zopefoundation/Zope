# -*- coding: iso-8859-15 -*-

import unittest
import cgi
from docutils.core import publish_parts
from reStructuredText import HTML, Warnings


txt = """Hello World
============

text text

Von Vögeln und Öfen
===================

- some
- more
- text

"""


docutils_include_warning = '''\
<p class="system-message-title">System Message: WARNING/2 (<tt class="docutils">&lt;string&gt;</tt>, line 2)</p>
<p>&quot;include&quot; directive disabled.</p>'''

docutils_raw_warning = '''\
<p class="system-message-title">System Message: WARNING/2 (<tt class="docutils">&lt;string&gt;</tt>, line 1)</p>
<p>&quot;raw&quot; directive disabled.</p>'''


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

            expected = '<h%d>Hello World</h%d>' % (level+1, level+1)
            self.assertEqual(expected in html, True)

            expected = '<h%d>Von Vögeln und Öfen</h%d>' % (level+1, level+1)
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

    def test_file_insertion_off_by_default(self):
        directive = '.. include:: /etc/passwd'
        source = 'hello world\n %s' % directive
        parts = publish_parts(source=source, writer_name='html4css1',
                              settings_overrides={'warning_stream': Warnings()})

        # The include: directive hasn't been rendered, it remains
        # verbatimly in the rendered output.  Instead a warning
        # message is presented:
        self.assert_(directive in parts['body'])
        self.assert_(docutils_include_warning in parts['body'])

    def test_include_directive_raises(self):
        directive = '.. include:: /etc/passwd'
        source = 'hello world\n %s' % directive
        result = HTML(source)

        # The include: directive hasn't been rendered, it remains
        # verbatimly in the rendered output.  Instead a warning
        # message is presented:
        self.assert_(directive in result)
        self.assert_(docutils_include_warning in result)

    def test_raw_directive_disabled(self):
        EXPECTED = '<h1>HELLO WORLD</h1>'
        source = '.. raw:: html\n\n  %s\n' % EXPECTED
        result = HTML(source)       # don't raise, but don't work either

        # The raw: directive hasn't been rendered, it remains
        # verbatimly in the rendered output.  Instead a warning
        # message is presented:
        self.assert_(EXPECTED not in result)
        self.assert_(cgi.escape(EXPECTED) in result)
        self.assert_(docutils_raw_warning in result)

    def test_raw_directive_file_option_raises(self):
        source = '.. raw:: html\n  :file: inclusion.txt'
        result = HTML(source)

        # The raw: directive hasn't been rendered, it remains
        # verbatimly in the rendered output.  Instead a warning
        # message is presented:
        self.assert_(source in result)
        self.assert_(docutils_raw_warning in result)

    def test_raw_directive_url_option_raises(self):
        source = '.. raw:: html\n  :url: http://www.zope.org'
        result = HTML(source)

        # The raw: directive hasn't been rendered, it remains
        # verbatimly in the rendered output.  Instead a warning
        # message is presented:
        self.assert_(source in result)
        self.assert_(docutils_raw_warning in result)

    def test_csv_table_file_option_raise(self):
        source = '.. csv-table:: \n  :file: inclusion.txt'
        result = HTML(source)
        self.assertTrue('File and URL access deactivated' in result)

    def test_csv_table_url_option_raise(self):
        source = '.. csv-table:: \n  :url: http://www.evil.org'
        result = HTML(source)
        self.assertTrue('File and URL access deactivated' in result)


def test_suite():
    from unittest import TestSuite, makeSuite
    return TestSuite((makeSuite(TestReST),))

