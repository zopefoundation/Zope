#
# Tests the PortalTestCase
#
# NOTE: This is *not* an example PortalTestCase. Do not
# use this file as a blueprint for your own tests!
#
# See testPythonScript.py and testShoppingCart.py for
# example test cases. See testSkeleton.py for a quick
# way of getting started.
#

# $Id: testPortalTestCase.py,v 1.21 2004/04/09 12:38:37 shh42 Exp $

import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

import transaction
from Testing import ZopeTestCase

from Acquisition import aq_base
from AccessControl import getSecurityManager
from types import ListType

portal_name = 'dummy_1_'
user_name = ZopeTestCase.user_name


def hasattr_(ob, attr):
    return hasattr(aq_base(ob), attr)


# Dummy portal
from OFS.SimpleItem import SimpleItem
from OFS.Folder import Folder       

class DummyMembershipTool(SimpleItem):
    id = 'portal_membership'                
    def createMemberarea(self, member_id):      
        portal = self.aq_inner.aq_parent            
        portal.Members.manage_addFolder(member_id)          
    def getHomeFolder(self, member_id):                             
        portal = self.aq_inner.aq_parent
        return portal.Members[member_id]
                  
class DummyPortal(Folder):
    _v_skindata = None                
    def __init__(self, id):
        self.id = id
        self._addRole('Member') 
        self._setObject('portal_membership', DummyMembershipTool())
        self.manage_addFolder('Members')
    def setupCurrentSkin(self):
        if self._v_skindata is None:
            self._v_skindata = 'refreshed'


