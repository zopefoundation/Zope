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

import html

from AccessControl import ClassSecurityInfo
from AccessControl.class_init import InitializeClass
from AccessControl.Permission import Permission
from AccessControl.Permissions import change_permissions
from AccessControl.requestmethod import requestmethod
from AccessControl.rolemanager import RoleManager as BaseRoleManager
from AccessControl.rolemanager import _string_hash
from AccessControl.rolemanager import reqattr
from App.special_dtml import DTMLFile
from zExceptions import BadRequest


class RoleManager(BaseRoleManager):
    """An object that has configurable permissions"""

    security = ClassSecurityInfo()

    manage_options = (
        {
            'label': 'Security',
            'action': 'manage_access',
        },
    )

    security.declareProtected(change_permissions, 'manage_roleForm')  # NOQA: D001,E501
    manage_roleForm = DTMLFile(
        'dtml/roleEdit',
        globals(),
        management_view='Security'
    )

    @security.protected(change_permissions)
    @requestmethod('POST')
    def manage_role(self, role_to_manage, permissions=[], REQUEST=None):
        """Change the permissions given to the given role.
        """
        BaseRoleManager.manage_role(
            self, role_to_manage, permissions=permissions)
        if REQUEST is not None:
            return self.manage_access(REQUEST)

    security.declareProtected(change_permissions, 'manage_acquiredForm')  # NOQA: D001,E501
    manage_acquiredForm = DTMLFile(
        'dtml/acquiredEdit',
        globals(),
        management_view='Security'
    )

    @security.protected(change_permissions)
    @requestmethod('POST')
    def manage_acquiredPermissions(self, permissions=[], REQUEST=None):
        """Change the permissions that acquire.
        """
        BaseRoleManager.manage_acquiredPermissions(
            self, permissions=permissions)
        if REQUEST is not None:
            return self.manage_access(REQUEST)

    security.declareProtected(change_permissions, 'manage_permissionForm')  # NOQA: D001,E501
    manage_permissionForm = DTMLFile(
        'dtml/permissionEdit',
        globals(),
        management_view='Security'
    )

    @security.protected(change_permissions)
    @requestmethod('POST')
    def manage_permission(
        self,
        permission_to_manage,
        roles=[],
        acquire=0,
        REQUEST=None
    ):
        """Change the settings for the given permission.

        If optional arg acquire is true, then the roles for the permission
        are acquired, in addition to the ones specified, otherwise the
        permissions are restricted to only the designated roles.
        """
        BaseRoleManager.manage_permission(
            self, permission_to_manage, roles=roles, acquire=acquire)
        if REQUEST is not None:
            return self.manage_access(REQUEST)

    _normal_manage_access = DTMLFile('dtml/access', globals())
    manage_reportUserPermissions = DTMLFile(
        'dtml/reportUserPermissions',
        globals()
    )

    @security.protected(change_permissions)
    def manage_access(self, REQUEST, **kw):
        """Return an interface for making permissions settings."""
        return self._normal_manage_access(**kw)

    @security.protected(change_permissions)
    @requestmethod('POST')
    def manage_changePermissions(self, REQUEST):
        """Change all permissions settings, called by management screen."""
        valid_roles = self.valid_roles()
        have = REQUEST.__contains__
        permissions = self.ac_inherited_permissions(1)
        fails = []
        for ip in range(len(permissions)):
            permission_name = permissions[ip][0]
            permission_hash = _string_hash(permission_name)
            roles = []
            for role in valid_roles:
                role_name = role
                role_hash = _string_hash(role_name)
                if have(f"permission_{permission_hash}role_{role_hash}"):
                    roles.append(role)
            name, value = permissions[ip][:2]
            try:
                p = Permission(name, value, self)
                if not have('acquire_%s' % permission_hash):
                    roles = tuple(roles)
                p.setRoles(roles)
            except Exception:
                fails.append(name)

        if fails:
            raise BadRequest('Some permissions had errors: '
                             + html.escape(', '.join(fails), True))
        if REQUEST is not None:
            return self.manage_access(REQUEST)

    security.declareProtected(change_permissions, 'manage_listLocalRoles')  # NOQA: D001,E501
    manage_listLocalRoles = DTMLFile(
        'dtml/listLocalRoles',
        globals(),
        management_view='Security'
    )

    security.declareProtected(change_permissions, 'manage_editLocalRoles')  # NOQA: D001,E501
    manage_editLocalRoles = DTMLFile(
        'dtml/editLocalRoles',
        globals(),
        management_view='Security'
    )

    @security.protected(change_permissions)
    @requestmethod('POST')
    def manage_addLocalRoles(self, userid, roles, REQUEST=None):
        """Set local roles for a user."""
        BaseRoleManager.manage_addLocalRoles(self, userid, roles)
        if REQUEST is not None:
            stat = 'Your changes have been saved.'
            return self.manage_listLocalRoles(self, REQUEST, stat=stat)

    @security.protected(change_permissions)
    @requestmethod('POST')
    def manage_setLocalRoles(self, userid, roles=[], REQUEST=None):
        """Set local roles for a user."""
        if roles:
            BaseRoleManager.manage_setLocalRoles(self, userid, roles)
        else:
            return self.manage_delLocalRoles((userid,), REQUEST)
        if REQUEST is not None:
            stat = 'Your changes have been saved.'
            return self.manage_listLocalRoles(self, REQUEST, stat=stat)

    @security.protected(change_permissions)
    @requestmethod('POST')
    def manage_delLocalRoles(self, userids, REQUEST=None):
        """Remove all local roles for a user."""
        BaseRoleManager.manage_delLocalRoles(self, userids)
        if REQUEST is not None:
            stat = 'Your changes have been saved.'
            return self.manage_listLocalRoles(self, REQUEST, stat=stat)

    @security.protected(change_permissions)
    def manage_defined_roles(self, submit=None, REQUEST=None):
        """Called by management screen."""
        if submit == 'Add Role':
            role = reqattr(REQUEST, 'role').strip()
            return self._addRole(role, REQUEST)

        if submit == 'Delete Role':
            roles = reqattr(REQUEST, 'roles')
            return self._delRoles(roles, REQUEST)

        return self.manage_access(REQUEST)

    @requestmethod('POST')
    def _addRole(self, role, REQUEST=None):
        if not role:
            raise BadRequest('You must specify a role name')
        if role in self.__ac_roles__:
            raise BadRequest('The given role is already defined')
        data = list(self.__ac_roles__)
        data.append(role)
        self.__ac_roles__ = tuple(data)
        if REQUEST is not None:
            return self.manage_access(REQUEST)

    @requestmethod('POST')
    def _delRoles(self, roles, REQUEST=None):
        if not roles:
            raise BadRequest('You must specify a role name')
        data = list(self.__ac_roles__)
        for role in roles:
            try:
                data.remove(role)
            except Exception:
                pass
        self.__ac_roles__ = tuple(data)
        if REQUEST is not None:
            return self.manage_access(REQUEST)

    def _has_user_defined_role(self, role):
        return role in self.__ac_roles__

    # Compatibility names only!!

    smallRolesWidget = selectedRoles = ''
    aclAChecked = aclPChecked = aclEChecked = ''
    validRoles = BaseRoleManager.valid_roles

    def manage_editRoles(self, REQUEST, acl_type='A', acl_roles=[]):
        pass

    def _setRoles(self, acl_type, acl_roles):
        pass


InitializeClass(RoleManager)
