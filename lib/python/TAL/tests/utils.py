"""Helper functions for the test suite."""

import os
import sys

mydir = os.path.abspath(os.path.join(os.getcwd(), os.path.dirname(__file__)))
codedir = os.path.dirname(os.path.dirname(mydir))

if codedir not in sys.path:
    sys.path.append(codedir)

import unittest


def run_suite(suite, outf=None, errf=None):
    if outf is None:
        outf = sys.stdout
    runner = unittest.TextTestRunner(outf)
    result = runner.run(suite)

##     print "\n\n"
##     if result.errors:
##         print "Errors (unexpected exceptions):"
##         map(print_error, result.errors)
##         print
##     if result.failures:
##         print "Failures:"
##         map(print_error, result.failures)
##         print
    newerrs = len(result.errors) + len(result.failures)
    if newerrs:
        print "'Errors' indicate exceptions other than AssertionError."
        print "'Failures' indicate AssertionError"
        if errf is None:
            errf = sys.stderr
        errf.write("%d errors, %d failures\n"
                   % (len(result.errors), len(result.failures)))
    return newerrs


def print_error(info):
    testcase, (type, e, tb) = info
