from Zope.Interfaces.Interface import Interface

from ZDOMInterface import ElementInterface

class Item:
    """
    Description of the Item interface
    """

    __extends__ = (ElementInterface,)

    def title_or_id(self):
        """
        Descripotion
        
        """

    def title_and_id(self):
        """
        Description
        """

    def this(self):
        """
        description
        """

    def absolute_url(self, relative=1):
        """
        description
        """

ItemInterface=Interface(Item) # create the interface object

