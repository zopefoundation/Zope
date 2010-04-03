##############################################################################
#
# Copyright (c) 2010 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
""" Unit tests for App.Extensions module
"""
import unittest

class FuncCodeTests(unittest.TestCase):

    def _getTargetClass(self):
        from App.Extensions import FuncCode
        return FuncCode

    def _makeOne(self, f, im=0):
        return self._getTargetClass()(f, im)

    def test_ctor_not_method_no_args(self):
        def f():
            pass
        fc = self._makeOne(f)
        self.assertEqual(fc.co_varnames, ())
        self.assertEqual(fc.co_argcount, 0)

    def test_ctor_not_method_w_args(self):
        def f(a, b):
            pass
        fc = self._makeOne(f)
        self.assertEqual(fc.co_varnames, ('a', 'b'))
        self.assertEqual(fc.co_argcount, 2)

    def test_ctor_w_method_no_args(self):
        def f(self):
            pass
        fc = self._makeOne(f, im=1)
        self.assertEqual(fc.co_varnames, ())
        self.assertEqual(fc.co_argcount, 0)

    def test_ctor_w_method_w_args(self):
        def f(self, a, b):
            pass
        fc = self._makeOne(f, im=1)
        self.assertEqual(fc.co_varnames, ('a', 'b'))
        self.assertEqual(fc.co_argcount, 2)

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(FuncCodeTests),
    ))
