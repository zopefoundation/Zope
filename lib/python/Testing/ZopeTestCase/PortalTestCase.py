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

# $Id: PortalTestCase.py,v 1.24 2004/03/29 01:14:14 shh42 Exp $

import ZopeTestCase

from AccessControl import getSecurityManager
from AccessControl.SecurityManagement import newSecurityManager
from Acquisition import aq_base

portal_name = 'portal'
user_name = ZopeTestCase.user_name


class PortalTestCase(ZopeTestCase.ZopeTestCase):
    '''Base test case for testing CMF-style portals

       __implements__ = (IPortalTestCase, ISimpleSecurity, IExtensibleSecurity)

       See doc/IZopeTestCase.py for more.
    '''

    _configure_portal = 1

    def getPortal(self):
        '''Returns the portal object for use by the setup
           code. Will typically be overridden by subclasses
           to return the object serving as the portal.
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
        '''Configures the portal. Framework authors may override.'''
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
        uf._doAddUser(user_name, 'secret', ['Member'], [])

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

    def _clear(self, call_close_hook=0):
        '''Clears the fixture.'''
        # No automagic cleanups here. We rely on
        # transaction abort. Those who commit are
        # required to clean up their own mess.
        if call_close_hook:
            self.beforeClose()
        self._close()
        self.logout()
        self.afterClear()

    # Security interfaces

    def setRoles(self, roles, name=user_name):
        '''Changes the user's roles.'''
        uf = self.portal.acl_users
        uf._doChangeUser(name, None, roles, [])
        if name == getSecurityManager().getUser().getId():
            self.login(name)

    def setPermissions(self, permissions, role='Member'):
        '''Changes the user's permissions.'''
        self.portal.manage_role(role, permissions)

    def login(self, name=user_name):
        '''Logs in.'''
        uf = self.portal.acl_users
        user = uf.getUserById(name)
        if not hasattr(user, 'aq_base'):
            user = user.__of__(uf)
        newSecurityManager(None, user)


# b/w compatibility names
_portal_name = portal_name

