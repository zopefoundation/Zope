
from InterfaceBase import InterfaceBase

class Attribute(InterfaceBase):
    """Attribute descriptions
    """
    
    def __init__(self, __name__=None, __doc__=None):
        """Create an 'attribute' description
        """
        self.__name__=__name__
        self.__doc__=__doc__ or __name__
        self.__tagged_values = {}




