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
"""Tests the PortalTestCase

NOTE: This is *not* an example TestCase. Do not
use this file as a blueprint for your own tests!

See testPythonScript.py and testShoppingCart.py for
example test cases. See testSkeleton.py for a quick
way of getting started.
"""

from Testing import ZopeTestCase

from Acquisition import aq_base
from AccessControl import getSecurityManager
from types import ListType

import transaction

portal_name = 'dummy_1_'
user_name = ZopeTestCase.user_name


def hasattr_(ob, attr):
    return hasattr(aq_base(ob), attr)


# A dummy portal

from OFS.SimpleItem import SimpleItem
from OFS.Folder import Folder

class DummyPortal(Folder):
    def __init__(self, id):
        self.id = id
        self._addRole('Member')
        self._setObject('portal_membership', DummyMembershipTool())
        self.manage_addFolder('Members')
        self._called = []
    def clearCurrentSkin(self):
        self._called.append('clearCurrentSkin')
    def setupCurrentSkin(self):
        self._called.append('setupCurrentSkin')

class DummyMembershipTool(SimpleItem):
    id = 'portal_membership'
    def __init__(self):
        self._called = []
    def createMemberarea(self, member_id):
        self._called.append('createMemberarea')
        portal = self.aq_inner.aq_parent
        portal.Members.manage_addFolder(member_id)
    def getHomeFolder(self, member_id):
        portal = self.aq_inner.aq_parent
        return getattr(portal.Members, member_id)

class NewMembershipTool(DummyMembershipTool):
    def createMemberArea(self, member_id):
        self._called.append('createMemberArea')
        portal = self.aq_inner.aq_parent
        portal.Members.manage_addFolder(member_id)


