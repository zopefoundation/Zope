#! /usr/bin/env python1.5
"""Tests for TALInterpreter."""

import sys

from TAL.tests import utils
import unittest

from StringIO import StringIO

from TAL.TALDefs import METALError
from TAL.HTMLTALParser import HTMLTALParser
from TAL.TALInterpreter import TALInterpreter
from TAL.TALInterpreter import interpolate
from TAL.DummyEngine import DummyEngine


class TestCaseBase(unittest.TestCase):

    def _compile(self, source):
        parser = HTMLTALParser()
        parser.parseString(source)
        program, macros = parser.getCode()
        return program, macros


class MacroErrorsTestCase(TestCaseBase):

    def setUp(self):
        dummy, macros = self._compile('<p metal:define-macro="M">Booh</p>')
        self.macro = macros['M']
        self.engine = DummyEngine(macros)
        program, dummy = self._compile('<p metal:use-macro="M">Bah</p>')
        self.interpreter = TALInterpreter(program, {}, self.engine)

    def tearDown(self):
        try:
            self.interpreter()
        except METALError:
            pass
        else:
            self.fail("Expected METALError")

    def check_mode_error(self):
        self.macro[1] = ("mode", "duh")

    def check_version_error(self):
        self.macro[0] = ("version", "duh")


class OutputPresentationTestCase(TestCaseBase):

    def check_attribute_wrapping(self):
        # To make sure the attribute-wrapping code is invoked, we have to
        # include at least one TAL/METAL attribute to avoid having the start
        # tag optimized into a rawtext instruction.
        INPUT = r"""
        <html this='element' has='a' lot='of' attributes=', so' the='output'
              needs='to' be='line' wrapped='.' tal:define='foo nothing'>
        </html>"""
        EXPECTED = r'''
        <html this="element" has="a" lot="of"
              attributes=", so" the="output" needs="to"
              be="line" wrapped=".">
        </html>''' "\n"
        self.compare(INPUT, EXPECTED)

    def check_unicode_content(self):
        INPUT = """<p tal:content="python:u'déjà-vu'">para</p>"""
        EXPECTED = u"""<p>déjà-vu</p>""" "\n"
        self.compare(INPUT, EXPECTED)

    def check_unicode_structure(self):
        INPUT = """<p tal:replace="structure python:u'déjà-vu'">para</p>"""
        EXPECTED = u"""déjà-vu""" "\n"
        self.compare(INPUT, EXPECTED)

    def check_i18n_replace_number(self):
        INPUT = """
        <p i18n:translate="foo ${bar}">
        <span tal:replace="python:123" i18n:name="bar">para</span>
        </p>"""
        EXPECTED = u"""
        <p>FOO 123</p>""" "\n"
        self.compare(INPUT, EXPECTED)

    def check_entities(self):
        INPUT = ('<img tal:define="foo nothing" '
                 'alt="&a; &#1; &#x0a; &a &#45 &; &#0a; <>" />')
        EXPECTED = ('<img alt="&a; &#1; &#x0a; '
                    '&amp;a &amp;#45 &amp;; &amp;#0a; &lt;&gt;" />\n')
        self.compare(INPUT, EXPECTED)
        
    def compare(self, INPUT, EXPECTED):
        program, macros = self._compile(INPUT)
        sio = StringIO()
        interp = TALInterpreter(program, {}, DummyEngine(), sio, wrap=60)
        interp()
        self.assertEqual(sio.getvalue(), EXPECTED)

class InterpolateTestCase(TestCaseBase):
    def check_syntax_ok(self):
        text = "foo ${bar_0MAN} $baz_zz bee"
        mapping = {'bar_0MAN': 'fish', 'baz_zz': 'moo'}
        expected = "foo fish moo bee"
        self.assertEqual(interpolate(text, mapping), expected)

    def check_syntax_bad(self):
        text = "foo $_bar_man} $ ${baz bee"
        mapping = {'_bar_man': 'fish', 'baz': 'moo'}
        expected = text
        self.assertEqual(interpolate(text, mapping), expected)

    def check_missing(self):
        text = "foo ${bar} ${baz}"
        mapping = {'bar': 'fish'}
        expected = "foo fish ${baz}"
        self.assertEqual(interpolate(text, mapping), expected)

    def check_redundant(self):
        text = "foo ${bar}"
        mapping = {'bar': 'fish', 'baz': 'moo'}
        expected = "foo fish"
        self.assertEqual(interpolate(text, mapping), expected)

    def check_numeric(self):
        text = "foo ${bar}"
        mapping = {'bar': 123}
        expected = "foo 123"
        self.assertEqual(interpolate(text, mapping), expected)

    def check_unicode(self):
        text = u"foo ${bar}"
        mapping = {u'bar': u'baz'}
        expected = u"foo baz"
        self.assertEqual(interpolate(text, mapping), expected)

    def check_unicode_mixed_unknown_encoding(self):
        # This test assumes that sys.getdefaultencoding is ascii...
        text = u"foo ${bar}"
        mapping = {u'bar': 'd\xe9j\xe0'}
        expected = u"foo d\\xe9j\\xe0"
        self.assertEqual(interpolate(text, mapping), expected)

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(MacroErrorsTestCase, "check_"))
    suite.addTest(unittest.makeSuite(OutputPresentationTestCase, "check_"))
    suite.addTest(unittest.makeSuite(InterpolateTestCase, "check_"))
    return suite


if __name__ == "__main__":
    errs = utils.run_suite(test_suite())
    sys.exit(errs and 1 or 0)
