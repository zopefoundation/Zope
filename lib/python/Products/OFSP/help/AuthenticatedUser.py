"""
Authenticated User
"""

class AuthenticatedUser:
    """
    This interface needs to be supported by objects that
    are returned by user validation and used for access control.
    """
    

    def getUserName():
        """

        Return the username of a user

        Permission - Allways available
        
        """

    def hasRole(object, roles):
        """

        Return a value that is true if the user has the given roles on
        the given object and return false otherwise.

        Permission - Allways available
        
        """

    def getRoles(object):
        """

        Returns a list of the roles the user has on the given object
        (in the current context?)

        Permission - Allways available

        """

    def getId():
        """

        Get the ID of the user. The ID can be used, at least from
        Python, to get the user from the user's UserDatabase.

        Permission - Python only

        """

    def getDatabasePath():
        """

        Get a physical path to the user's UserDatabase.  A Traversal
        facility can be used to get the user database from the path
        returned by this method.

        Permission - Python only

        """