class TestPortalTestCase(ZopeTestCase.PortalTestCase):
    '''Tests the PortalTestCase.'''

    _setUp = ZopeTestCase.PortalTestCase.setUp
    _tearDown = ZopeTestCase.PortalTestCase.tearDown

    def getPortal(self):
        self.app._setObject(portal_name, DummyPortal(portal_name))
        return self.app[portal_name]

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

    def test_01_getPortal(self):
        # Portal should be set up
        self.app = self._app()
        self.portal = self.getPortal()
        self.failUnless(hasattr_(self.app, portal_name))
        self.failUnless(hasattr_(self.portal, 'Members'))
        self.failUnless(hasattr_(self.portal, 'portal_membership'))
        self.failUnless('Member' in self.portal.userdefined_roles())

    def test_02_setupUserFolder(self):
        # User folder should be set up.
        self.app = self._app()
        self.portal = self.getPortal()
        self.failIf(hasattr_(self.portal, 'acl_users'))
        self._setupUserFolder()
        self.failUnless(hasattr_(self.portal, 'acl_users'))
        # Must not complain if UF already exists
        self._setupUserFolder()

    def test_03_setupUser(self):
        # User should be set up
        self.app = self._app()
        self.portal = self.getPortal()
        self._setupUserFolder()
        self._setupUser()
        acl_user = self.portal.acl_users.getUserById(user_name)
        self.failUnless(acl_user)
        self.assertEqual(acl_user.getRoles(), ('Member', 'Authenticated'))
        self.assertEqual(type(acl_user.roles), ListType)

    def test_04_setupHomeFolder(self):
        # User's home folder should be set up
        self.app = self._app()
        self.portal = self.getPortal()
        self._setupUserFolder()
        self._setupUser()
        self.login()
        self._setupHomeFolder()
        self.failUnless(hasattr_(self.portal.Members, user_name))
        self.failIf(self.folder is None)
        # Shut up deprecation warnings
        try: owner_info = self.folder.getOwnerTuple()
        except AttributeError:
            owner_info = self.folder.getOwner(info=1)
        self.assertEqual(owner_info, ([portal_name, 'acl_users'], user_name))

    def test_05_refreshSkinData(self):
        # The _v_skindata attribute should be refreshed
        self.app = self._app()
        self.portal = self.getPortal()
        self.assertEqual(self.portal._v_skindata, None)
        self._refreshSkinData()
        self.assertEqual(self.portal._v_skindata, 'refreshed')

    def test_06_setRoles(self):
        # Roles should be set for user
        self.app = self._app()
        self.portal = self.getPortal()
        self._setupUserFolder()
        self._setupUser()
        test_roles = ['Manager', 'Member']
        test_roles.sort()
        self.setRoles(test_roles)
        acl_user = self.portal.acl_users.getUserById(user_name)
        user_roles = list(acl_user.getRoles())
        user_roles.remove('Authenticated')
        user_roles.sort()
        self.assertEqual(user_roles, test_roles)

    def test_07_setRoles_2(self):
        # Roles should be set for logged in user
        self.app = self._app()
        self.portal = self.getPortal()
        self._setupUserFolder()
        self._setupUser()
        self.login()
        test_roles = ['Manager', 'Member']
        test_roles.sort()
        self.setRoles(test_roles)
        auth_user = getSecurityManager().getUser()
        user_roles = list(auth_user.getRoles())
        user_roles.remove('Authenticated')
        user_roles.sort()
        self.assertEqual(user_roles, test_roles)

    def test_08_setRoles_3(self):
        # Roles should be set for a specified user
        self.app = self._app()
        self.portal = self.getPortal()
        self._setupUserFolder()
        self.portal.acl_users._doAddUser('test_user_2_', 'secret', [], [])
        test_roles = ['Manager', 'Member']
        test_roles.sort()
        self.setRoles(test_roles, 'test_user_2_')
        acl_user = self.portal.acl_users.getUserById('test_user_2_')
        user_roles = list(acl_user.getRoles())
        user_roles.remove('Authenticated')
        user_roles.sort()
        self.assertEqual(user_roles, test_roles)

    def test_09_setPermissions(self):
        # Permissions should be set for user
        self.app = self._app()
        self.portal = self.getPortal()
        test_perms = ['Add Folders']
        self.setPermissions(test_perms)
        self.assertPermissionsOfRole(test_perms, 'Member')

    def test_10_setPermissions_2(self):
        # Permissions should be set for a specified role
        self.app = self._app()
        self.portal = self.getPortal()
        self.portal._addRole('test_role_2_')
        test_perms = ['Add Folders']
        self.assertPermissionsOfRole([], 'test_role_2_')
        self.setPermissions(test_perms, 'test_role_2_')
        self.assertPermissionsOfRole(test_perms, 'test_role_2_')

    def test_11_login(self):
        # User should be able to log in
        self.app = self._app()
        self.portal = self.getPortal()
        self._setupUserFolder()
        self._setupUser()
        auth_name = getSecurityManager().getUser().getUserName()
        self.assertEqual(auth_name, 'Anonymous User')
        self.login()
        auth_name = getSecurityManager().getUser().getId()
        self.assertEqual(auth_name, user_name)

    def test_12_login_2(self):
        # A specified user should be logged in
        self.app = self._app()
        self.portal = self.getPortal()
        self._setupUserFolder()
        self.portal.acl_users._doAddUser('test_user_2_', 'secret', [], [])
        auth_name = getSecurityManager().getUser().getUserName()
        self.assertEqual(auth_name, 'Anonymous User')
        self.login('test_user_2_')
        auth_name = getSecurityManager().getUser().getId()
        self.assertEqual(auth_name, 'test_user_2_')

    def test_13_login_3(self):
        # Unknown user should raise AttributeError
        self.app = self._app()
        self.portal = self.getPortal()
        self._setupUserFolder()
        self.assertRaises(AttributeError, self.login, 'test_user_3_')

    def test_14_logout(self):
        # User should be able to log out
        self.app = self._app()
        self.portal = self.getPortal()
        self._setupUserFolder()
        self._setupUser()
        self.login()
        self.logout()
        auth_name = getSecurityManager().getUser().getUserName()
        self.assertEqual(auth_name, 'Anonymous User')

    def test_15_clear(self):
        # Everything should be removed
        self.app = self._app()
        self.portal = self.getPortal()
        self._setupUserFolder()
        self._setupUser()
        self._setupHomeFolder()
        self._clear(1)
        # XXX: No more cleanups in _clear()
        #self.failIf(self.portal.acl_users.getUserById(user_name))
        #self.failIf(hasattr_(self.portal.Members, user_name))
        auth_name = getSecurityManager().getUser().getUserName()
        self.assertEqual(auth_name, 'Anonymous User')
        self.assertEqual(self._called, ['beforeClose', 'afterClear'])
        # clear must not fail when called repeatedly
        self._clear()

    def test_16_setUp(self):
        # Everything should be set up
        self._setUp()
        self.failUnless(hasattr_(self.app, portal_name))
        self.failUnless(hasattr_(self.portal, 'acl_users'))
        self.failUnless(hasattr_(self.portal, 'Members'))
        self.failUnless(hasattr_(self.portal, 'portal_membership'))
        self.failUnless('Member' in self.portal.userdefined_roles())
        self.failUnless(hasattr_(self.portal.Members, user_name))
        acl_user = self.portal.acl_users.getUserById(user_name)
        self.failUnless(acl_user)
        self.assertEqual(acl_user.getRoles(), ('Member', 'Authenticated'))
        self.assertEqual(type(acl_user.roles), ListType)
        auth_name = getSecurityManager().getUser().getId()
        self.assertEqual(auth_name, user_name)
        # XXX: Changed in 0.9.0
        #self.assertEqual(self._called, ['afterClear', 'beforeSetUp', 'afterSetUp'])
        self.assertEqual(self._called, ['beforeSetUp', 'afterSetUp'])
        self.assertEqual(self.portal._v_skindata, 'refreshed')

    def test_17_tearDown(self):
        # Everything should be removed
        self._setUp()
        self._called = []
        self._tearDown()
        # XXX: No more cleanups in _clear()
        #self.failIf(hasattr_(self.portal.Members, user_name))
        #self.assertEqual(self.portal.acl_users.getUserById(user_name), None)
        auth_name = getSecurityManager().getUser().getUserName()
        self.assertEqual(auth_name, 'Anonymous User')
        self.assertEqual(self._called, ['beforeTearDown', 'beforeClose', 'afterClear'])

    def test_18_configureFlag(self):
        # Nothing should be configured
        self._configure_portal = 0
        self._setUp()
        self.assertEqual(self.portal.acl_users.getUserById(user_name), None)
        self.failIf(hasattr_(self.portal.Members, user_name))
        auth_name = getSecurityManager().getUser().getUserName()
        self.assertEqual(auth_name, 'Anonymous User')
        # XXX: Changed in 0.9.0
        #self.assertEqual(self._called, ['afterClear', 'beforeSetUp', 'afterSetUp'])
        self.assertEqual(self._called, ['beforeSetUp', 'afterSetUp'])
        self.assertEqual(self.portal._v_skindata, 'refreshed')

    def test_19_configureFlag_2(self):
        # Nothing should be cleared
        self._setUp()
        self._configure_portal = 0
        self._called = []
        self._clear()
        # XXX: Since 0.8.4 we abort before closing the connection
        #self.failUnless(hasattr_(self.portal.Members, user_name))
        #self.failUnless(self.portal.acl_users.getUserById(user_name))
        auth_name = getSecurityManager().getUser().getUserName()
        self.assertEqual(auth_name, 'Anonymous User')
        self.assertEqual(self._called, ['afterClear'])

    # Helpers

    def getPermissionsOfRole(self, role, context=None):
        '''Returns sorted list of permission names of the
           given role in the given context.
        '''
        if context is None: context = self.portal
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


