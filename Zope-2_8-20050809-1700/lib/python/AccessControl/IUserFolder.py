class IStandardUserFolder:
    def getUser(self, name):
        """
        Returns the user object specified by name.  If there is no
        user named 'name' in the user folder, return None.
        """

    def getUsers(self):
        """
        Returns a sequence of all user objects which reside in the user
        folder.
        """

    def getUserNames(self):
        """
        Returns a sequence of names of the users which reside in the user
        folder.
        """
