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
"""

from zope.component import adapts
from zope.interface import implements, Interface

from Testing import ZopeTestCase

from Testing.ZopeTestCase.placeless import setUp, tearDown
from Testing.ZopeTestCase.placeless import zcml
from Testing.ZopeTestCase.placeless import temporaryPlacelessSetUp


def setupZCML():
    import AccessControl
    import Zope2.App
    zcml.load_config('meta.zcml', Zope2.App)
    zcml.load_config('permissions.zcml', AccessControl)
    zcml.load_config('directives.zcml', ZopeTestCase)


class IAdaptable(Interface):
    """This is a Zope interface.
    """
    def method():
        """This method will be adapted
        """

class IAdapted(Interface):
    """The interface we adapt to.
    """

    def adaptedMethod():
        """A method to adapt.
        """

class Adaptable:
    implements(IAdaptable)

    def method(self):
        return "The method"


class Adapter:
    implements(IAdapted)
    adapts(IAdaptable)

    def __init__(self, context):
        self.context = context

    def adaptedMethod(self):
        return "Adapted: %s" % self.context.method()


class TestPlacelessSetUp(ZopeTestCase.ZopeTestCase):
    '''Tests ZopeTestCase with placeless setup'''

    def afterSetUp(self):
        tearDown()

    def beforeTearDown(self):
        tearDown()

    def testSimple(self):
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