from AccessControl.User import UserFolder

class WrappingUserFolder(UserFolder):
    '''User folder returning wrapped user objects'''

    def getUser(self, name):
        return UserFolder.getUser(self, name).__of__(self)


class TestPlainUserFolder(ZopeTestCase.PortalTestCase):
    '''Tests whether user objects are properly wrapped'''

    def getPortal(self):
        self.app._setObject(portal_name, DummyPortal(portal_name))
        return self.app[portal_name]

    def testGetUserDoesNotWrapUser(self):
        user = self.portal.acl_users.getUserById(user_name)
        self.failIf(hasattr(user, 'aq_base'))
        self.failUnless(user is aq_base(user))

    def testLoggedInUserIsWrapped(self):
        user = getSecurityManager().getUser()
        self.assertEqual(user.getId(), user_name)
        self.failUnless(hasattr(user, 'aq_base'))
        self.failUnless(user.__class__.__name__, 'User')
        self.failUnless(user.aq_parent.__class__.__name__, 'UserFolder')
        self.failUnless(user.aq_parent.aq_parent.__class__.__name__, 'Folder')


class TestWrappingUserFolder(ZopeTestCase.PortalTestCase):
    '''Tests whether user objects are properly wrapped'''

    def getPortal(self):
        self.app._setObject(portal_name, DummyPortal(portal_name))
        return self.app[portal_name]

    def _setupUserFolder(self):
        self.portal._setObject('acl_users', WrappingUserFolder())

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


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestPortalTestCase))
    suite.addTest(makeSuite(TestPlainUserFolder))
    suite.addTest(makeSuite(TestWrappingUserFolder))
    return suite

if __name__ == '__main__':
    framework()

