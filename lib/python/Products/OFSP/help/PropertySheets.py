"""
PropertySheets
"""

class PropertySheets:
    """

    A PropertySheet is an abstraction for organizing and working with
    a set of related properties. Conceptually it acts like a container
    for a set of related properties and metadata describing those
    properties. PropertySheet objects are accessed through a
    PropertySheets object that acts as a collection of PropertySheet
    instances.

    Objects that support property sheets (objects that support the
    PropertyManager interface or ZClass objects) have a
    'propertysheets'

    attribute (a PropertySheets instance) that is the collection of
    PropertySheet objects. The PropertySheets object exposes an
    interface much like a Python mapping, so that individual
    PropertySheet objects

    may be accessed via dictionary-style key indexing.


    """
    
    def values(self):
        """

        Return a sequence of all of the PropertySheet objects for
        in the collection.

        """

    def items(self):
        """

        Return a sequence containing an '(id, object)' tuple for
        each PropertySheet object in the collection.

        """

    def get(self, name, default=None):
        """

        Return the PropertySheet identified by 'name', or the value
        given in 'default' if the named PropertySheet is not found.

        """
