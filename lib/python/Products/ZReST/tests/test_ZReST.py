# -*- coding: iso-8859-15 -*-

""" Unit tests for ZReST objects

$Id$
"""
import unittest

txt = """Hello World
============

text text

Von Vögeln und Öfen
===================

- some
- more
- text

"""

class TestZReST(unittest.TestCase):

    def _getTargetClass(self):
        from Products.ZReST.ZReST import ZReST
        return ZReST

    def _makeOne(self, id='test', *args, **kw):
        return self._getTargetClass()(id=id, *args, **kw)

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

    def testConversion(self):
        resty = self._makeOne()
        resty.source = txt
        resty.input_encoding = 'iso-8859-15'
        resty.output_encoding = 'iso-8859-15'
        resty.render()
        html = resty.index_html()

        s = '<h1><a id="hello-world" name="hello-world">Hello World</a></h1>'
        self.assertEqual(s in html, True)

        s = '<h1><a id="von-v-geln-und-fen" name="von-v-geln-und-fen">'\
            'Von Vögeln und Öfen</a></h1>'
        self.assertEqual(s in html, True)

        # ZReST should render a complete HTML document
        self.assertEqual('<html' in html, True)
        self.assertEqual('<body>' in html, True)

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


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestZReST))
    return suite

if __name__ == '__main__':
    unittest.main(defaultSuite='test_suite')
