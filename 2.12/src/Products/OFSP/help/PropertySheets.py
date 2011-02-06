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


class PropertySheets:
    """

    A PropertySheet is an abstraction for organizing and working with
    a set of related properties. Conceptually it acts like a container
    for a set of related properties and meta-data describing those
    properties. PropertySheet objects are accessed through a
    PropertySheets object that acts as a collection of PropertySheet
    instances.

    Objects that support property sheets (objects that support the
    PropertyManager interface) have a
    'propertysheets' attribute (a PropertySheets instance) that is the
    collection of PropertySheet objects. The PropertySheets object
    exposes an interface much like a Python mapping, so that
    individual PropertySheet objects may be accessed via
    dictionary-style key indexing.

    """

    def values():
        """

        Return a sequence of all of the PropertySheet objects
        in the collection.

        Permission -- Python only

        """

    def items():
        """

        Return a sequence containing an '(id, object)' tuple for
        each PropertySheet object in the collection.

        Permission -- Python only

        """

    def get(name, default=None):
        """

        Return the PropertySheet identified by 'name', or the value
        given in 'default' if the named PropertySheet is not found.

        Permission -- Python only

        """
