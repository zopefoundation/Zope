#! /usr/bin/env python1.5
"""Run all tests."""

import sys
import utils
import unittest
import test_htmlparser
import test_htmltalparser
import test_talinterpreter
import test_files
import test_sourcepos

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(test_htmlparser.test_suite())
    suite.addTest(test_htmltalparser.test_suite())
    if not utils.skipxml:
        import test_xmlparser
        suite.addTest(test_xmlparser.test_suite())
    suite.addTest(test_talinterpreter.test_suite())
    suite.addTest(test_files.test_suite())
    suite.addTest(test_sourcepos.test_suite())
    return suite

def main():
    return utils.run_suite(test_suite())

if __name__ == "__main__":
    errs = main()
    sys.exit(errs and 1 or 0)
