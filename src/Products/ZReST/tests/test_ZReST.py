# -*- coding: iso-8859-15 -*-

""" Unit tests for ZReST objects
"""

import unittest
import cgi
import tempfile

txt = """Hello World
============

text text

Von Vögeln und Öfen
===================

- some
- more
- text

"""


csv_text = """bin:x:1:1:bin:/bin:/bin/bash
daemon:x:2:2:Daemon:/sbin:/bin/bash
"""

docutils_include_warning = '(WARNING/2) "include" directive disabled.'
docutils_raw_warning = '(WARNING/2) "raw" directive disabled.'

class TestZReST(unittest.TestCase):

    def _getTargetClass(self):
        from Products.ZReST.ZReST import ZReST
        return ZReST

    def _makeOne(self, id='test', *args, **kw):
        return self._getTargetClass()(id=id, *args, **kw)

    def _csvfile(self):
        fn = tempfile.mktemp()
        open(fn, 'w').write(csv_text)
        return fn

    def test_empty(self):
        empty = self._makeOne()

        # New instances should not have non-volatile cache attributes
        self.assertRaises(AttributeError, lambda: empty.formatted)
        self.assertRaises(AttributeError, lambda: empty.warnings)

        self.assertEqual(empty._v_formatted, None)
        self.assertEqual(empty._v_warnings, None)

    def test_formatted_ignored(self):
        resty = self._makeOne()
        resty.formatted = 'IGNORE ME'

        self.assertFalse('IGNORE ME' in resty.index_html())

    def testConversion(self):
        resty = self._makeOne()
        resty.source = txt
        resty.input_encoding = 'iso-8859-15'
        resty.output_encoding = 'iso-8859-15'
        resty.render()
        html = resty.index_html()

        s = '<h1>Hello World</h1>'
        self.assertEqual(s in html, True)

        s = '<h1>Von Vögeln und Öfen</h1>'
        self.assertEqual(s in html, True)

        # ZReST should render a complete HTML document
        self.assertEqual('<html' in html, True)
        self.assertEqual('<body>' in html, True)

    def test_include_directive_raises(self):
        resty = self._makeOne()
        resty.source = 'hello world\n .. include:: /etc/passwd'
        result = resty.render()
        warnings = ''.join(resty._v_warnings.messages)

        # The include: directive hasn't been rendered, it remains
        # verbatimly in the rendered output.  Instead a warning
        # message is presented:
        self.assert_(docutils_include_warning in warnings)

    def test_raw_directive_disabled(self):
        resty = self._makeOne()
        EXPECTED = '<h1>HELLO WORLD</h1>'
        resty.source = '.. raw:: html\n\n  %s\n' % EXPECTED
        result = resty.render()
        warnings = ''.join(resty._v_warnings.messages)

        # The raw: directive hasn't been rendered, it remains
        # verbatimly in the rendered output.  Instead a warning
        # message is presented:
        self.assert_(EXPECTED not in result)
        self.assert_(cgi.escape(EXPECTED) in result)
        self.assert_(docutils_raw_warning in warnings)

    def test_raw_directive_file_directive_raises(self):
        resty = self._makeOne()
        resty.source = '.. raw:: html\n  :file: inclusion.txt'
        result = resty.render()
        warnings = ''.join(resty._v_warnings.messages)

        # The raw: directive hasn't been rendered, it remains
        # verbatimly in the rendered output.  Instead a warning
        # message is presented:
        self.assert_(docutils_raw_warning in warnings)

    def test_raw_directive_url_directive_raises(self):
        resty = self._makeOne()
        resty.source = '.. raw:: html\n  :url: http://www.zope.org/'
        result = resty.render()
        warnings = ''.join(resty._v_warnings.messages)

        # The raw: directive hasn't been rendered, it remains
        # verbatimly in the rendered output.  Instead a warning
        # message is presented:
        self.assert_(docutils_raw_warning in warnings)

    def test_csv_table_file_option_raise(self):
        resty = self._makeOne()
        csv_file = self._csvfile()
        resty.source = '.. csv-table:: \n  :file: %s' % csv_file
        result = resty.render()
        self.assertTrue('daemon' not in result, 
                        'csv-table/file directive is not disabled!')

    def test_csv_table_url_option_raise(self):
        resty = self._makeOne()
        csv_file = self._csvfile()
        resty.source = '.. csv-table:: \n  :url: file://%s' % csv_file
        result = resty.render()
        self.assertTrue('daemon' not in result, 
                        'csv-table/url directive is not disabled!')


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestZReST))
    return suite
