#! /usr/bin/env python1.5
"""Tests that run driver.py over input files comparing to output files."""

import os
import sys
import glob

from TAL.tests import utils
import unittest

from zope.tal import runtest

class FileTestCase(unittest.TestCase):

    def __init__(self, file, dir):
        self.__file = file
        self.__dir = dir
        unittest.TestCase.__init__(self)

    def shortDescription(self):
        return os.path.join("...", "TAL", "tests", "input",
                            os.path.basename(self.__file))

    def runTest(self):
        basename = os.path.basename(self.__file)
        #sys.stdout.write(basename + " ")
        sys.stdout.flush()
        if basename[:10] == 'test_metal':
            sys.argv = ["", "-Q", "-m", self.__file]
        else:
            sys.argv = ["", "-Q", self.__file]
        pwd = os.getcwd()
        try:
            try:
                os.chdir(self.__dir)
                runtest.main()
            finally:
                os.chdir(pwd)
        except SystemExit, what:
            if what.code:
                self.fail("output for %s didn't match" % self.__file)

try:
    script = __file__
except NameError:
    script = sys.argv[0]

def test_suite():
    suite = unittest.TestSuite()
    dir = os.path.dirname(script)
    dir = os.path.abspath(dir)
    parentdir = os.path.dirname(dir)
    prefix = os.path.join(dir, "input", "test*.")
    if utils.skipxml:
        xmlargs = []
    else:
        xmlargs = glob.glob(prefix + "xml")
        xmlargs.sort()
    htmlargs = glob.glob(prefix + "html")
    htmlargs.sort()
    args = xmlargs + htmlargs
    if not args:
        sys.stderr.write("Warning: no test input files found!!!\n")
    for arg in args:
        case = FileTestCase(arg, parentdir)
        suite.addTest(case)
    return suite

if __name__ == "__main__":
    errs = utils.run_suite(test_suite())
    sys.exit(errs and 1 or 0)
