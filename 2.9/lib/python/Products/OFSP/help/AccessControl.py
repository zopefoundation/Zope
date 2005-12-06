"""
AccessControl: Security functions and classes

  The functions and classes in this module are available to
  Python-based Scripts and Page Templates.

"""

def getSecurityManager():
    """
    Returns the security manager. See the 'SecurityManager' class.
    """

class SecurityManager:
    """
    A security manager provides methods for checking access and
    managing executable context and policies
    """

    def validate(accessed=None, container=None, name=None, value=None,
                 roles=None):
        """
        Validate access.

        Arguments:

        accessed -- the object that was being accessed

        container -- the object the value was found in

        name -- The name used to access the value

        value -- The value retrieved though the access.

        roles -- The roles of the object if already known.

        The arguments may be provided as keyword arguments. Some of
        these arguments may be omitted, however, the policy may
        reject access in some cases when arguments are omitted.  It
        is best to provide all the values possible.

        permission -- Always available
        """

    def checkPermission(self, permission, object):
        """
        Check whether the security context allows the given permission
        on the given object.

        permission -- Always available
        """

    def getUser(self):
        """
        Get the current authenticated user. See the
        'AuthenticatedUser' class.

        permission -- Always available
        """

    def calledByExecutable(self):
        """
        Return a boolean value indicating if this context was called
        by an executable.

        permission -- Always available
        """
