"""
InterfaceImplementer -- Mixin class for objects that support interfaces
"""

class InterfaceImplementer:
    """
    Mix-in class to support interfaces.
    Interface implementation is indicated
    with the __implements__ class attribute
    that should be a tuple of Interface objects.
    """
    def implementedInterfaces(self):
        """
        Returns a sequence of Interface objects
        that the object implements.
        """
        return self.__implements__
