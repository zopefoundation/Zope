from Zope.Interfaces.Interface import Interface

from ItemInterface import ItemInterface
from PropertyManagerInterface import PropertyManagerInterface

class File:
    """
    Description of the Image interface
    """

    __extends__ = (ItemInterface,
                   PropertyManagerInterface,
                   )

    def id(self):
        """

        Returns the id of the file.

        """

    def update_data(self, data, content_type=None, size=None):
        """

        Updates the File with 'data'.

        """

    def getSize(self):
        """

        Returns the size of the file.

        """

    get_size = getSize

    def getContentType(self):
        """

        Returns the content type of the file.

        """


FileInterface=Interface(File) # create the interface object
