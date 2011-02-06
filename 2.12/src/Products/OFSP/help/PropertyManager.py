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

class PropertyManager:
    """
    A Property Manager object has a collection of typed attributes
    called properties. Properties can be managed through the web or
    via DTML.

    In addition to having a type, properties can be writable or
    read-only and can have default values.
    """

    def getProperty(id, d=None):
        """
        Return the value of the property 'id'. If the property is not
        found the optional second argument or None is returned.

        Permission -- 'Access contents information'
        """

    def getPropertyType(id):
        """
        Get the type of property 'id'. Returns None if no such
        property exists.

        Permission -- 'Access contents information'
        """

    def hasProperty(id):
        """
        Returns a true value if the Property Manager has the property
        'id'. Otherwise returns a false value.

        Permission -- 'Access contents information'
        """

    def propertyIds():
        """
        Returns a list of property ids.

        Permission -- 'Access contents information'
        """

    def propertyValues():
        """
        Returns a list of property values.

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
        The meta-data includes 'id', 'type', and 'mode'.

        Permission -- 'Access contents information'
        """
