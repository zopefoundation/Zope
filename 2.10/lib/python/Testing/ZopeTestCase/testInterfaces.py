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
"""Interface tests

$Id$
"""

import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from Testing.ZopeTestCase import *
from Testing.ZopeTestCase.interfaces import *

from Interface.Verify import verifyClass
from Interface.Verify import verifyObject


class TestAbstractClasses(TestCase):

    def testIProfiled(self):
        self.failUnless(verifyClass(IProfiled, Profiled))

    def testIFunctional(self):
        self.failUnless(verifyClass(IFunctional, Functional))


class TestBaseTestCase(TestCase):

    def testIProfiled(self):
        self.failUnless(verifyClass(IProfiled, TestCase))
        self.failUnless(verifyObject(IProfiled, self))

    def testIZopeTestCase(self):
        self.failUnless(verifyClass(IZopeTestCase, TestCase))
        self.failUnless(verifyObject(IZopeTestCase, self))


class TestZopeTestCase(ZopeTestCase):

    _setup_fixture = 0

    def testIProfiled(self):
        self.failUnless(verifyClass(IProfiled, ZopeTestCase))
        self.failUnless(verifyObject(IProfiled, self))

    def testIZopeTestCase(self):
        self.failUnless(verifyClass(IZopeTestCase, ZopeTestCase))
        self.failUnless(verifyObject(IZopeTestCase, self))

    def testIZopeSecurity(self):
        self.failUnless(verifyClass(IZopeSecurity, ZopeTestCase))
        self.failUnless(verifyObject(IZopeSecurity, self))


class TestFunctionalTestCase(FunctionalTestCase):

    _setup_fixture = 0

    def testIFunctional(self):
        self.failUnless(verifyClass(IFunctional, FunctionalTestCase))
        self.failUnless(verifyObject(IFunctional, self))

    def testIProfiled(self):
        self.failUnless(verifyClass(IProfiled, FunctionalTestCase))
        self.failUnless(verifyObject(IProfiled, self))

    def testIZopeTestCase(self):
        self.failUnless(verifyClass(IZopeTestCase, FunctionalTestCase))
        self.failUnless(verifyObject(IZopeTestCase, self))

    def testIZopeSecurity(self):
        self.failUnless(verifyClass(IZopeSecurity, FunctionalTestCase))
        self.failUnless(verifyObject(IZopeSecurity, self))


class TestPortalTestCase(PortalTestCase):

    _configure_portal = 0

    def _portal(self):
        return None

    def testIProfiled(self):
        self.failUnless(verifyClass(IProfiled, PortalTestCase))
        self.failUnless(verifyObject(IProfiled, self))

    def testIZopeTestCase(self):
        self.failUnless(verifyClass(IZopeTestCase, PortalTestCase))
        self.failUnless(verifyObject(IZopeTestCase, self))

    def testIPortalTestCase(self):
        self.failUnless(verifyClass(IPortalTestCase, PortalTestCase))
        self.failUnless(verifyObject(IPortalTestCase, self))

    def testIPortalSecurity(self):
        self.failUnless(verifyClass(IPortalSecurity, PortalTestCase))
        self.failUnless(verifyObject(IPortalSecurity, self))


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestAbstractClasses))
    suite.addTest(makeSuite(TestBaseTestCase))
    suite.addTest(makeSuite(TestZopeTestCase))
    suite.addTest(makeSuite(TestFunctionalTestCase))
    suite.addTest(makeSuite(TestPortalTestCase))
    return suite

if __name__ == '__main__':
    framework()

