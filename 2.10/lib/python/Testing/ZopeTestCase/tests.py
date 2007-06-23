##############################################################################
#
# Copyright (c) 2006 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Test runner that works with zope.testing.testrunner

$Id$
"""

import unittest
import os
import Testing.ZopeTestCase

suite = unittest.TestSuite()

names = os.listdir(os.path.dirname(__file__))
tests = [x[:-3] for x in names
         if x.startswith('test') and x.endswith('.py')
         and x != 'tests.py'
         # Don't run this module as part of the Zope2 suite
         and x != 'testWebserver.py']

for test in tests:
    m = __import__('Testing.ZopeTestCase.%s' % test)
    m = getattr(Testing.ZopeTestCase, test)
    if hasattr(m, 'test_suite'):
        suite.addTest(m.test_suite())

def test_suite():
    return suite
