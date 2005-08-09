#!/usr/bin/env python
"""Run all tests."""

import unittest
import glob
import os
import sys

def test_suite():
    suite = unittest.TestSuite()
    for mname in glob.glob(os.path.join(sys.path[0], 'test*.py')):
        mname = os.path.split(mname)[1][:-3]
        m = __import__(mname)
        suite.addTest(m.test_suite())
    return suite

if __name__ == "__main__":
    unittest.main(defaultTest='test_suite')
