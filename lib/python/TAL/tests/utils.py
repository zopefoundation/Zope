"""Helper functions for the test suite."""

import os
import sys

mydir = os.path.abspath(os.path.dirname(__file__))
codedir = os.path.dirname(os.path.dirname(mydir))

if codedir not in sys.path:
    sys.path.append(codedir)

import unittest


# Set skipxml to true if an XML parser could not be found.
pyexpat = None
skipxml = 0
try:
    import pyexpat
except ImportError:
    try:
        # the C extension in PyXML
        import xml.parsers.pyexpat
    except ImportError:
        skipxml = 1
    else:
        pyexpat = xml.parsers.pyexpat


# Set oldexpat if the StartDoctypeDeclHandler and XmlDeclHandler are
# not supported.  The tests need to know whether the events reported
# by those handlers should be expected, but need to make sure the
# right thing is returned if they are.
oldexpat = 0
if pyexpat is not None:
    p = pyexpat.ParserCreate()
    # Can't use hasattr() since pyexpat supports the handler
    # attributes in a broken way.
    try:
        p.StartDoctypeDeclHandler = None
    except AttributeError:
        oldexpat = 1


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
##         print "Failures (assertion failures):"
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