class TestPortalTestCase(ZopeTestCase.PortalTestCase):
    '''Incrementally exercise the PortalTestCase API.'''

    _setUp = ZopeTestCase.PortalTestCase.setUp
    _tearDown = ZopeTestCase.PortalTestCase.tearDown

    def getPortal(self):
        # Must make sure we return a portal object
        self.app._setObject(portal_name, DummyPortal(portal_name))
        return getattr(self.app, portal_name)

    def setUp(self):
        # For this test case we *want* to start
        # with an empty fixture.
        self._called = []
        # Implicitly aborts previous transaction
        transaction.begin()

    def beforeSetUp(self):
        self._called.append('beforeSetUp')

    def afterSetUp(self):
        self._called.append('afterSetUp')

    def beforeTearDown(self):
        self._called.append('beforeTearDown')

    def beforeClose(self):
        self._called.append('beforeClose')

    def afterClear(self):
        self._called.append('afterClear')

    def test_getPortal(self):
        # Portal should be set up
        self.app = self._app()
        self.portal = self._portal()
        self.assertTrue(hasattr_(self.app, portal_name))
        self.assertTrue(hasattr_(self.portal, 'Members'))
        self.assertTrue(hasattr_(self.portal, 'portal_membership'))
        self.assertTrue('Member' in self.portal.userdefined_roles())

    def test_setupUserFolder(self):
        # User folder should be set up.
        self.app = self._app()
        self.portal = self._portal()
        self.assertFalse(hasattr_(self.portal, 'acl_users'))
        self._setupUserFolder()
        self.assertTrue(hasattr_(self.portal, 'acl_users'))
        # Must not complain if UF already exists
        self._setupUserFolder()

    def test_setupUser(self):
        # User should be set up
        self.app = self._app()
        self.portal = self._portal()
        self._setupUserFolder()
        self._setupUser()
        acl_user = self.portal.acl_users.getUserById(user_name)
        self.assertTrue(acl_user)
        self.assertEqual(acl_user.getRoles(), ('Member', 'Authenticated'))
        self.assertEqual(type(acl_user.roles), ListType)

    def test_setupHomeFolder(self):
        # User's home folder should be set up
        self.app = self._app()
        self.portal = self._portal()
        self._setupUserFolder()
        self._setupUser()
        self.login()
        self._setupHomeFolder()
        self.assertTrue(hasattr_(self.portal.Members, user_name))
        self.assertFalse(self.folder is None)
        # Shut up deprecation warnings
        try: owner_info = self.folder.getOwnerTuple()
        except AttributeError:
            owner_info = self.folder.getOwner(info=1)
        self.assertEqual(owner_info, ([portal_name, 'acl_users'], user_name))

    def test_refreshSkinData(self):
        # The skin cache should be refreshed
        self.app = self._app()
        self.portal = self._portal()
        self._refreshSkinData()
        self.assertEqual(self.portal._called, ['clearCurrentSkin', 'setupCurrentSkin'])

    def test_setRoles(self):
        # Roles should be set for user
        self.app = self._app()
        self.portal = self._portal()
        self._setupUserFolder()
        self._setupUser()
        test_roles = ['Manager', 'Member']
        self.setRoles(test_roles)
        acl_user = self.portal.acl_users.getUserById(user_name)
        self.assertRolesOfUser(test_roles, acl_user)

    def test_setRoles_2(self):
        # Roles should be set for logged in user
        self.app = self._app()
        self.portal = self._portal()
        self._setupUserFolder()
        self._setupUser()
        self.login()
        test_roles = ['Manager', 'Member']
        self.setRoles(test_roles)
        auth_user = getSecurityManager().getUser()
        self.assertRolesOfUser(test_roles, auth_user)

    def test_setRoles_3(self):
        # Roles should be set for a specified user
        self.app = self._app()
        self.portal = self._portal()
        self._setupUserFolder()
        self.portal.acl_users.userFolderAddUser('user_2', 'secret', [], [])
        test_roles = ['Manager', 'Member']
        self.setRoles(test_roles, 'user_2')
        acl_user = self.portal.acl_users.getUserById('user_2')
        self.assertRolesOfUser(test_roles, acl_user)

    def test_setRoles_4(self):
        # Roles should be set from a tuple
        self.app = self._app()
        self.portal = self._portal()
        self._setupUserFolder()
        self._setupUser()
        test_roles = ['Manager', 'Member']
        self.setRoles(tuple(test_roles))
        acl_user = self.portal.acl_users.getUserById(user_name)
        self.assertRolesOfUser(test_roles, acl_user)

    def test_setRoles_5(self):
        # Roles should be set from a string
        self.app = self._app()
        self.portal = self._portal()
        self._setupUserFolder()
        self._setupUser()
        test_roles = ['Manager']
        self.setRoles('Manager')
        acl_user = self.portal.acl_users.getUserById(user_name)
        self.assertRolesOfUser(test_roles, acl_user)

    def test_setPermissions(self):
        # Permissions should be set for user
        self.app = self._app()
        self.portal = self._portal()
        test_perms = ['Add Folders', 'Delete objects']
        self.setPermissions(test_perms)
        self.assertPermissionsOfRole(test_perms, 'Member')

    def test_setPermissions_2(self):
        # Permissions should be set for specified role
        self.app = self._app()
        self.portal = self._portal()
        self.portal._addRole('role_2')
        test_perms = ['Add Folders', 'Delete objects']
        self.assertPermissionsOfRole([], 'role_2')
        self.setPermissions(test_perms, 'role_2')
        self.assertPermissionsOfRole(test_perms, 'role_2')

    def test_setPermissions_3(self):
        # Permissions should be set from a tuple
        self.app = self._app()
        self.portal = self._portal()
        test_perms = ['Add Folders', 'Delete objects']
        self.setPermissions(tuple(test_perms))
        self.assertPermissionsOfRole(test_perms, 'Member')

    def test_setPermissions_4(self):
        # Permissions should be set from a string
        self.app = self._app()
        self.portal = self._portal()
        test_perms = ['Add Folders']
        self.setPermissions('Add Folders')
        self.assertPermissionsOfRole(test_perms, 'Member')

    def test_login(self):
        # User should be able to log in
        self.app = self._app()
        self.portal = self._portal()
        self._setupUserFolder()
        self._setupUser()
        auth_name = getSecurityManager().getUser().getUserName()
        self.assertEqual(auth_name, 'Anonymous User')
        self.login()
        auth_name = getSecurityManager().getUser().getId()
        self.assertEqual(auth_name, user_name)

    def test_login_2(self):
        # A specified user should be logged in
        self.app = self._app()
        self.portal = self._portal()
        self._setupUserFolder()
        self.portal.acl_users.userFolderAddUser('user_2', 'secret', [], [])
        auth_name = getSecurityManager().getUser().getUserName()
        self.assertEqual(auth_name, 'Anonymous User')
        self.login('user_2')
        auth_name = getSecurityManager().getUser().getId()
        self.assertEqual(auth_name, 'user_2')

    def test_login_3(self):
        # Unknown user should raise AttributeError
        self.app = self._app()
        self.portal = self._portal()
        self._setupUserFolder()
        self.assertRaises(AttributeError, self.login, 'user_3')

    def test_logout(self):
        # User should be able to log out
        self.app = self._app()
        self.portal = self._portal()
        self._setupUserFolder()
        self._setupUser()
        self.login()
        self.logout()
        auth_name = getSecurityManager().getUser().getUserName()
        self.assertEqual(auth_name, 'Anonymous User')

    def test_clear(self):
        # Everything should be removed
        self.app = self._app()
        self.portal = self._portal()
        self._setupUserFolder()
        self._setupUser()
        self._setupHomeFolder()
        self._clear(1)
        self.assertFalse(self.app.__dict__.has_key(portal_name))
        auth_name = getSecurityManager().getUser().getUserName()
        self.assertEqual(auth_name, 'Anonymous User')
        self.assertEqual(self._called, ['beforeClose', 'afterClear'])
        # clear must not fail when called repeatedly
        self._clear()

    def test_setUp(self):
        # Everything should be set up
        self._setUp()
        self.assertTrue(hasattr_(self.app, portal_name))
        self.assertTrue(hasattr_(self.portal, 'acl_users'))
        self.assertTrue(hasattr_(self.portal, 'Members'))
        self.assertTrue(hasattr_(self.portal, 'portal_membership'))
        self.assertTrue('Member' in self.portal.userdefined_roles())
        self.assertTrue(hasattr_(self.portal.Members, user_name))
        acl_user = self.portal.acl_users.getUserById(user_name)
        self.assertTrue(acl_user)
        self.assertEqual(acl_user.getRoles(), ('Member', 'Authenticated'))
        self.assertEqual(type(acl_user.roles), ListType)
        auth_name = getSecurityManager().getUser().getId()
        self.assertEqual(auth_name, user_name)
        # XXX: Changed in 0.9.0
        #self.assertEqual(self._called, ['afterClear', 'beforeSetUp', 'afterSetUp'])
        self.assertEqual(self._called, ['beforeSetUp', 'afterSetUp'])

    def test_tearDown(self):
        # Everything should be removed
        self._setUp()
        self._called = []
        self._tearDown()
        self.assertFalse(self.app.__dict__.has_key(portal_name))
        auth_name = getSecurityManager().getUser().getUserName()
        self.assertEqual(auth_name, 'Anonymous User')
        self.assertEqual(self._called, ['beforeTearDown', 'beforeClose', 'afterClear'])

    def test_configureFlag(self):
        # Nothing should be configured
        self._configure_portal = 0
        self._setUp()
        self.assertEqual(self.portal.acl_users.getUserById(user_name), None)
        self.assertFalse(hasattr_(self.portal.Members, user_name))
        auth_name = getSecurityManager().getUser().getUserName()
        self.assertEqual(auth_name, 'Anonymous User')
        # XXX: Changed in 0.9.0
        #self.assertEqual(self._called, ['afterClear', 'beforeSetUp', 'afterSetUp'])
        self.assertEqual(self._called, ['beforeSetUp', 'afterSetUp'])

    def test_createMemberarea(self):
        # Should call the membership tool's createMemberarea
        self.app = self._app()
        self.portal = self._portal()
        self._setupUserFolder()
        self._setupUser()
        self.login()
        self.createMemberarea(user_name)
        self.assertEqual(self.portal.portal_membership._called, ['createMemberarea'])
        self.assertTrue(hasattr_(self.portal.Members, user_name))

    def test_createMemberarea_NewTool(self):
        # Should call the membership tool's createMemberArea
        self.app = self._app()
        self.portal = self._portal()
        self._setupUserFolder()
        self._setupUser()
        self.portal._delObject('portal_membership')
        self.portal._setObject('portal_membership', NewMembershipTool())
        self.login()
        self.createMemberarea(user_name)
        self.assertEqual(self.portal.portal_membership._called, ['createMemberArea'])
        self.assertTrue(hasattr_(self.portal.Members, user_name))

    # Helpers

    def getPermissionsOfRole(self, role, context=None):
        '''Returns sorted list of permission names of the
           given role in the given context.
        '''
        if context is None:
            context = self.portal
        perms = context.permissionsOfRole(role)
        return [p['name'] for p in perms if p['selected']]

    def assertPermissionsOfRole(self, permissions, role, context=None):
        '''Compares list of permission names to permissions of the
           given role in the given context. Fails if the lists are not
           found equal.
        '''
        lhs = list(permissions)[:]
        lhs.sort()
        rhs = self.getPermissionsOfRole(role, context)
        rhs.sort()
        self.assertEqual(lhs, rhs)

    def assertRolesOfUser(self, roles, user):
        '''Compares list of role names to roles of user. Fails if the
           lists are not found equal.
        '''
        lhs = list(roles)[:]
        lhs.sort()
        rhs = list(user.getRoles())[:]
        rhs.remove('Authenticated')
        rhs.sort()
        self.assertEqual(lhs, rhs)


