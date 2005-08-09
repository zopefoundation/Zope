##############################################################################
#
# Copyright (c) 2004, 2005 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Test security induced by ZCML

$Id: test_security.py 12915 2005-05-31 10:23:19Z philikon $
"""
import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from Products.Five.tests.fivetest import *

import zope.security
from zope.component import getView
from zope.testing.cleanup import CleanUp

import Products.Five.security
from Products.Five import zcml
from Products.Five.traversable import FakeRequest
from Products.Five.security import clearSecurityInfo, newInteraction
from Products.Five.tests.dummy import Dummy1, Dummy2
from Globals import InitializeClass


def assertRolesEqual(actual, expect):
    if actual:
        # filter out embedded permissions, which appear when
        # verbose security is enabled
        filtered = [r for r in actual if not r.endswith('_Permission')]
        if isinstance(actual, tuple):
            actual = tuple(filtered)
        else:
            actual = filtered
    if actual != expect:
        raise AssertionError('%s != %s' % (repr(actual), repr(expect)))


class PageSecurityTest(FiveTestCase):

    def test_page_security(self):
        decl = """
        <configure xmlns="http://namespaces.zope.org/zope"
            xmlns:browser="http://namespaces.zope.org/browser">

          <browser:page
             for="Products.Five.tests.dummy.IDummy"
             class="Products.Five.tests.dummy.DummyView"
             attribute="foo"
             name="test_page_security"
             permission="zope2.ViewManagementScreens"
           />

        </configure>
        """
        zcml.load_string(decl)
        request = FakeRequest()
        # Wrap into an acquisition so that imPermissionRole objects
        # can be evaluated.
        view = getView(Dummy1(), 'test_page_security', request)

        ac = getattr(view, '__ac_permissions__')
        # It's protecting the object with the permission, and not the
        # attribute, so we get ('',) instead of ('foo',).
        ex_ac = (('View management screens', ('',)),)
        self.assertEquals(ac, ex_ac)

        # Wrap into an acquisition so that imPermissionRole objects
        # can be evaluated. __roles__ is a imPermissionRole object.
        view = view.__of__(self.folder)
        view_roles = getattr(view, '__roles__', None)
        self.failIf(view_roles is None)
        self.failIf(view_roles == ())
        assertRolesEqual(view_roles, ('Manager',))


class SecurityEquivalenceTest(FiveTestCase):

    def setUp(self):
        self.dummy1 = Dummy1
        self.dummy2 = Dummy2

    def tearDown(self):
        clearSecurityInfo(self.dummy1)
        clearSecurityInfo(self.dummy2)

    def test_equivalence(self):
        self.failIf(hasattr(self.dummy1, '__ac_permissions__'))
        self.failIf(hasattr(self.dummy2, '__ac_permissions__'))

        decl = """
        <configure xmlns="http://namespaces.zope.org/zope">

        <content
            class="Products.Five.tests.dummy.Dummy1">

          <allow attributes="foo" />

          <!-- XXX not yet supported
          <deny attributes="baz" />
          -->

          <require attributes="bar keg"
              permission="zope2.ViewManagementScreens"
              />

        </content>
        </configure>
        """
        zcml.load_string(decl)
        InitializeClass(self.dummy2)

        ac1 = getattr(self.dummy1, '__ac_permissions__')
        ac2 = getattr(self.dummy2, '__ac_permissions__')
        self.assertEquals(ac1, ac2)

        bar_roles1 = getattr(self.dummy1, 'bar__roles__').__of__(self.dummy1)
        assertRolesEqual(bar_roles1.__of__(self.dummy1), ('Manager',))

        keg_roles1 = getattr(self.dummy1, 'keg__roles__').__of__(self.dummy1)
        assertRolesEqual(keg_roles1.__of__(self.dummy1), ('Manager',))

        foo_roles1 = getattr(self.dummy1, 'foo__roles__')
        assertRolesEqual(foo_roles1, None)

        # XXX Not yet supported.
        # baz_roles1 = getattr(self.dummy1, 'baz__roles__')
        # self.assertEquals(baz_roles1, ())

        bar_roles2 = getattr(self.dummy2, 'bar__roles__').__of__(self.dummy2)
        assertRolesEqual(bar_roles2.__of__(self.dummy2), ('Manager',))

        keg_roles2 = getattr(self.dummy2, 'keg__roles__').__of__(self.dummy2)
        assertRolesEqual(keg_roles2.__of__(self.dummy2), ('Manager',))

        foo_roles2 = getattr(self.dummy2, 'foo__roles__')
        assertRolesEqual(foo_roles2, None)

        baz_roles2 = getattr(self.dummy2, 'baz__roles__')
        assertRolesEqual(baz_roles2, ())


class FiveCheckPermissionTest(FiveTestCase):

    def afterSetUp(self):
        self.checkPermission = Products.Five.security.checkPermission

    def test_publicPermissionId(self):
        self.failUnless(self.checkPermission('zope2.Public', self.folder))

    def test_privatePermissionId(self):
        self.failIf(self.checkPermission('zope.Private', self.folder))
        self.failIf(self.checkPermission('zope2.Private', self.folder))

    def test_accessPermissionId(self):
        self.failUnless(self.checkPermission('zope2.AccessContentsInformation',
                                             self.folder))

    def test_invalidPermissionId(self):
        self.failIf(self.checkPermission('notapermission', self.folder))

class Zope3CheckPermissionTest(FiveCheckPermissionTest):

    def afterSetUp(self):
        self.checkPermission = zope.security.checkPermission
        newInteraction()

def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(SecurityEquivalenceTest))
    suite.addTest(makeSuite(PageSecurityTest))
    suite.addTest(makeSuite(FiveCheckPermissionTest))
    suite.addTest(makeSuite(Zope3CheckPermissionTest))
    return suite

if __name__ == '__main__':
    framework()
