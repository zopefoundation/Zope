#
# Default test case & fixture for Zope testing
#
# The fixture consists of:
#
#   - a folder (self.folder)
#   - a user folder inside that folder
#   - a default user inside the user folder
#
# The default user is logged in and has the 'Access contents information'
# and 'View' permissions given to his role.
#

# $Id: ZopeTestCase.py,v 1.15 2004/03/29 01:14:13 shh42 Exp $

import ZopeLite as Zope

import unittest
import utils
import profiler

import transaction
from AccessControl import getSecurityManager
from AccessControl.SecurityManagement import newSecurityManager
from AccessControl.SecurityManagement import noSecurityManager
from AccessControl.Permissions import access_contents_information
from AccessControl.Permissions import view

folder_name = 'test_folder_1_'
user_name = 'test_user_1_'
user_role = 'test_role_1_'
standard_permissions = [access_contents_information, view]

_connections = utils.ConnectionRegistry()



def app():
    '''Opens a ZODB connection and returns the app object.'''
    app = Zope.app()
    _connections.register(app._p_jar)
    return utils.makerequest(app)

def close(app):
    '''Closes the app's ZODB connection.'''
    _connections.close(app._p_jar)

def closeConnections():
    '''Closes all registered ZODB connections.'''
    _connections.closeAll()



class ZopeTestCase(profiler.Profiled, unittest.TestCase):
    '''Base test case for Zope testing

       __implements__ = (IZopeTestCase, ISimpleSecurity, IExtensibleSecurity)

       See doc/IZopeTestCase.py for more
    '''

    _setup_fixture = 1

    def afterSetUp(self):
        '''Called after setUp() has completed. This is
           far and away the most useful hook.
        '''
        pass

    def beforeTearDown(self):
        '''Called before tearDown() is executed.
           Note that tearDown() is not called if
           setUp() fails.
        '''
        pass

    def afterClear(self):
        '''Called after the fixture has been cleared.
           Note that this may occur during setUp() *and*
           tearDown().
        '''
        pass

    def beforeSetUp(self):
        '''Called before the ZODB connection is opened,
           at the start of setUp(). By default begins
           a new transaction.
        '''
        transaction.begin()

    def beforeClose(self):
        '''Called before the ZODB connection is closed,
           at the end of tearDown(). By default aborts
           the transaction.
        '''
        get_transaction().abort()

    def setUp(self):
        '''Sets up the fixture. Do not override,
           use the hooks instead.
        '''
        try:
            self.beforeSetUp()
            self.app = self._app()
            self._setup()
            self.afterSetUp()
        except:
            self._clear()
            raise

    def tearDown(self):
        '''Tears down the fixture. Do not override,
           use the hooks instead.
        '''
        try:
            self.beforeTearDown()
            self._clear(1)
        except:
            self._clear()
            raise

    def _app(self):
        '''Returns the app object for a test.'''
        return app()

    def _setup(self):
        '''Sets up the fixture. Framework authors may override.'''
        if self._setup_fixture:
            self._setupFolder()
            self._setupUserFolder()
            self._setupUser()
            self.login()

    def _setupFolder(self):
        '''Creates and configures the folder.'''
        self.app.manage_addFolder(folder_name)
        self.folder = self.app._getOb(folder_name)
        self.folder._addRole(user_role)
        self.folder.manage_role(user_role, standard_permissions)

    def _setupUserFolder(self):
        '''Creates the user folder.'''
        self.folder.manage_addUserFolder()

    def _setupUser(self):
        '''Creates the default user.'''
        uf = self.folder.acl_users
        uf._doAddUser(user_name, 'secret', [user_role], [])

    def _clear(self, call_close_hook=0):
        '''Clears the fixture.'''
        if self._setup_fixture:
            try: self.app._delObject(folder_name)
            except (AttributeError, RuntimeError): pass
        if call_close_hook:
            self.beforeClose()
        self._close()
        self.logout()
        self.afterClear()

    def _close(self):
        '''Closes the ZODB connection.'''
        get_transaction().abort()
        closeConnections()

    # Security interfaces

    def setRoles(self, roles, name=user_name):
        '''Changes the user's roles.'''
        uf = self.folder.acl_users
        uf._doChangeUser(name, None, roles, [])
        if name == getSecurityManager().getUser().getId():
            self.login(name)

    def setPermissions(self, permissions, role=user_role):
        '''Changes the user's permissions.'''
        self.folder.manage_role(role, permissions)

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

    # b/w compatibility methods

    def _setRoles(self, roles, name=user_name):
        self.setRoles(roles, name)
    def _setPermissions(self, permissions, role=user_role):
        self.setPermissions(permissions, role)
    def _login(self, name=user_name):
        self.login(name)
    def _logout(self):
        self.logout()


# b/w compatibility names
_folder_name = folder_name
_user_name = user_name
_user_role = user_role
_standard_permissions = standard_permissions