from OFS.userfolder import UserFolder

class WrappingUserFolder(UserFolder):
    '''User folder returning wrapped user objects'''

    def getUser(self, name):
        return UserFolder.getUser(self, name).__of__(self)


class TestPlainUserFolder(ZopeTestCase.PortalTestCase):
    '''Tests whether user objects are properly wrapped'''

    def getPortal(self):
        self.app._setObject(portal_name, DummyPortal(portal_name))
        return getattr(self.app, portal_name)

    def testGetUserDoesNotWrapUser(self):
        user = self.portal.acl_users.getUserById(user_name)
        self.assertFalse(hasattr(user, 'aq_base'))
        self.assertTrue(user is aq_base(user))

    def testLoggedInUserIsWrapped(self):
        user = getSecurityManager().getUser()
        self.assertEqual(user.getId(), user_name)
        self.assertTrue(hasattr(user, 'aq_base'))
        self.assertTrue(user.__class__.__name__, 'User')
        self.assertTrue(user.aq_parent.__class__.__name__, 'UserFolder')
        self.assertTrue(user.aq_parent.aq_parent.__class__.__name__, 'Folder')


class TestWrappingUserFolder(ZopeTestCase.PortalTestCase):
    '''Tests whether user objects are properly wrapped'''

    def getPortal(self):
        self.app._setObject(portal_name, DummyPortal(portal_name))
        return getattr(self.app, portal_name)

    def _setupUserFolder(self):
        self.portal._setObject('acl_users', WrappingUserFolder())

    def testGetUserWrapsUser(self):
        user = self.portal.acl_users.getUserById(user_name)
        self.assertTrue(hasattr(user, 'aq_base'))
        self.assertFalse(user is aq_base(user))
        self.assertTrue(user.aq_parent.__class__.__name__, 'WrappingUserFolder')

    def testLoggedInUserIsWrapped(self):
        user = getSecurityManager().getUser()
        self.assertEqual(user.getId(), user_name)
        self.assertTrue(hasattr(user, 'aq_base'))
        self.assertTrue(user.__class__.__name__, 'User')
        self.assertTrue(user.aq_parent.__class__.__name__, 'WrappingUserFolder')
        self.assertTrue(user.aq_parent.aq_parent.__class__.__name__, 'Folder')


