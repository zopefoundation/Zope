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

$Id: testInterfaces.py,v 1.3 2005/01/01 20:38:16 shh42 Exp $
"""

import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from Testing import ZopeTestCase
from Testing.ZopeTestCase.interfaces import *

try:
    from Interface.Verify import verifyObject
    have_verify = 1
except ImportError:
    print 'testInterfaces.py: The tests in this module require Zope >= 2.6'
    have_verify = 0


class TestBaseTestCase(ZopeTestCase.TestCase):

    _setup_fixture = 0

    def testIProfiled(self):
        self.failUnless(verifyObject(IProfiled, self))

    def testIZopeTestCase(self):
        self.failUnless(verifyObject(IZopeTestCase, self))


class TestZopeTestCase(ZopeTestCase.ZopeTestCase):

    _setup_fixture = 0

    def testIProfiled(self):
        self.failUnless(verifyObject(IProfiled, self))

    def testIZopeTestCase(self):
        self.failUnless(verifyObject(IZopeTestCase, self))

    def testIZopeSecurity(self):
        self.failUnless(verifyObject(IZopeSecurity, self))


class TestFunctionalTestCase(ZopeTestCase.FunctionalTestCase):

    _setup_fixture = 0

    def testIFunctional(self):
        self.failUnless(verifyObject(IFunctional, self))

    def testIProfiled(self):
        self.failUnless(verifyObject(IProfiled, self))

    def testIZopeTestCase(self):
        self.failUnless(verifyObject(IZopeTestCase, self))

    def testIZopeSecurity(self):
        self.failUnless(verifyObject(IZopeSecurity, self))


class TestPortalTestCase(ZopeTestCase.PortalTestCase):

    _configure_portal = 0

    def getPortal(self):
        return None

    def testIProfiled(self):
        self.failUnless(verifyObject(IProfiled, self))

    def testIZopeTestCase(self):
        self.failUnless(verifyObject(IZopeTestCase, self))

    def testIZopeSecurity(self):
        self.failUnless(verifyObject(IZopeSecurity, self))

    def testIPortalTestCase(self):
        self.failUnless(verifyObject(IPortalTestCase, self))

    def testIPortalSecurity(self):
        self.failUnless(verifyObject(IPortalSecurity, self))


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    if have_verify:
        suite.addTest(makeSuite(TestBaseTestCase))
        suite.addTest(makeSuite(TestZopeTestCase))
        suite.addTest(makeSuite(TestFunctionalTestCase))
        suite.addTest(makeSuite(TestPortalTestCase))
    return suite

if __name__ == '__main__':
    framework()

