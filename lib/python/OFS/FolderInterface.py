from Zope.Interfaces.Interface import Interface

from ObjectManagerInterface import ObjectManagerInterface
from PropertyManagerInterface import PropertyManagerInterface
from AccessControl.RoleManagerInterface import RoleManagerInterface
from ItemInterface import ItemInterface
from FindSupportInterface import FindSupportInterface

class Folder:
    """

    A Folder object can contain other Zope objects, including other
    Folders.  It is the generic 'container' object for Zope managment.
    It is analogous to a UNIX 'directory' or a Windows 'Folder'.

    """

    __extends__ = (ObjectManagerInterface,
                   PropertyManagerInterface,
                   RoleManagerInterface,
                   ItemInterface,
                   FindSupportInterface,
                   )

    
FolderInterface=Interface(Folder) # create the interface object
