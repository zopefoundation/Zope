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
from AccessControl.Permissions import add_page_templates
from AccessControl.Permissions import add_user_folders
from AccessControl.SecurityManagement import getSecurityManager
from AccessControl.unauthorized import Unauthorized
from App.special_dtml import DTMLFile
from webdav.Collection import Collection
from zope.interface import implements

from OFS.FindSupport import FindSupport
from OFS.interfaces import IFolder
from OFS.ObjectManager import ObjectManager
from OFS.PropertyManager import PropertyManager
from OFS.role import RoleManager
from OFS.SimpleItem import Item


manage_addFolderForm=DTMLFile('dtml/folderAdd', globals())

def manage_addFolder(self, id, title='',
                     createPublic=0,
                     createUserF=0,
                     REQUEST=None):
    """Add a new Folder object with id *id*.

    If the 'createPublic' and 'createUserF' parameters are set to any true
    value, an 'index_html' and a 'UserFolder' objects are created respectively
    in the new folder.
    """
    ob = Folder(id)
    ob.title = title
    self._setObject(id, ob)
    ob = self._getOb(id)

    checkPermission=getSecurityManager().checkPermission

    if createUserF:
        if not checkPermission(add_user_folders, ob):
            raise Unauthorized, (
                  'You are not authorized to add User Folders.'
                  )
        ob.manage_addUserFolder()

    if createPublic:
        if not checkPermission(add_page_templates, ob):
            raise Unauthorized, (
                  'You are not authorized to add Page Templates.'
                  )
        ob.manage_addProduct['PageTemplates'].manage_addPageTemplate(
            id='index_html', title='')

    if REQUEST is not None:
        return self.manage_main(self, REQUEST, update_menu=1)


class Folder(
    ObjectManager,
    PropertyManager,
    RoleManager,
    Collection,
    Item,
    FindSupport,
    ):

    """Folders are basic container objects that provide a standard
    interface for object management. Folder objects also implement
    a management interface and can have arbitrary properties.
    """

    implements(IFolder)
    meta_type='Folder'

    _properties=({'id':'title', 'type': 'string','mode':'wd'},)

    manage_options=(
        ObjectManager.manage_options +
        ({'label': 'View', 'action': ''}, ) +
        PropertyManager.manage_options +
        RoleManager.manage_options +
        Item.manage_options +
        FindSupport.manage_options
        )

    __ac_permissions__=()

    def __init__(self, id=None):
        if id is not None:
            self.id = str(id)

InitializeClass(Folder)
