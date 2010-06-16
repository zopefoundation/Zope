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

class PropertySheet:
    """

    A PropertySheet is an abstraction for organizing and working
    with a set of related properties. Conceptually it acts like a
    container for a set of related properties and meta-data describing
    those properties. A PropertySheet may or may not provide a web
    interface for managing its properties.

    """

    def xml_namespace():
        """

        Return a namespace string usable as an xml namespace
        for this property set. This may be an empty string if
        there is no default namespace for a given property sheet.

        Permission -- Python only

        """

    def getProperty(id, d=None):
        """

        Get the property 'id', returning the optional second
        argument or None if no such property is found.

        Permission -- Python only

        """

    def getPropertyType(id):
        """

        Get the type of property 'id'. Returns None if no such
        property exists.

        Permission -- Python only

        """

    def hasProperty(id):
        """

        Returns true if 'self' has a property with the given 'id',
        false otherwise.

        Permission -- 'Access contents information'

        """

    def propertyIds():
        """

        Returns a list of property ids.

        Permission --  'Access contents information'

        """

    def propertyValues():
        """

        Returns a list of actual property values.

        Permission -- 'Access contents information'

        """

    def propertyItems():
        """

        Return a list of (id, property) tuples.

        Permission -- 'Access contents information'

        """

    def propertyMap():
        """

        Returns a tuple of mappings, giving meta-data for properties.

        Permssion -- Python only

        """

    def propertyInfo():
        """

        Returns a mapping containing property meta-data.

        Permission -- Python only

        """

    def manage_addProperty(id, value, type, REQUEST=None):
        """

        Add a new property with the given 'id', 'value' and 'type'.

        These are the
        property types:

          'boolean' -- 1 or 0.

          'date' -- A 'DateTime' value, for example '12/31/1999 15:42:52 PST'.

          'float' -- A decimal number, for example '12.4'.

          'int' -- An integer number, for example, '12'.

          'lines' -- A list of strings, one per line.

          'long' -- A long integer, for example '12232322322323232323423'.

          'string' -- A string of characters, for example 'This is a string'.

          'text' -- A multi-line string, for example a paragraph.

          'tokens' -- A list of strings separated by white space, for example
          'one two three'.

          'selection' -- A string selected by a pop-up menu.

          'multiple selection' -- A list of strings selected by a selection list.

        This method will use the passed in 'type' to try to convert
        the 'value' argument to the named type. If the given 'value'
        cannot be converted, a ValueError will be raised.

        The value given for 'selection' and 'multiple selection'
        properites may be an attribute or method name.  The attribute
        or method must return a sequence values.

        If the given 'type' is not recognized, the 'value' and 'type'
        given are simply stored blindly by the object.

        If no value is passed in for 'REQUEST', the method will return
        'None'. If a value is provided for 'REQUEST' (as it will when
        called via the web), the property management form for the
        object will be rendered and returned.

        This method may be called via the web, from DTML or from
        Python code.

        Permission -- 'Manage Properties'

        """

    def manage_changeProperties(REQUEST=None, **kw):
        """

        Change object properties by passing either a REQUEST object or
        name=value parameters

        Some objects have "special" properties defined by product
        authors that cannot be changed. If you try to change one of
        these properties through this method, an error will be raised.

        Note that no type checking or conversion happens when this
        method is called, so it is the caller's responsibility to
        ensure that the updated values are of the correct type.
        *This should probably change*.

        If a REQUEST object is passed (as it will be when
        called via the web), the method will return an HTML message
        dialog. If no REQUEST is passed, the method returns 'None' on
        success.

        This method may be called via the web, from DTML or from
        Python code.

        Permission -- 'Manage Properties'

        """


    def manage_delProperties(ids=None, REQUEST=None):
        """

        Delete one or more properties with the given 'ids'. The 'ids'
        argument should be a sequence (tuple or list) containing the
        ids of the properties to be deleted. If 'ids' is empty no
        action will be taken. If any of the properties named in 'ids'
        does not exist, an error will be raised.

        Some objects have "special" properties defined by product
        authors that cannot be deleted. If one of these properties is
        named in 'ids', an HTML error message is returned.

        If no value is passed in for 'REQUEST', the method will return
        None. If a value is provided for 'REQUEST' (as it will be when
        called via the web), the property management form for the
        object will be rendered and returned.

        This method may be called via the web, from DTML or from
        Python code.

        Permission -- 'Manage Properties'

        """
