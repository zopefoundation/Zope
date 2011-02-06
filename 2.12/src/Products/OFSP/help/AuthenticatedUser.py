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

class AuthenticatedUser:
    """
    This interface needs to be supported by objects that
    are returned by user validation and used for access control.
    """

    def getUserName():
        """
        Return the name of a user

        Permission -- Always available
        """

    def has_role(roles, object=None):
        """
        Return true if the user has at least one role from a list of
        roles, optionally in the context of an object.

        Permission -- Always available
        """

    def has_permission(permission, object):
        """
        Return true if the user has a permission on an object.

        Permission -- Always available
        """

    def getRoles():
        """
        Return a list of the user's roles.

        Permission -- Always available
        """

    def getRolesInContext(object):
        """
        Return the list of roles assigned to the user, including local
        roles assigned in context of an object.

        Permission -- Always available
        """

    def getId():
        """
        Get the ID of the user. The ID can be used from
        Python to get the user from the user's UserDatabase.

        Permission -- Always available
        """

    def getDomains():
        """
        Return the list of domain restrictions for a user.

        Permission -- Always available
        """
