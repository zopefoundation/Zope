##############################################################################
#
# Copyright (c) 2005 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""AccessControl z3 interfaces.

$Id$
"""

from zope.interface import Attribute
from zope.interface import Interface


# XXX: might contain non-API methods and outdated comments;
#      not synced with ZopeBook API Reference;
#      based on AccessControl.Owned.Owned
class IOwned(Interface):

    manage_owner = Attribute("""Manage owner view""")

    def owner_info():
        """Get ownership info for display
        """

    def getOwner(info=0):
        """Get the owner

        If a true argument is provided, then only the owner path and id are
        returned. Otherwise, the owner object is returned.
        """

    def getOwnerTuple():
        """Return a tuple, (userdb_path, user_id) for the owner.

        o Ownership can be acquired, but only from the containment path.

        o If unowned, return None.
        """

    def getWrappedOwner():
        """Get the owner, modestly wrapped in the user folder.

        o If the object is not owned, return None.

        o If the owner's user database doesn't exist, return Nobody.

        o If the owner ID does not exist in the user database, return Nobody.
        """

    def changeOwnership(user, recursive=0):
        """Change the ownership to the given user.

        If 'recursive' is true then also take ownership of all sub-objects,
        otherwise sub-objects retain their ownership information.
        """

    def userCanTakeOwnership():
        """
        """

    def manage_takeOwnership(REQUEST, RESPONSE, recursive=0):
        """Take ownership (responsibility) for an object.

        If 'recursive' is true, then also take ownership of all sub-objects.
        """

    def manage_changeOwnershipType(explicit=1,
                                   RESPONSE=None, REQUEST=None):
        """Change the type (implicit or explicit) of ownership.
        """

    def _deleteOwnershipAfterAdd():
        """
        """

    def manage_fixupOwnershipAfterAdd():
        """
        """


# XXX: might contain non-API methods and outdated comments;
#      not synced with ZopeBook API Reference;
#      based on AccessControl.PermissionMapping.RoleManager
class IPermissionMappingSupport(Interface):

    def manage_getPermissionMapping():
        """Return the permission mapping for the object

        This is a list of dictionaries with:

          permission_name -- The name of the native object permission

          class_permission -- The class permission the permission is
             mapped to.
        """

    def manage_setPermissionMapping(permission_names=[],
                                    class_permissions=[], REQUEST=None):
        """Change the permission mapping
        """


# XXX: might contain non-API methods and outdated comments;
#      not synced with ZopeBook API Reference;
#      based on AccessControl.Role.RoleManager
class IRoleManager(IPermissionMappingSupport):

    """An object that has configurable permissions"""

    permissionMappingPossibleValues = Attribute("""Acquired attribute""")

    def ac_inherited_permissions(all=0):
        """Get all permissions not defined in ourself that are inherited.

        This will be a sequence of tuples with a name as the first item and an
        empty tuple as the second.
        """

    def permission_settings(permission=None):
        """Return user-role permission settings.

        If 'permission' is passed to the method then only the settings for
        'permission' is returned.
        """

    manage_roleForm = Attribute(""" """)

    def manage_role(role_to_manage, permissions=[], REQUEST=None):
        """Change the permissions given to the given role.
        """

    manage_acquiredForm = Attribute(""" """)

    def manage_acquiredPermissions(permissions=[], REQUEST=None):
        """Change the permissions that acquire.
        """

    manage_permissionForm = Attribute(""" """)

    def manage_permission(permission_to_manage,
                          roles=[], acquire=0, REQUEST=None):
        """Change the settings for the given permission.

        If optional arg acquire is true, then the roles for the permission
        are acquired, in addition to the ones specified, otherwise the
        permissions are restricted to only the designated roles.
        """

    def manage_access(REQUEST, **kw):
        """Return an interface for making permissions settings.
        """

    def manage_changePermissions(REQUEST):
        """Change all permissions settings, called by management screen.
        """

    def permissionsOfRole(role):
        """Used by management screen.
        """

    def rolesOfPermission(permission):
        """Used by management screen.
        """

    def acquiredRolesAreUsedBy(permission):
        """Used by management screen.
        """


    # Local roles support
    # -------------------
    #
    # Local roles allow a user to be given extra roles in the context
    # of a particular object (and its children). When a user is given
    # extra roles in a particular object, an entry for that user is made
    # in the __ac_local_roles__ dict containing the extra roles.

    __ac_local_roles__  = Attribute(""" """)

    manage_listLocalRoles = Attribute(""" """)

    manage_editLocalRoles = Attribute(""" """)

    def has_local_roles():
        """
        """

    def get_local_roles():
        """
        """

    def users_with_local_role(role):
        """
        """

    def get_valid_userids():
        """
        """

    def get_local_roles_for_userid(userid):
        """
        """

    def manage_addLocalRoles(userid, roles, REQUEST=None):
        """Set local roles for a user."""

    def manage_setLocalRoles(userid, roles, REQUEST=None):
        """Set local roles for a user."""

    def manage_delLocalRoles(userids, REQUEST=None):
        """Remove all local roles for a user."""

    #------------------------------------------------------------

    def access_debug_info():
        """Return debug info.
        """

    def valid_roles():
        """Return list of valid roles.
        """

    def validate_roles(roles):
        """Return true if all given roles are valid.
        """

    def userdefined_roles():
        """Return list of user-defined roles.
        """

    def manage_defined_roles(submit=None, REQUEST=None):
        """Called by management screen.
        """

    def _addRole(role, REQUEST=None):
        """
        """

    def _delRoles(roles, REQUEST=None):
        """
        """

    def _has_user_defined_role(role):
        """
        """

    def manage_editRoles(REQUEST, acl_type='A', acl_roles=[]):
        """
        """

    def _setRoles(acl_type, acl_roles):
        """
        """

    def possible_permissions():
        """
        """
