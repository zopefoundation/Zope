#! /usr/bin/env python1.5
"""Tests for TALInterpreter."""

import sys

import utils
import unittest

from StringIO import StringIO

from TAL.TALDefs import METALError
from TAL.HTMLTALParser import HTMLTALParser
from TAL.TALInterpreter import TALInterpreter
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
        program, macros = self._compile(INPUT)
        sio = StringIO()
        interp = TALInterpreter(program, {}, DummyEngine(), sio, wrap=60)
        interp()
        self.assertEqual(sio.getvalue(), EXPECTED)


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(MacroErrorsTestCase, "check_"))
    suite.addTest(unittest.makeSuite(OutputPresentationTestCase, "check_"))
    return suite


if __name__ == "__main__":
    errs = utils.run_suite(test_suite())
    sys.exit(errs and 1 or 0)
