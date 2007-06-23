##############################################################################
#
# Copyright (c) 2005 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Runs all tests in the current directory [and below]

Execute like:
  python runalltests.py [-R]

$Id$
"""

__version__ = '0.3.1'

import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

import unittest
TestRunner = unittest.TextTestRunner
suite = unittest.TestSuite()
cwd = os.getcwd()

def test_finder(recurse, dir, names):
    if dir == os.curdir or '__init__.py' in names:
        parts = [x for x in dir[len(os.curdir):].split(os.sep) if x]
        tests = [x for x in names if x.startswith('test') and x.endswith('.py')]
        for test in tests:
            if test == 'tests.py' and 'ZopeTestCase' in cwd:
                # Skip tests.py when running ZTC tests
                continue
            modpath = parts + [test[:-3]]
            m = __import__('.'.join(modpath))
            for part in modpath[1:]:
                m = getattr(m, part)
            if hasattr(m, 'test_suite'):
                suite.addTest(m.test_suite())
    if not recurse:
        names[:] = []

if __name__ == '__main__':
    os.path.walk(os.curdir, test_finder, '-R' in sys.argv)
    TestRunner().run(suite)

