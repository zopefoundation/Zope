#
# Abstract base test case for working with CMF-style portals
#
# This base class maintains a fixture consisting of:
#
#   - a portal object (self.portal)
#   - a user folder inside the portal
#   - a default user with role 'Member' inside the user folder
#   - the default user's memberarea (self.folder)
#   - the default user is logged in
#
# The twist is that the portal object itself is *not* created
# by the PortalTestCase class! Subclasses must make sure
# getPortal() returns a usable portal object to the setup code.
#

# $Id: PortalTestCase.py,v 1.29 2004/09/09 18:48:59 shh42 Exp $

import base
import types

from AccessControl import getSecurityManager
from AccessControl.SecurityManagement import newSecurityManager
from AccessControl.SecurityManagement import noSecurityManager
from Acquisition import aq_base

portal_name = 'portal'
from ZopeTestCase import user_name
from ZopeTestCase import user_password


class PortalTestCase(base.TestCase):
    '''Base test case for testing CMF-style portals

       __implements__ = (IPortalTestCase, ISimpleSecurity, IExtensibleSecurity)

       See doc/IZopeTestCase.py for more.
    '''

    _configure_portal = 1

    def getPortal(self):
        '''Returns the portal object to the setup code.
           Will typically be overridden by subclasses
           to return the object serving as the "portal".

           Note: This method should not be called by tests!
        '''
        return self.app[portal_name]

    def createMemberarea(self, member_id):
        '''Creates a memberarea for the specified member. 
           Subclasses may override to provide a customized
           or more lightweight version of the memberarea.
        '''
        pm = self.portal.portal_membership
        pm.createMemberarea(member_id)

    def setUp(self):
        '''Sets up the fixture. Do not override,
           use the hooks instead.
        '''
        try:
            self.beforeSetUp()
            self.app = self._app()
            self.portal = self.getPortal()
            self._setup()
            self._refreshSkinData()
            self.afterSetUp()
        except:
            self._clear()
            raise

    def _setup(self):
        '''Configures the portal. Framework authors may
           override.
        '''
        if self._configure_portal:
            self._setupUserFolder()
            self._setupUser()
            self.login()
            self._setupHomeFolder()

    def _setupUserFolder(self):
        '''Creates the user folder if missing.'''
        if not hasattr(aq_base(self.portal), 'acl_users'):
            self.portal.manage_addUserFolder()

    def _setupUser(self):
        '''Creates the default user.'''
        uf = self.portal.acl_users
        uf.userFolderAddUser(user_name, user_password, ['Member'], [])

    def _setupHomeFolder(self):
        '''Creates the default user's home folder.'''
        self.createMemberarea(user_name)
        pm = self.portal.portal_membership
        self.folder = pm.getHomeFolder(user_name)

    def _refreshSkinData(self):
        '''Refreshes the magic _v_skindata attribute.'''
        if hasattr(self.portal, '_v_skindata'):
            self.portal._v_skindata = None
        if hasattr(self.portal, 'setupCurrentSkin'):
            self.portal.setupCurrentSkin()

    # Security interfaces

    def setRoles(self, roles, name=user_name):
        '''Changes the user's roles.'''
        self.assertEqual(type(roles), types.ListType)
        uf = self.portal.acl_users
        uf.userFolderEditUser(name, None, roles, [])
        if name == getSecurityManager().getUser().getId():
            self.login(name)

    def getRoles(self, name=user_name):
        '''Returns the user's roles.'''
        uf = self.portal.acl_users
        return uf.getUserById(name).getRoles()

    def setPermissions(self, permissions, role='Member'):
        '''Changes the permissions assigned to role.'''
        self.assertEqual(type(permissions), types.ListType)
        self.portal.manage_role(role, permissions)

    def getPermissions(self, role='Member'):
        '''Returns the permissions assigned to role.'''
        perms = self.portal.permissionsOfRole(role)
        return [p['name'] for p in perms if p['selected']]

    def login(self, name=user_name):
        '''Logs in.'''
        uf = self.portal.acl_users
        user = uf.getUserById(name)
        if not hasattr(user, 'aq_base'):
            user = user.__of__(uf)
        newSecurityManager(None, user)

    def logout(self):
        '''Logs out.'''
        noSecurityManager()

    # b/w compatibility methods

    def _setRoles(self, roles, name=user_name):
        self.setRoles(roles, name)
    def _setPermissions(self, permissions, role='Member'):
        self.setPermissions(permissions, role)
    def _login(self, name=user_name):
        self.login(name)
    def _logout(self):
        self.logout()


# b/w compatibility names
_portal_name = portal_name

