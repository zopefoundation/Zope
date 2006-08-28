"""test runner that works with zope.testing.testrunner"""
import unittest
import os, sys

import os, sys

suite = unittest.TestSuite()

names = os.listdir(os.path.dirname(__file__))
tests = [x[:-3] for x in names \
         if x.startswith('test') and x.endswith('.py') \
         and not x == 'tests.py']

import Testing.ZopeTestCase
for test in tests:
    m = __import__("Testing.ZopeTestCase.%s" %test)
    m = getattr(Testing.ZopeTestCase, test)
    if hasattr(m, 'test_suite'):
        suite.addTest(m.test_suite())

def test_suite():
    return suite
