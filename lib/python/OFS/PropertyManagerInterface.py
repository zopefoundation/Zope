from Zope.Interfaces.Interface import Interface

class PropertyManager:
    """
    Description of the PropertyManager interface
    """

    def valid_property_id(self, id):
        """

        Returns a true result if 'id' is a valid property name and is
        not allready an attribute of 'self'.

        """

    def getProperty(self, id, d=None):
        """

        Get the property 'id', returning the optional second 
        argument or None if no such property is found.

        """

    def getPropertyType(self, id):
        """

        Get the type of property 'id'.  returns None if no such
        property exists.

        """

    def hasProperty(self, id):
        """

        Returns a true value if 'self' has the property 'id'.
        Otherwise returns a false value.

        """

    def propertyIds(self):
        """

        Returns a list of property ids.

        """

    def propertyValues(self):
        """

        Returns a list of actual property objects.

        """

    def propertyIds(self):
        """

        Return a list of (id, property) tuples.

        """

    def propertyMap(self):
        """

        Returns a tuple of mappings, giving meta-data for properties.

        """

    def propertyLable(self, id):
        """

        Returns a label for the given property 'id'.  This just
        returns 'id'.

        """

    def propdict(self):
        """

        Returns a mapping from property id to property object.

        """


PropertyManagerInterface=Interface(PropertyManager) # create the interface object
