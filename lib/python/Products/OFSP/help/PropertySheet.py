"""
PropertySheet
"""


class PropertySheet:
    """"

    A PropertySheet is an abstraction for organizing and working
    with a set of related properties. Conceptually it acts like a
    container for a set of related properties and metadata describing 
    those properties. A PropertySheet may or may not provide a web 
    interface for managing its properties.

    """

    def xml_namespace(self):
        """

        Return a namespace string usable as an xml namespace
        for this property set. This may be an empty string if 
        there is no default namespace for a given property sheet
        (esp. property sheets added in ZClass definitions).

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

        Returns true if 'self' has a property with the given 'id', 
        false otherwise. This method is protected by the 'Access 
        contents information' permission.

        """

    def propertyIds(self):
        """

        Returns a list of property ids. This method is protected by 
        the 'Access contents information' permission.

        """

    def propertyValues(self):
        """

        Returns a list of actual property values. This method is 
        protected by the 'Access contents information' permission.

        """

    def propertyItems(self):
        """

        Return a list of (id, property) tuples. This method is 
        protected by the 'Access contents information' permission.

        """
        
    def propertyMap(self):
        """

        Returns a tuple of mappings, giving meta-data for properties.

        """

    def propertyInfo(self):
        """

        Returns a mapping containing property metadata.

        """

    def manage_addProperty(self, id, value, type, REQUEST=None):
        """

        Add a new property with the given 'id', 'value' and 'type'.
        Supported values for the 'type' argument are outlined below 
        in the section "property types". This method will use the 
        passed in 'type' to try to convert the 'value' argument to 
        the named type. If the given 'value' cannot be converted,
        a ValueError will be raised.

        *If the given 'type' is not recognized, the 'value' and 'type' 
        
        given are simply stored blindly by the object. This seems like 
        
        bad behavior - it should probably raise an exception instead.*

        If no value is passed in for 'REQUEST', the method will return
        'None'. If a value is provided for 'REQUEST' (as it will when
        called via the web), the property management form for the
        object will be rendered and returned.

        This method may be called via the web, from DTML or from
        Python code. It is protected by the 'Manage properties'
        permission.

        """

    def manage_changeProperties(self, REQUEST=None, **kw):
        """

        Change existing object properties by passing either a mapping 
        object as 'REQUEST' containing name:value pairs or by passing 
        name=value keyword arguments.

        Some objects have "special" properties defined by product 
        authors that cannot be changed. If you try to change one of 
        these properties through this method, an error will be raised.

        Note that no type checking or conversion happens when this 
        method is called, so it is the caller's responsibility to 
        ensure that the updated values are of the correct type. 
        *This should probably change*.

        If a value is provided for 'REQUEST' (as it will be when
        called via the web), the method will return an HTML message
        dialog. If no REQUEST is passed, the method returns 'None' on
        success.

        This method may be called via the web, from DTML or from
        Python code. It is protected by the 'Manage properties'
        permission.

        """


    def manage_delProperties(self, ids=None, REQUEST=None):
        """

        Delete one or more properties with the given 'ids'. The 'ids' 
        argument should be a sequence (tuple or list) containing the 
        ids of the properties to be deleted. If 'ids' is empty no 
        action will be taken. If any of the properties named in 'ids' 
        does not exist, an error will be raised. 

        Some objects have "special" properties defined by product
        authors that cannot be deleted. If one of these properties is
        named in 'ids', an HTML error message is returned (this is
        lame and should be changed).

        If no value is passed in for 'REQUEST', the method will return
        None. If a value is provided for 'REQUEST' (as it will be when
        
        called via the web), the property management form for the
        object will be rendered and returned.

        This method may be called via the web, from DTML or from
        Python code. It is protected by the 'Manage properties'
        permission.

        """







