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
"""Role manager
"""

from cgi import escape

from App.Dialogs import MessageDialog
from App.special_dtml import DTMLFile

from AccessControl import ClassSecurityInfo
from AccessControl.class_init import InitializeClass
from AccessControl.rolemanager import RoleManager as BaseRoleManager
from AccessControl.rolemanager import reqattr
from AccessControl.Permission import Permission
from AccessControl.Permissions import change_permissions
from AccessControl.requestmethod import requestmethod


class RoleManager(BaseRoleManager):
    """An object that has configurable permissions"""

    security = ClassSecurityInfo()

    manage_options=(
        {'label': 'Security', 'action': 'manage_access'},
        )

    security.declareProtected(change_permissions, 'manage_roleForm')
    manage_roleForm=DTMLFile('dtml/roleEdit', globals(),
                             management_view='Security')

    security.declareProtected(change_permissions, 'manage_role')
    @requestmethod('POST')
    def manage_role(self, role_to_manage, permissions=[], REQUEST=None):
        """Change the permissions given to the given role.
        """
        BaseRoleManager.manage_role(
            self, role_to_manage, permissions=permissions)
        if REQUEST is not None:
            return self.manage_access(REQUEST)

    security.declareProtected(change_permissions, 'manage_acquiredForm')
    manage_acquiredForm=DTMLFile('dtml/acquiredEdit', globals(),
                                 management_view='Security')

    security.declareProtected(change_permissions, 'manage_acquiredPermissions')
    @requestmethod('POST')
    def manage_acquiredPermissions(self, permissions=[], REQUEST=None):
        """Change the permissions that acquire.
        """
        BaseRoleManager.manage_acquiredPermissions(
            self, permissions=permissions)
        if REQUEST is not None:
            return self.manage_access(REQUEST)

    security.declareProtected(change_permissions, 'manage_permissionForm')
    manage_permissionForm=DTMLFile('dtml/permissionEdit', globals(),
                                   management_view='Security')

    security.declareProtected(change_permissions, 'manage_permission')
    @requestmethod('POST')
    def manage_permission(self, permission_to_manage,
                          roles=[], acquire=0, REQUEST=None):
        """Change the settings for the given permission.

        If optional arg acquire is true, then the roles for the permission
        are acquired, in addition to the ones specified, otherwise the
        permissions are restricted to only the designated roles.
        """
        BaseRoleManager.manage_permission(
            self, permission_to_manage, roles=roles, acquire=acquire)
        if REQUEST is not None:
            return self.manage_access(REQUEST)

    _normal_manage_access=DTMLFile('dtml/access', globals())
    manage_reportUserPermissions=DTMLFile(
        'dtml/reportUserPermissions', globals())

    security.declareProtected(change_permissions, 'manage_access')
    def manage_access(self, REQUEST, **kw):
        """Return an interface for making permissions settings.
        """
        return apply(self._normal_manage_access, (), kw)

    security.declareProtected(change_permissions, 'manage_changePermissions')
    @requestmethod('POST')
    def manage_changePermissions(self, REQUEST):
        """Change all permissions settings, called by management screen.
        """
        valid_roles=self.valid_roles()
        indexes=range(len(valid_roles))
        have=REQUEST.has_key
        permissions=self.ac_inherited_permissions(1)
        fails = []
        for ip in range(len(permissions)):
            roles = []
            for ir in indexes:
                if have("p%dr%d" % (ip, ir)):
                    roles.append(valid_roles[ir])
            name, value = permissions[ip][:2]
            try:
                p = Permission(name, value, self)
                if not have('a%d' % ip):
                    roles=tuple(roles)
                p.setRoles(roles)
            except:
                fails.append(name)

        if fails:
            return MessageDialog(title="Warning!",
                                 message="Some permissions had errors: "
                                   + escape(', '.join(fails)),
                                 action='manage_access')
        return MessageDialog(
            title = 'Success!',
            message = 'Your changes have been saved',
            action = 'manage_access')

    security.declareProtected(change_permissions, 'manage_listLocalRoles')
    manage_listLocalRoles=DTMLFile('dtml/listLocalRoles', globals(),
                                   management_view='Security')

    security.declareProtected(change_permissions, 'manage_editLocalRoles')
    manage_editLocalRoles=DTMLFile('dtml/editLocalRoles', globals(),
                                   management_view='Security')

    security.declareProtected(change_permissions, 'manage_addLocalRoles')
    @requestmethod('POST')
    def manage_addLocalRoles(self, userid, roles, REQUEST=None):
        """Set local roles for a user."""
        BaseRoleManager.manage_addLocalRoles(self, userid, roles)
        if REQUEST is not None:
            stat='Your changes have been saved.'
            return self.manage_listLocalRoles(self, REQUEST, stat=stat)

    security.declareProtected(change_permissions, 'manage_setLocalRoles')
    @requestmethod('POST')
    def manage_setLocalRoles(self, userid, roles, REQUEST=None):
        """Set local roles for a user."""
        BaseRoleManager.manage_setLocalRoles(self, userid, roles)
        if REQUEST is not None:
            stat='Your changes have been saved.'
            return self.manage_listLocalRoles(self, REQUEST, stat=stat)

    security.declareProtected(change_permissions, 'manage_delLocalRoles')
    @requestmethod('POST')
    def manage_delLocalRoles(self, userids, REQUEST=None):
        """Remove all local roles for a user."""
        BaseRoleManager.manage_delLocalRoles(self, userids)
        if REQUEST is not None:
            stat='Your changes have been saved.'
            return self.manage_listLocalRoles(self, REQUEST, stat=stat)

    security.declareProtected(change_permissions, 'manage_defined_roles')
    def manage_defined_roles(self, submit=None, REQUEST=None):
        """Called by management screen.
        """

        if submit=='Add Role':
            role=reqattr(REQUEST, 'role').strip()
            return self._addRole(role, REQUEST)

        if submit=='Delete Role':
            roles=reqattr(REQUEST, 'roles')
            return self._delRoles(roles, REQUEST)

        return self.manage_access(REQUEST)

    @requestmethod('POST')
    def _addRole(self, role, REQUEST=None):
        if not role:
            return MessageDialog(
                   title='Incomplete',
                   message='You must specify a role name',
                   action='manage_access')
        if role in self.__ac_roles__:
            return MessageDialog(
                   title='Role Exists',
                   message='The given role is already defined',
                   action='manage_access')
        data = list(self.__ac_roles__)
        data.append(role)
        self.__ac_roles__=tuple(data)
        if REQUEST is not None:
            return self.manage_access(REQUEST)

    @requestmethod('POST')
    def _delRoles(self, roles, REQUEST=None):
        if not roles:
            return MessageDialog(
                   title='Incomplete',
                   message='You must specify a role name',
                   action='manage_access')
        data = list(self.__ac_roles__)
        for role in roles:
            try:
                data.remove(role)
            except:
                pass
        self.__ac_roles__ = tuple(data)
        if REQUEST is not None:
            return self.manage_access(REQUEST)

    def _has_user_defined_role(self, role):
        return role in self.__ac_roles__

    # Compatibility names only!!

    smallRolesWidget=selectedRoles=aclAChecked=aclPChecked=aclEChecked=''
    validRoles=BaseRoleManager.valid_roles

    def manage_editRoles(self, REQUEST, acl_type='A', acl_roles=[]):
        pass

    def _setRoles(self, acl_type, acl_roles):
        pass

InitializeClass(RoleManager)
