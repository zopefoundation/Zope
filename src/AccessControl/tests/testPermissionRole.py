##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
"""Tests of PermissionRole
"""

__rcs_id__='$Id$'
__version__='$Revision: 1.4 $'[11:-2]

import os, sys, unittest

from AccessControl.PermissionRole import PermissionRole
from Acquisition import Implicit, Explicit, aq_base

ViewPermission = 'View'
EditThingsPermission = 'Edit Things!'
DeletePermission = 'Delete'


class AppRoot(Explicit):
    _View_Permission = None
    _Edit_Things__Permission = ('Manager', 'Owner')
    # No default for delete permission.

class ImplicitContainer(Implicit):
    pass

class ExplicitContainer(Explicit):
    pass

class RestrictiveObject(Implicit):
    _View_Permission = ('Manager',)
    _Delete_Permission = ()  # Nobody

class PermissiveObject(Explicit):
    _Edit_Things__Permission = ['Anonymous']


def assertPRoles(ob, permission, expect):
    """
    Asserts that in the context of ob, the given permission maps to
    the given roles.
    """
    pr = PermissionRole(permission)
    roles = pr.__of__(ob)
    roles2 = aq_base(pr).__of__(ob)
    assert roles == roles2 or tuple(roles) == tuple(roles2), (
        'Different methods of checking roles computed unequal results')
    same = 0
    if roles:
        # When verbose security is enabled, permission names are
        # embedded in the computed roles.  Remove the permission
        # names.
        roles = [r for r in roles if not r.endswith('_Permission')]
    if roles is None or expect is None:
        if (roles is None or tuple(roles) == ('Anonymous',)) and (
            expect is None or tuple(expect) == ('Anonymous',)):
            same = 1
    else:
        got = {}
        for r in roles: got[r] = 1
        expected = {}
        for r in expect: expected[r] = 1
        if got == expected:  # Dict compare does the Right Thing.
            same = 1
    assert same, 'Expected roles: %s, got: %s' % (`expect`, `roles`)


class PermissionRoleTests (unittest.TestCase):

    def testRestrictive(self, explicit=0):
        app = AppRoot()
        if explicit:
            app.c = ExplicitContainer()
        else:
            app.c = ImplicitContainer()
        app.c.o = RestrictiveObject()
        o = app.c.o
        assertPRoles(o, ViewPermission,       ('Manager',))
        assertPRoles(o, EditThingsPermission, ('Manager','Owner',))
        assertPRoles(o, DeletePermission,     ())

    def testPermissive(self, explicit=0):
        app = AppRoot()
        if explicit:
            app.c = ExplicitContainer()
        else:
            app.c = ImplicitContainer()
        app.c.o = PermissiveObject()
        o = app.c.o
        assertPRoles(o, ViewPermission,       ('Anonymous',))
        assertPRoles(o, EditThingsPermission, ('Anonymous','Manager','Owner',))
        assertPRoles(o, DeletePermission,     ('Manager',))

    def testExplicit(self):
        self.testRestrictive(1)
        self.testPermissive(1)

    def testAppDefaults(self):
        o = AppRoot()
        assertPRoles(o, ViewPermission,       ('Anonymous',))
        assertPRoles(o, EditThingsPermission, ('Manager','Owner',))
        assertPRoles(o, DeletePermission,     ('Manager',))

    def testPermissionRoleSupportsGetattr(self):
        a = PermissionRole('a')
        self.failUnless(getattr(a, '__roles__') == ('Manager',))
        self.failUnless(getattr(a, '_d') == ('Manager',))
        self.failUnless(getattr(a, '__name__') == 'a')
        self.failUnless(getattr(a, '_p') == '_a_Permission')

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(PermissionRoleTests))
    return suite

def main():
    unittest.TextTestRunner().run(test_suite())

if __name__ == '__main__':
    main()