# Because we override setUp we need to test again

class HookTest(ZopeTestCase.PortalTestCase):

    def setUp(self):
        self._called = []
        ZopeTestCase.PortalTestCase.setUp(self)

    def beforeSetUp(self):
        self._called.append('beforeSetUp')
        ZopeTestCase.PortalTestCase.beforeSetUp(self)

    def _setup(self):
        self._called.append('_setup')
        ZopeTestCase.PortalTestCase._setup(self)

    def afterClear(self):
        self._called.append('afterClear')
        ZopeTestCase.PortalTestCase.afterClear(self)

    def assertHooks(self, sequence):
        self.assertEqual(self._called, sequence)


class TestSetUpRaises(HookTest):

    class Error:
        pass

    def getPortal(self):
        self.app._setObject(portal_name, DummyPortal(portal_name))
        return getattr(self.app, portal_name)

    def setUp(self):
        try:
            HookTest.setUp(self)
        except self.Error:
            self.assertHooks(['beforeSetUp', '_setup', 'afterClear'])
            # Connection has been closed
            from Testing.ZopeTestCase import connections
            self.assertEqual(connections.count(), 0)

    def _setup(self):
        HookTest._setup(self)
        raise self.Error

    def testTrigger(self):
        pass


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestPortalTestCase))
    suite.addTest(makeSuite(TestPlainUserFolder))
    suite.addTest(makeSuite(TestWrappingUserFolder))
    suite.addTest(makeSuite(TestSetUpRaises))
    return suite

