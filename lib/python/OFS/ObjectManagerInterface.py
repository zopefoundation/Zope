from Zope.Interfaces.Interface import Interface

class ObjectManager:
    """
    Description of the ObjectManager interface
    """
    def objectIds(self, spec=None):
        """

        'objectIds' returns the ids of objects in this ObjectManager.
        If the optional argument 'spec' is provided, then only ids of
        objects of meta_type 'spec' will be returned.  'spec' can be
        either a string or a list of strings.

        """

    def objectValues(self, spec=None):
        """

        'objectValues' returns the actuall subobjects in this
        ObjectManager.  If the optional argument 'spec' is provided,
        then only objects of meta_type 'spec' will be returned.
        'spec' can be either a string or a list of strings.

        """

    def objectItems(self, spec=None):
        """

        'objectItems' returns a list of (id, subobject) tuples in this
        ObjectManager.  if the optional argument 'spec' is provided,
        then only objects of meta_type 'spec' will be returned.
        'spec' can be either a string or a list of strings.

        """

    def objectMap(self):
        """

        Returns a tuple of mappings containing subobject meta-data.

        """

    def superValues(self, t):
        """

        'superValues' returns a list of objects of the given meta_type
        't'.  This search is performed in the current ObjectManager
        and all ObjectManagers above it.

        """


ObjectManagerInterface=Interface(ObjectManager) # create the interface object
