from Zope.Interfaces.Interface import Interface

class RoleManager:
    """
    Description of the RoleManager interface
    """

    def ac_inherited_permissions(self, all=0):
        """

        Get all permissions not defined in ourself that are inherited.
        Returns a sequence of tuples with a name as the first item an
        an empty tuple as the second.

        """

    def permission_settings(self):
        """

        Return user-role permission settings.

        """

    def permissionsOfRole(self, role):
        """

        Return the permissions that this Role maps to.

        """

    def rolesOfPermission(self, permission):
        """

        Returns roles that have 'permission'.

        """

    def acquiredRolesAreUsedBy(self, permission):

        """

        I have no idea.

        """

    def has_local_roles(self):
        """

        Returns the number of local roles for 'self', otherwiser
        returns a false value.

        """

    def get_local_roles(self):
        """

        Returns a sequence of local roles for 'self'.

        """

    def get_valid_userids(self):
        """

        who knows.

        """

    def get_local_roles_for_userid(self, userid):
        """

        who knows.

        """

    def valid_roles(self):
        """

        Returns a list of valid roles.

        """

    def validate_roles(self, roles):
        """

        Returns a true value if all given roles are valid.

        """

    def userdefined_roles(self):
        """

        Returns a list of user defined roles.

        """



RoleManagerInterface=Interface(RoleManager) # create the interface object
