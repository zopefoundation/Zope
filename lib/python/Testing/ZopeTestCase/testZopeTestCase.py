#
# Tests the ZopeTestCase, eating its own dogfood
#
# NOTE: This is *not* an example ZopeTestCase. Do not
# use this file as a blueprint for your own tests!
#
# See testPythonScript.py and testShoppingCart.py for
# example test cases. See testSkeleton.py for a quick
# way of getting started.
#

# $Id: testZopeTestCase.py,v 1.17 2004/04/09 12:38:37 shh42 Exp $

import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

import transaction
from Testing import ZopeTestCase

from Acquisition import aq_base
from AccessControl import getSecurityManager
from types import ListType

folder_name = ZopeTestCase.folder_name
user_name = ZopeTestCase.user_name
user_role = ZopeTestCase.user_role
standard_permissions = ZopeTestCase.standard_permissions


def hasattr_(ob, attr):
    return hasattr(aq_base(ob), attr)


class TestZopeTestCase(ZopeTestCase.ZopeTestCase):
    '''Incrementally exercise the ZopeTestCase API.
       Exploit the fact that tests are sorted by name.
    '''

    _setUp = ZopeTestCase.ZopeTestCase.setUp
    _tearDown = ZopeTestCase.ZopeTestCase.tearDown

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

    def test_01_setupFolder(self):
        # Folder should be set up
        self.app = self._app()
        self._setupFolder()
        self.failUnless(hasattr_(self.app, folder_name))
        self.failUnless(hasattr(self, 'folder'))
        self.failUnless(user_role in self.folder.userdefined_roles())
        self.assertPermissionsOfRole(standard_permissions, user_role)

    def test_02_setupUserFolder(self):
        # User folder should be set up
        self.app = self._app()
        self._setupFolder()
        self._setupUserFolder()
        self.failUnless(hasattr_(self.folder, 'acl_users'))

    def test_03_setupUser(self):
        # User should be set up
        self.app = self._app()
        self._setupFolder()
        self._setupUserFolder()
        self._setupUser()
        acl_user = self.folder.acl_users.getUserById(user_name)
        self.failUnless(acl_user)
        self.assertEqual(acl_user.getRoles(), (user_role, 'Authenticated'))
        self.assertEqual(type(acl_user.roles), ListType)

    def test_04_setRoles(self):
        # Roles should be set for user
        self.app = self._app()
        self._setupFolder()
        self._setupUserFolder()
        self._setupUser()
        test_roles = ['Manager', user_role]
        test_roles.sort()
        self.setRoles(test_roles)
        acl_user = self.folder.acl_users.getUserById(user_name)
        user_roles = list(acl_user.getRoles())
        user_roles.remove('Authenticated')
        user_roles.sort()
        self.assertEqual(user_roles, test_roles)

    def test_05_setRoles_2(self):
        # Roles of logged in user should be updated
        self.app = self._app()
        self._setupFolder()
        self._setupUserFolder()
        self._setupUser()
        self.login()
        test_roles = ['Manager', user_role]
        test_roles.sort()
        self.setRoles(test_roles)
        auth_user = getSecurityManager().getUser()
        user_roles = list(auth_user.getRoles())
        user_roles.remove('Authenticated')
        user_roles.sort()
        self.assertEqual(user_roles, test_roles)

    def test_06_setRoles_3(self):
        # Roles should be set for a specified user
        self.app = self._app()
        self._setupFolder()
        self._setupUserFolder()
        self.folder.acl_users._doAddUser('test_user_2_', 'secret', [], [])
        test_roles = ['Manager', user_role]
        test_roles.sort()
        self.setRoles(test_roles, 'test_user_2_')
        acl_user = self.folder.acl_users.getUserById('test_user_2_')
        user_roles = list(acl_user.getRoles())
        user_roles.remove('Authenticated')
        user_roles.sort()
        self.assertEqual(user_roles, test_roles)

    def test_07_setPermissions(self):
        # Permissions should be set for user
        self.app = self._app()
        self._setupFolder()
        test_perms = standard_permissions + ['Add Folders']
        self.assertPermissionsOfRole(standard_permissions, user_role)
        self.setPermissions(test_perms)
        self.assertPermissionsOfRole(test_perms, user_role)

    def test_08_setPermissions_2(self):
        # Permissions should be set for a specified role
        self.app = self._app()
        self._setupFolder()
        self.folder._addRole('test_role_2_')
        self.assertPermissionsOfRole([], 'test_role_2_')
        self.setPermissions(standard_permissions, 'test_role_2_')
        self.assertPermissionsOfRole(standard_permissions, 'test_role_2_')

    def test_09_login(self):
        # User should be able to log in
        self.app = self._app()
        self._setupFolder()
        self._setupUserFolder()
        self._setupUser()
        auth_name = getSecurityManager().getUser().getUserName()
        self.assertEqual(auth_name, 'Anonymous User')
        self.login()
        auth_name = getSecurityManager().getUser().getId()
        self.assertEqual(auth_name, user_name)

    def test_10_login_2(self):
        # A specified user should be logged in
        self.app = self._app()
        self._setupFolder()
        self._setupUserFolder()
        self.folder.acl_users._doAddUser('test_user_2_', 'secret', [], [])
        auth_name = getSecurityManager().getUser().getUserName()
        self.assertEqual(auth_name, 'Anonymous User')
        self.login('test_user_2_')
        auth_name = getSecurityManager().getUser().getId()
        self.assertEqual(auth_name, 'test_user_2_')

    def test_11_login_3(self):
        # Unknown user should raise AttributeError
        self.app = self._app()
        self._setupFolder()
        self._setupUserFolder()
        self.assertRaises(AttributeError, self.login, 'test_user_3_')

    def test_12_logout(self):
        # User should be able to log out
        self.app = self._app()
        self._setupFolder()
        self._setupUserFolder()
        self._setupUser()
        self.login()
        self.logout()
        auth_name = getSecurityManager().getUser().getUserName()
        self.assertEqual(auth_name, 'Anonymous User')

    def test_13_clear(self):
        # Everything should be removed
        self.app = self._app()
        self._setupFolder()
        self._setupUserFolder()
        self._setupUser()
        self._clear(1)
        self.failIf(hasattr_(self.app, folder_name))
        auth_name = getSecurityManager().getUser().getUserName()
        self.assertEqual(auth_name, 'Anonymous User')
        self.assertEqual(self._called, ['beforeClose', 'afterClear'])
        # _clear must not fail when called repeatedly
        self._clear()

    def test_14_setUp(self):
        # Everything should be set up
        self._setUp()
        self.failUnless(hasattr_(self.app, folder_name))
        self.failUnless(hasattr(self, 'folder'))
        self.failUnless(user_role in self.folder.userdefined_roles())
        self.assertPermissionsOfRole(standard_permissions, user_role)
        self.failUnless(hasattr_(self.folder, 'acl_users'))
        acl_user = self.folder.acl_users.getUserById(user_name)
        self.failUnless(acl_user)
        self.assertEqual(acl_user.getRoles(), (user_role, 'Authenticated'))
        self.assertEqual(type(acl_user.roles), ListType)
        auth_name = getSecurityManager().getUser().getId()
        self.assertEqual(auth_name, user_name)
        # XXX: Changed in 0.9.0
        #self.assertEqual(self._called, ['afterClear', 'beforeSetUp', 'afterSetUp'])
        self.assertEqual(self._called, ['beforeSetUp', 'afterSetUp'])

    def test_15_tearDown(self):
        # Everything should be removed
        self._setUp()
        self._called = []
        self._tearDown()
        self.failIf(hasattr_(self.app, folder_name))
        auth_name = getSecurityManager().getUser().getUserName()
        self.assertEqual(auth_name, 'Anonymous User')
        self.assertEqual(self._called, ['beforeTearDown', 'beforeClose', 'afterClear'])

    def test_16_setupFlag(self):
        # Nothing should be set up
        self._setup_fixture = 0
        self._setUp()
        self.failIf(hasattr_(self.app, folder_name))
        auth_name = getSecurityManager().getUser().getUserName()
        self.assertEqual(auth_name, 'Anonymous User')
        # XXX: Changed in 0.9.0
        #self.assertEqual(self._called, ['afterClear', 'beforeSetUp', 'afterSetUp'])
        self.assertEqual(self._called, ['beforeSetUp', 'afterSetUp'])

    def test_17_setupFlag_2(self):
        # Nothing should be cleared
        self._setUp()
        self._setup_fixture = 0
        self._called = []
        self._clear()
        # XXX: Since 0.8.4 we abort before closing the connection
        #self.failUnless(hasattr_(self.app, folder_name))
        auth_name = getSecurityManager().getUser().getUserName()
        self.assertEqual(auth_name, 'Anonymous User')
        self.assertEqual(self._called, ['afterClear'])

    # Bug tests

    def test_18_setOwnerPermissions(self):
        # Permissions should be modified for the Owner role
        self.app = self._app()
        self._setupFolder()
        self.assertPermissionsOfRole([], 'Owner')
        self.setPermissions(standard_permissions, 'Owner')
        self.assertPermissionsOfRole(standard_permissions, 'Owner')

    def test_19_setManagerPermissions(self):
        # Permissions should *not* be modified for the Manager role
        self.app = self._app()
        self._setupFolder()
        # Setting permissions for Manager role does not work like this
        manager_perms = self.getPermissionsOfRole('Manager')
        self.setPermissions(standard_permissions, 'Manager')
        # Manager does still have all permissions
        self.assertPermissionsOfRole(manager_perms, 'Manager')

    def test_20_setManagerPermissions_2(self):
        # Permissions should be modified for the Manager role
        self.app = self._app()
        self._setupFolder()
        # However, it works like that (because we turn off acquisition?)
        manager_perms = self.getPermissionsOfRole('Manager')
        self.folder.manage_permission('Take ownership', ['Owner'], acquire=0)
        self.assertPermissionsOfRole(['Take ownership'], 'Owner')
        # Manager does not have 'Take ownership' anymore
        manager_perms.remove('Take ownership')
        self.assertPermissionsOfRole(manager_perms, 'Manager')

    # Helpers

    def getPermissionsOfRole(self, role, context=None):
        '''Returns sorted list of permission names of the
           given role in the given context.
        '''
        if context is None: context = self.folder
        perms = context.permissionsOfRole(role)
        perms = [p['name'] for p in perms if p['selected']]
        perms.sort()
        return perms

    def assertPermissionsOfRole(self, permissions, role, context=None):
        '''Compares list of permission names to permissions of the
           given role in the given context. Fails if the lists are not
           found equal.
        '''
        perms = list(permissions)[:]
        perms.sort()
        self.assertEqual(self.getPermissionsOfRole(role, context), perms)


