#! /usr/bin/env python1.5
"""Run all tests."""

import os, sys, glob
execfile(os.path.join(sys.path[0], 'framework.py'))

def test_suite():
    suite = unittest.TestSuite()
    for mname in glob.glob(os.path.join(sys.path[0], 'test*.py')):
        mname = os.path.split(mname)[1][:-3]
        m = __import__(mname)
        suite.addTest(m.test_suite())
    return suite

if __name__ == "__main__":
    main()
