#!/usr/bin/env python
"""Run all tests."""

import unittest

def test_suite():
    suite = unittest.TestSuite()
    for mname in ('DTMLTests', 'HTMLTests', 'Expressions', 'TALES'):
        m = __import__('test' + mname)
        suite.addTest(m.test_suite())
    return suite

if __name__ == "__main__":
    unittest.main(defaultTest='test_suite')
