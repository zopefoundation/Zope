"""
PropertyManager
"""

class PropertyManager:
    """
    A Property Manager object has a collection of typed attributes
    called properties. Properties can be managed through the web or
    via DTML.
    
    In addition to having a type, properties can be writable or
    read-only and can have default values.
    """

    def getProperty(self, id, d=None):
        """
        Return the value of the property 'id'. If the property is not
        found the optional second argument or None is returned.
        
        Permission -- XXX None XXX
        """

    def getPropertyType(self, id):
        """
        Get the type of property 'id'. Returns None if no such
        property exists.
        
        Permission -- XXX None XXX   
        """

    def hasProperty(self, id):
        """
        Returns a true value if the Property Manager has the property
        'id'. Otherwise returns a false value.
        
        Permission -- 'Access contents information'
        """

    def propertyIds(self):
        """
        Returns a list of property ids.
        
        Permission -- 'Access contents information'
        """

    def propertyValues(self):
        """
        Returns a list of property values.
        
        Permission -- 'Access contents information'        
        """

    def propertyItems(self):
        """
        Return a list of (id, property) tuples.
        
        Permission -- 'Access contents information'
        """

    def propertyMap(self):
        """
        Returns a tuple of mappings, giving meta-data for properties.
        The meta-data includes 'id', 'type', and 'mode'.
        
        Permission -- XXX None XXX
        """

    def propdict(self):
        """
        Returns the properties as a mapping from property id to
        property value.
        
        Permission -- XXX None XXX
        """
