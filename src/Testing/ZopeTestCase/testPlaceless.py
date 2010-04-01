##############################################################################
#
# Copyright (c) 2005 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Placeless setup tests

$Id$
"""

from Testing import ZopeTestCase

from Testing.ZopeTestCase.placeless import setUp, tearDown
from Testing.ZopeTestCase.placeless import zcml
from Testing.ZopeTestCase.placeless import temporaryPlacelessSetUp

import Products.Five.tests
from Products.Five.tests.adapters import IAdapted
from Products.Five.tests.adapters import Adaptable


def setupZCML():
    zcml.load_config('meta.zcml', Products.Five)
    zcml.load_config('permissions.zcml', Products.Five)
    zcml.load_config('directives.zcml', Products.Five.tests)


class TestPlacelessSetUp(ZopeTestCase.ZopeTestCase):
    '''Tests ZopeTestCase with placeless setup'''

    def afterSetUp(self):
        tearDown()

    def beforeTearDown(self):
        tearDown()

    def testSimple(self):
        # SetUp according to Five's adapter test
        setUp()
        setupZCML()
        # Now we have a fixture that should work for adaptation
        adapted = IAdapted(Adaptable())
        self.assertEqual(adapted.adaptedMethod(), 'Adapted: The method')

    def func(self, *args):
        adapted = IAdapted(Adaptable())
        return True

    def testNoCA(self):
        self.assertRaises(TypeError, self.func)

    def testAvailableCA(self):
        setUp()
        setupZCML()
        self.assertEqual(self.func(), True)

    def testDecoratorLoadsZCMLCallable(self):
        f = temporaryPlacelessSetUp(self.func, required_zcml=setupZCML)
        self.assertEqual(f(), True)

    def testDecoratorLoadsZCMLIterable(self):
        f = temporaryPlacelessSetUp(self.func, required_zcml=(setupZCML,))
        self.assertEqual(f(), True)

    def testPlacelessFlagDisablesDecoration(self):
        f = temporaryPlacelessSetUp(self.func, placeless_available=False, required_zcml=setupZCML)
        self.assertRaises(TypeError, f)

    def testDecoratedFuncLoadsZCMLCallable(self):
        f = temporaryPlacelessSetUp(self.func)
        self.assertEqual(f(required_zcml=setupZCML), True)

    def testDecoratedFuncLoadsZCMLIterable(self):
        f = temporaryPlacelessSetUp(self.func)
        self.assertEqual(f(required_zcml=(setupZCML,)), True)


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestPlacelessSetUp))
    return suite

