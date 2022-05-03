##############################################################################
#
# Copyright (c) 2006 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Test runner that works with zope.testrunner
"""

import os
import unittest

import Testing.ZopeTestCase


suite = unittest.TestSuite()

names = os.listdir(os.path.dirname(__file__))
tests = [x[:-3] for x in names
         if x.startswith('test') and x.endswith('.py') and x != 'tests.py']

for test in tests:
    m = __import__('Testing.ZopeTestCase.%s' % test)
    m = getattr(Testing.ZopeTestCase, test)
    if hasattr(m, 'test_suite'):
        suite.addTest(m.test_suite())


def test_suite():
    return suite
