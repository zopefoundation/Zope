#! /usr/bin/env python1.5
"""Tests for TALInterpreter."""

import sys

import utils
import unittest

from TAL.TALDefs import METALError
from TAL.HTMLTALParser import HTMLTALParser
from TAL.TALInterpreter import TALInterpreter
from TAL.DummyEngine import DummyEngine


class MacroErrorsTestCase(unittest.TestCase):

    def _compile(self, source):
        parser = HTMLTALParser()
        parser.parseString(source)
        program, macros = parser.getCode()
        return program, macros

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


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(MacroErrorsTestCase, "check_"))
    return suite


if __name__ == "__main__":
    errs = utils.run_suite(test_suite())
    sys.exit(errs and 1 or 0)
