""" Unit tests for ZReST objects

$Id$
"""
import unittest
import tempfile


csv_text = """bin:x:1:1:bin:/bin:/bin/bash
daemon:x:2:2:Daemon:/sbin:/bin/bash
"""

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

        self.failIf('IGNORE ME' in resty.index_html())

    def test_include_directive_raises(self):
        resty = self._makeOne()
        resty.source = 'hello world\n .. include:: /etc/passwd'
        self.assertRaises(NotImplementedError, resty.render)

    def test_raw_directive_disabled(self):

        EXPECTED = '<h1>HELLO WORLD</h1>'

        resty = self._makeOne()
        resty.source = '.. raw:: html\n\n  %s\n' % EXPECTED
        result = resty.render() # don't raise, but don't work either
        self.failIf(EXPECTED in result)

        self.failUnless("&quot;raw&quot; directive disabled" in result)
        from cgi import escape
        self.failUnless(escape(EXPECTED) in result)

    def test_raw_directive_file_directive_raises(self):

        resty = self._makeOne()
        resty.source = '.. raw:: html\n  :file: inclusion.txt'
        self.assertRaises(NotImplementedError, resty.render)

    def test_raw_directive_url_directive_raises(self):

        resty = self._makeOne()
        resty.source = '.. raw:: html\n  :url: http://www.zope.org/'
        self.assertRaises(NotImplementedError, resty.render)

    def test_csv_table_file_option_raise(self):

        resty = self._makeOne()
        csv_file = self._csvfile()
        resty.source = '.. csv-table:: \n  :file: %s' % csv_file
        result = resty.render()
        self.failUnless('daemon' not in result, 
                        'csv-table/file directive is not disabled!')

    def test_csv_table_url_option_raise(self):
        resty = self._makeOne()
        csv_file = self._csvfile()
        resty.source = '.. csv-table:: \n  :url: file://%s' % csv_file
        result = resty.render()
        self.failUnless('daemon' not in result, 
                        'csv-table/url directive is not disabled!')


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestZReST))
    return suite

if __name__ == '__main__':
    unittest.main(defaultSuite='test_suite')