import unittest

class TestConnectionRegistry(unittest.TestCase):
    '''Tests the ZODB connection registry'''

    class Conn:
        closed = 0
        def close(self):
            self.closed = 1

    def setUp(self):
        self.reg = ZopeTestCase.utils.ConnectionRegistry()
        self.conns = [self.Conn(), self.Conn(), self.Conn()]

    def testRegister(self):
        # Should be able to register connections
        for conn in self.conns:
            self.reg.register(conn)
        assert len(self.reg) == 3

    def testCloseConnection(self):
        # Should be able to close a single registered connection
        for conn in self.conns:
            self.reg.register(conn)
        assert len(self.reg) == 3
        self.reg.close(self.conns[0])
        assert len(self.reg) == 2
        assert self.conns[0].closed == 1
        assert self.conns[1].closed == 0
        assert self.conns[2].closed == 0

    def testCloseSeveralConnections(self):
        # Should be able to close all registered connections one-by-one
        for conn in self.conns:
            self.reg.register(conn)
        assert len(self.reg) == 3
        self.reg.close(self.conns[0])
        assert len(self.reg) == 2
        assert self.conns[0].closed == 1
        assert self.conns[1].closed == 0
        assert self.conns[2].closed == 0
        self.reg.close(self.conns[2])
        assert len(self.reg) == 1
        assert self.conns[0].closed == 1
        assert self.conns[1].closed == 0
        assert self.conns[2].closed == 1
        self.reg.close(self.conns[1])
        assert len(self.reg) == 0
        assert self.conns[0].closed == 1
        assert self.conns[1].closed == 1
        assert self.conns[2].closed == 1

    def testCloseForeignConnection(self):
        # Should be able to close a connection that has not been registered
        for conn in self.conns:
            self.reg.register(conn)
        assert len(self.reg) == 3
        conn = self.Conn()
        self.reg.close(conn)
        assert len(self.reg) == 3
        assert self.conns[0].closed == 0
        assert self.conns[1].closed == 0
        assert self.conns[2].closed == 0
        assert conn.closed == 1

    def testCloseAllConnections(self):
        # Should be able to close all registered connections at once
        for conn in self.conns:
            self.reg.register(conn)
        assert len(self.reg) == 3
        self.reg.closeAll()
        assert len(self.reg) == 0
        assert self.conns[0].closed == 1
        assert self.conns[1].closed == 1
        assert self.conns[2].closed == 1


