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
"""Interface tests
"""

from Testing.ZopeTestCase import *
from Testing.ZopeTestCase.interfaces import *

from zope.interface.verify import verifyClass
from zope.interface.verify import verifyObject


class TestAbstractClasses(TestCase):

    def testIFunctional(self):
        self.assertTrue(verifyClass(IFunctional, Functional))


class TestBaseTestCase(TestCase):

    def testIZopeTestCase(self):
        self.assertTrue(verifyClass(IZopeTestCase, TestCase))
        self.assertTrue(verifyObject(IZopeTestCase, self))


class TestZopeTestCase(ZopeTestCase):

    _setup_fixture = 0

    def testIZopeTestCase(self):
        self.assertTrue(verifyClass(IZopeTestCase, ZopeTestCase))
        self.assertTrue(verifyObject(IZopeTestCase, self))

    def testIZopeSecurity(self):
        self.assertTrue(verifyClass(IZopeSecurity, ZopeTestCase))
        self.assertTrue(verifyObject(IZopeSecurity, self))


class TestFunctionalTestCase(FunctionalTestCase):

    _setup_fixture = 0

    def testIFunctional(self):
        self.assertTrue(verifyClass(IFunctional, FunctionalTestCase))
        self.assertTrue(verifyObject(IFunctional, self))

    def testIZopeTestCase(self):
        self.assertTrue(verifyClass(IZopeTestCase, FunctionalTestCase))
        self.assertTrue(verifyObject(IZopeTestCase, self))

    def testIZopeSecurity(self):
        self.assertTrue(verifyClass(IZopeSecurity, FunctionalTestCase))
        self.assertTrue(verifyObject(IZopeSecurity, self))


class TestPortalTestCase(PortalTestCase):

    _configure_portal = 0

    def _portal(self):
        return None

    def testIZopeTestCase(self):
        self.assertTrue(verifyClass(IZopeTestCase, PortalTestCase))
        self.assertTrue(verifyObject(IZopeTestCase, self))

    def testIPortalTestCase(self):
        self.assertTrue(verifyClass(IPortalTestCase, PortalTestCase))
        self.assertTrue(verifyObject(IPortalTestCase, self))

    def testIPortalSecurity(self):
        self.assertTrue(verifyClass(IPortalSecurity, PortalTestCase))
        self.assertTrue(verifyObject(IPortalSecurity, self))


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestAbstractClasses))
    suite.addTest(makeSuite(TestBaseTestCase))
    suite.addTest(makeSuite(TestZopeTestCase))
    suite.addTest(makeSuite(TestFunctionalTestCase))
    suite.addTest(makeSuite(TestPortalTestCase))
    return suite

