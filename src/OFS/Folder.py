##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Folder object

Folders are the basic container objects and are analogous to directories.
"""

from AccessControl.class_init import InitializeClass
from App.special_dtml import DTMLFile
from OFS.FindSupport import FindSupport
from OFS.interfaces import IFolder
from OFS.Lockable import LockableItem
from OFS.ObjectManager import ObjectManager
from OFS.PropertyManager import PropertyManager
from OFS.role import RoleManager
from OFS.SimpleItem import Item
from OFS.SimpleItem import PathReprProvider
from webdav.Collection import Collection
from zope.interface import implementer


manage_addFolderForm = DTMLFile('dtml/folderAdd', globals())


def manage_addFolder(
    self,
    id,
    title='',
    createPublic=0,
    createUserF=0,
    REQUEST=None
):
    """Add a new Folder object with id *id*.
    """
    ob = Folder(id)
    ob.title = title
    self._setObject(id, ob)
    ob = self._getOb(id)
    if REQUEST is not None:
        return self.manage_main(self, REQUEST)


@implementer(IFolder)
class Folder(
    PathReprProvider,
    ObjectManager,
    PropertyManager,
    RoleManager,
    Collection,
    LockableItem,
    Item,
    FindSupport
):
    """Folders are basic container objects that provide a standard
    interface for object management. Folder objects also implement
    a management interface and can have arbitrary properties.
    """
    meta_type = 'Folder'
    zmi_icon = 'far fa-folder'

    _properties = (
        {
            'id': 'title',
            'type': 'string',
            'mode': 'wd',
        },
    )

    manage_options = (
        ObjectManager.manage_options
        + ({'label': 'View', 'action': ''}, )
        + PropertyManager.manage_options
        + RoleManager.manage_options
        + Item.manage_options
        + FindSupport.manage_options
    )

    __ac_permissions__ = ()

    def __init__(self, id=None):
        if id is not None:
            self.id = str(id)


InitializeClass(Folder)