from AccessControl.User import UserFolder
from Acquisition import aq_inner, aq_parent, aq_chain

class WrappingUserFolder(UserFolder):
    '''User folder returning wrapped user objects'''

    def getUser(self, name):
        return UserFolder.getUser(self, name).__of__(self)


class TestPlainUserFolder(ZopeTestCase.ZopeTestCase):
    '''Tests whether user objects are properly wrapped'''

    def testGetUserDoesNotWrapUser(self):
        user = self.folder.acl_users.getUserById(user_name)
        self.failIf(hasattr(user, 'aq_base'))
        self.failUnless(user is aq_base(user))

    def testLoggedInUserIsWrapped(self):
        user = getSecurityManager().getUser()
        self.assertEqual(user.getId(), user_name)
        self.failUnless(hasattr(user, 'aq_base'))
        self.failUnless(user.__class__.__name__, 'User')
        self.failUnless(user.aq_parent.__class__.__name__, 'UserFolder')
        self.failUnless(user.aq_parent.aq_parent.__class__.__name__, 'Folder')


class TestWrappingUserFolder(ZopeTestCase.ZopeTestCase):
    '''Tests whether user objects are properly wrapped'''

    def _setupUserFolder(self):
        self.folder._setObject('acl_users', WrappingUserFolder())

    def testGetUserWrapsUser(self):
        user = self.folder.acl_users.getUserById(user_name)
        self.failUnless(hasattr(user, 'aq_base'))
        self.failIf(user is aq_base(user))
        self.failUnless(user.aq_parent.__class__.__name__, 'WrappingUserFolder')

    def testLoggedInUserIsWrapped(self):
        user = getSecurityManager().getUser()
        self.assertEqual(user.getId(), user_name)
        self.failUnless(hasattr(user, 'aq_base'))
        self.failUnless(user.__class__.__name__, 'User')
        self.failUnless(user.aq_parent.__class__.__name__, 'WrappingUserFolder')
        self.failUnless(user.aq_parent.aq_parent.__class__.__name__, 'Folder')


class TestRequestVariables(ZopeTestCase.ZopeTestCase):
    '''Makes sure the REQUEST contains required variables'''

    def testRequestVariables(self):
        request = self.app.REQUEST
        self.failIfEqual(request.get('SERVER_NAME', ''), '')
        self.failIfEqual(request.get('SERVER_PORT', ''), '')
        self.failIfEqual(request.get('REQUEST_METHOD', ''), '')
        self.failIfEqual(request.get('URL', ''), '')
        self.failIfEqual(request.get('SERVER_URL', ''), '')
        self.failIfEqual(request.get('URL0', ''), '')
        self.failIfEqual(request.get('URL1', ''), '')
        self.failIfEqual(request.get('BASE0', ''), '')
        self.failIfEqual(request.get('BASE1', ''), '')
        self.failIfEqual(request.get('BASE2', ''), '')


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestZopeTestCase))
    suite.addTest(makeSuite(TestConnectionRegistry))
    suite.addTest(makeSuite(TestPlainUserFolder))
    suite.addTest(makeSuite(TestWrappingUserFolder))
    suite.addTest(makeSuite(TestRequestVariables))
    return suite

if __name__ == '__main__':
    framework()

