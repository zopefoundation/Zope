##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""User folders
"""

import os

from Acquisition import aq_base

from App.Management import Navigation
from App.Management import Tabs
from App.special_dtml import DTMLFile
from App.Dialogs import MessageDialog
from OFS.role import RoleManager
from OFS.SimpleItem import Item

from AccessControl import ClassSecurityInfo
from AccessControl.class_init import InitializeClass
from AccessControl.Permissions import manage_users as ManageUsers
from AccessControl.requestmethod import requestmethod
from AccessControl.rolemanager import DEFAULTMAXLISTUSERS
from AccessControl import userfolder as accesscontrol_userfolder
from AccessControl.users import readUserAccessFile
from AccessControl.users import _remote_user_mode
from AccessControl.users import emergency_user
from AccessControl.users import reqattr


class BasicUserFolder(Navigation, Tabs, Item, RoleManager,
                      accesscontrol_userfolder.BasicUserFolder):
    """Base class for UserFolder-like objects"""

    security = ClassSecurityInfo()

    # Note: use of the '_super' name is deprecated.
    _super = emergency_user

    manage_options=(
        (
        {'label': 'Contents', 'action': 'manage_main'},
        {'label': 'Properties', 'action': 'manage_userFolderProperties'},
        )
        +RoleManager.manage_options
        +Item.manage_options
        )

    security.declareProtected(ManageUsers, 'userFolderAddUser')
    @requestmethod('POST')
    def userFolderAddUser(self, name, password, roles, domains,
                          REQUEST=None, **kw):
        """API method for creating a new user object. Note that not all
           user folder implementations support dynamic creation of user
           objects."""
        if hasattr(self, '_doAddUser'):
            return self._doAddUser(name, password, roles, domains, **kw)
        raise NotImplementedError

    security.declareProtected(ManageUsers, 'userFolderEditUser')
    @requestmethod('POST')
    def userFolderEditUser(self, name, password, roles, domains,
                           REQUEST=None, **kw):
        """API method for changing user object attributes. Note that not
           all user folder implementations support changing of user object
           attributes."""
        if hasattr(self, '_doChangeUser'):
            return self._doChangeUser(name, password, roles, domains, **kw)
        raise NotImplementedError

    security.declareProtected(ManageUsers, 'userFolderDelUsers')
    @requestmethod('POST')
    def userFolderDelUsers(self, names, REQUEST=None):
        """API method for deleting one or more user objects. Note that not
           all user folder implementations support deletion of user objects."""
        if hasattr(self, '_doDelUsers'):
            return self._doDelUsers(names)
        raise NotImplementedError

    _mainUser=DTMLFile('dtml/mainUser', globals())
    _add_User=DTMLFile('dtml/addUser', globals(),
                       remote_user_mode__=_remote_user_mode)
    _editUser=DTMLFile('dtml/editUser', globals(),
                       remote_user_mode__=_remote_user_mode)
    manage=manage_main=_mainUser
    manage_main._setName('manage_main')

    _userFolderProperties = DTMLFile('dtml/userFolderProps', globals())

    def manage_userFolderProperties(self, REQUEST=None,
                                    manage_tabs_message=None):
        """
        """
        return self._userFolderProperties(
            self, REQUEST, manage_tabs_message=manage_tabs_message,
            management_view='Properties')

    @requestmethod('POST')
    def manage_setUserFolderProperties(self, encrypt_passwords=0,
                                       update_passwords=0,
                                       maxlistusers=DEFAULTMAXLISTUSERS,
                                       REQUEST=None):
        """
        Sets the properties of the user folder.
        """
        self.encrypt_passwords = not not encrypt_passwords
        try:
            self.maxlistusers = int(maxlistusers)
        except ValueError:
            self.maxlistusers = DEFAULTMAXLISTUSERS
        if encrypt_passwords and update_passwords:
            changed = 0
            for u in self.getUsers():
                pw = u._getPassword()
                if not self._isPasswordEncrypted(pw):
                    pw = self._encryptPassword(pw)
                    self._doChangeUser(u.getUserName(), pw, u.getRoles(),
                                       u.getDomains())
                    changed = changed + 1
            if REQUEST is not None:
                if not changed:
                    msg = 'All passwords already encrypted.'
                else:
                    msg = 'Encrypted %d password(s).' % changed
                return self.manage_userFolderProperties(
                    REQUEST, manage_tabs_message=msg)
            else:
                return changed
        else:
            if REQUEST is not None:
                return self.manage_userFolderProperties(
                    REQUEST, manage_tabs_message='Saved changes.')

    @requestmethod('POST')
    def _addUser(self, name, password, confirm, roles, domains, REQUEST=None):
        if not name:
            return MessageDialog(
                   title='Illegal value',
                   message='A username must be specified',
                   action='manage_main')
        if not password or not confirm:
            if not domains:
                return MessageDialog(
                   title='Illegal value',
                   message='Password and confirmation must be specified',
                   action='manage_main')
        if self.getUser(name) or (self._emergency_user and
                                  name == self._emergency_user.getUserName()):
            return MessageDialog(
                   title='Illegal value',
                   message='A user with the specified name already exists',
                   action='manage_main')
        if (password or confirm) and (password != confirm):
            return MessageDialog(
                   title='Illegal value',
                   message='Password and confirmation do not match',
                   action='manage_main')

        if not roles:
            roles = []
        if not domains:
            domains = []

        if domains and not self.domainSpecValidate(domains):
            return MessageDialog(
                   title='Illegal value',
                   message='Illegal domain specification',
                   action='manage_main')
        self._doAddUser(name, password, roles, domains)
        if REQUEST:
            return self._mainUser(self, REQUEST)

    @requestmethod('POST')
    def _changeUser(self, name, password, confirm, roles, domains,
                    REQUEST=None):
        if password == 'password' and confirm == 'pconfirm':
            # Protocol for editUser.dtml to indicate unchanged password
            password = confirm = None
        if not name:
            return MessageDialog(
                   title='Illegal value',
                   message='A username must be specified',
                   action='manage_main')
        if password == confirm == '':
            if not domains:
                return MessageDialog(
                   title='Illegal value',
                   message='Password and confirmation must be specified',
                   action='manage_main')
        if not self.getUser(name):
            return MessageDialog(
                   title='Illegal value',
                   message='Unknown user',
                   action='manage_main')
        if (password or confirm) and (password != confirm):
            return MessageDialog(
                   title='Illegal value',
                   message='Password and confirmation do not match',
                   action='manage_main')

        if not roles:
            roles = []
        if not domains:
            domains = []

        if domains and not self.domainSpecValidate(domains):
            return MessageDialog(
                   title='Illegal value',
                   message='Illegal domain specification',
                   action='manage_main')
        self._doChangeUser(name, password, roles, domains)
        if REQUEST:
            return self._mainUser(self, REQUEST)

    @requestmethod('POST')
    def _delUsers(self, names, REQUEST=None):
        if not names:
            return MessageDialog(
                   title='Illegal value',
                   message='No users specified',
                   action='manage_main')
        self._doDelUsers(names)
        if REQUEST:
            return self._mainUser(self, REQUEST)

    security.declareProtected(ManageUsers, 'manage_users')
    def manage_users(self, submit=None, REQUEST=None, RESPONSE=None):
        """This method handles operations on users for the web based forms
           of the ZMI. Application code (code that is outside of the forms
           that implement the UI of a user folder) are encouraged to use
           manage_std_addUser"""
        if submit=='Add...':
            return self._add_User(self, REQUEST)

        if submit=='Edit':
            try:
                user=self.getUser(reqattr(REQUEST, 'name'))
            except:
                return MessageDialog(
                    title='Illegal value',
                    message='The specified user does not exist',
                    action='manage_main')
            return self._editUser(self, REQUEST, user=user, password=user.__)

        if submit=='Add':
            name = reqattr(REQUEST, 'name')
            password = reqattr(REQUEST, 'password')
            confirm = reqattr(REQUEST, 'confirm')
            roles = reqattr(REQUEST, 'roles')
            domains = reqattr(REQUEST, 'domains')
            return self._addUser(name, password, confirm, roles,
                                 domains, REQUEST)

        if submit=='Change':
            name = reqattr(REQUEST, 'name')
            password = reqattr(REQUEST, 'password')
            confirm = reqattr(REQUEST, 'confirm')
            roles = reqattr(REQUEST, 'roles')
            domains = reqattr(REQUEST, 'domains')
            return self._changeUser(name, password, confirm, roles,
                                    domains, REQUEST)

        if submit=='Delete':
            names = reqattr(REQUEST, 'names')
            return self._delUsers(names, REQUEST)

        return self._mainUser(self, REQUEST)

    def manage_beforeDelete(self, item, container):
        if item is self:
            try:
                del container.__allow_groups__
            except:
                pass

    def manage_afterAdd(self, item, container):
        if item is self:
            self = aq_base(self)
            container.__allow_groups__ = self

    def _setId(self, id):
        if id != self.id:
            raise ValueError(MessageDialog(
                title='Invalid Id',
                message='Cannot change the id of a UserFolder',
                action='./manage_main'))

InitializeClass(BasicUserFolder)


class UserFolder(accesscontrol_userfolder.UserFolder, BasicUserFolder):
    """Standard UserFolder object

    A UserFolder holds User objects which contain information
    about users including name, password domain, and roles.
    UserFolders function chiefly to control access by authenticating
    users and binding them to a collection of roles."""

    icon = 'p_/UserFolder'
    _ofs_migrated = False

    def __init__(self):
        super(UserFolder, self).__init__()
        self._ofs_migrated = True

    def _createInitialUser(self):
        """
        If there are no users or only one user in this user folder,
        populates from the 'inituser' file in the instance home.
        We have to do this even when there is already a user
        just in case the initial user ignored the setup messages.
        We don't do it for more than one user to avoid
        abuse of this mechanism.
        Called only by OFS.Application.initialize().
        """
        if len(self.data) <= 1:
            info = readUserAccessFile('inituser')
            if info:
                import App.config
                name, password, domains, remote_user_mode = info
                self._doDelUsers(self.getUserNames())
                self._doAddUser(name, password, ('Manager', ), domains)
                cfg = App.config.getConfiguration()
                try:
                    os.remove(os.path.join(cfg.instancehome, 'inituser'))
                except:
                    pass

InitializeClass(UserFolder)


def manage_addUserFolder(self, dtself=None, REQUEST=None, **ignored):
    """ """
    f = UserFolder()
    self = self.this()
    try:
        self._setObject('acl_users', f)
    except:
        return MessageDialog(
            title='Item Exists',
            message='This object already contains a User Folder',
            action='%s/manage_main' % REQUEST['URL1'])
    self.__allow_groups__ = f
    if REQUEST is not None:
        REQUEST['RESPONSE'].redirect(self.absolute_url()+'/manage_main')
