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
"""Default test case & fixture for Zope testing

The fixture consists of:

  - a folder (self.folder)
  - a user folder inside that folder
  - a default user inside the user folder

The default user is logged in and has the 'Access contents information'
and 'View' permissions given to his role.
"""

import base
import functional
import interfaces
import utils
import connections

from zope.interface import implements
from AccessControl import getSecurityManager
from AccessControl.SecurityManagement import newSecurityManager
from AccessControl.SecurityManagement import noSecurityManager
from AccessControl.Permissions import access_contents_information
from AccessControl.Permissions import view

folder_name = 'test_folder_1_'
user_name = 'test_user_1_'
user_password = 'secret'
user_role = 'test_role_1_'
standard_permissions = [access_contents_information, view]


class ZopeTestCase(base.TestCase):
    '''Base test case for Zope testing'''

    implements(interfaces.IZopeSecurity)

    _setup_fixture = 1

    def _setup(self):
        '''Sets up the fixture. Framework authors may
           override.
        '''
        if self._setup_fixture:
            self._setupFolder()
            self._setupUserFolder()
            self._setupUser()
            self.login()

    def _setupFolder(self):
        '''Creates and configures the folder.'''
        from OFS.Folder import manage_addFolder
        manage_addFolder(self.app, folder_name)
        self.folder = getattr(self.app, folder_name)
        self.folder._addRole(user_role)
        self.folder.manage_role(user_role, standard_permissions)

    def _setupUserFolder(self):
        '''Creates the user folder.'''
        from OFS.userfolder import manage_addUserFolder
        manage_addUserFolder(self.folder)

    def _setupUser(self):
        '''Creates the default user.'''
        uf = self.folder.acl_users
        uf.userFolderAddUser(user_name, user_password, [user_role], [])

    def _clear(self, call_close_hook=0):
        '''Clears the fixture.'''
        # This code is a wart from the olden days.
        try:
            if connections.contains(self.app):
                self.app._delObject(folder_name)
        except:
            pass
        base.TestCase._clear(self, call_close_hook)

    # Security interface

    def setRoles(self, roles, name=user_name):
        '''Changes the user's roles.'''
        uf = self.folder.acl_users
        uf.userFolderEditUser(name, None, utils.makelist(roles), [])
        if name == getSecurityManager().getUser().getId():
            self.login(name)

    def setPermissions(self, permissions, role=user_role):
        '''Changes the user's permissions.'''
        self.folder.manage_role(role, utils.makelist(permissions))

    def login(self, name=user_name):
        '''Logs in.'''
        uf = self.folder.acl_users
        user = uf.getUserById(name)
        if not hasattr(user, 'aq_base'):
            user = user.__of__(uf)
        newSecurityManager(None, user)

    def logout(self):
        '''Logs out.'''
        noSecurityManager()


class FunctionalTestCase(functional.Functional, ZopeTestCase):
    '''Convenience base class for functional Zope tests

       You can mix-in Functional with every xTestCase
       to turn it into a functional test case.
    '''


from base import app
from base import close

