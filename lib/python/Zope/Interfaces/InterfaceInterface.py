
from Interface import Interface

class _Interface:
    """ This is the Interface for Interface objects """

    def defered(self):
        """

        Returns a defered class corresponding to the interface

        """

    def extends(self, other):
        """

        Does this Interface extend 'other'?

        """

    def implementedBy(self, object):
        """

        Does 'object' implement this Interface?

        """

    def implementedByInstancesOf(self, klass):
        """

        Do instances of the given class implement the interface?

        """

    def implements(self):
        """

        Returns a sequence of base interfaces

        """

    def names(self):
        """

        Returns the attribute names defined by the interface

        """

    def namesAndDescriptions(self):
        """

        Return the attribute names and descriptions defined by the interface

        """

    def getDescriptionFor(self, name, default=None):
        """

        Return the attribute description for the given name

        """


InterfaceInterface = Interface(_Interface, 'InterfaceInterface')


