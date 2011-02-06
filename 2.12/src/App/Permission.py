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
__doc__='''Zope registerable permissions

$Id$'''
__version__='$Revision: 1.9 $'[11:-2]

from AccessControl.Permissions import view_management_screens
from AccessControl.Permissions import define_permissions
from AccessControl.Role import RoleManager
from AccessControl.SecurityInfo import ClassSecurityInfo
from Acquisition import Implicit
from App.class_init import InitializeClass
from App.special_dtml import DTMLFile
from ExtensionClass import Base
from OFS.SimpleItem import Item
from Persistence import Persistent

class Permission(RoleManager,
                 Persistent,
                 Implicit,
                 Item
                ):
    """Model Permission meta-data
    """
    meta_type = 'Zope Permission'
    icon = 'p_/Permission_icon'
    security = ClassSecurityInfo()

    manage_options=(
        (
        {'label':'Edit', 'action':'manage_main',
         'help':('OFSP', 'Zope-Permission_Edit.stx')},
        )
        + RoleManager.manage_options
        + Item.manage_options
        )

    def __init__(self, id, title, name):
        self.id=id
        self.title=title
        self.name=name

    security.declareProtected(define_permissions, 'manage_edit')
    def manage_edit(self, title, name, REQUEST=None):
        "Modify Permission properties."
        if title != self.title: self.title=title
        if name != self.name:
            self._unregister()
            self.name=name
            self._register()
        if REQUEST is not None: return self.manage_main(self, REQUEST)

    security.declarePrivate('manage_afterAdd')
    def manage_afterAdd(self, item, container):
        self._register()

    security.declarePrivate('manage_beforeDelete')
    def manage_beforeDelete(self, item, container):
        self._unregister()

    def _register(self):
        # Register with the product folder
        product = self.aq_parent
        product.aq_acquire('_manage_add_product_permission')(
            product, self.name)

    def _unregister(self):
        # Unregister with the product folder
        product = self.aq_parent
        product.aq_acquire('_manage_remove_product_permission')(
            product, self.name)

    security.declareProtected(view_management_screens, 'manage_main')
    manage_main = DTMLFile('dtml/editPermission', globals())

    index_html = None

InitializeClass(Permission)


class PermissionManager(Base):

    security = ClassSecurityInfo()

    meta_types={
        'name': Permission.meta_type, 'action': 'manage_addPermissionForm'
        },

    security.declareProtected(define_permissions, 'manage_addPermissionForm')
    manage_addPermissionForm = DTMLFile('dtml/addPermission', globals())

    security.declareProtected(define_permissions, 'manage_addPermission')
    def manage_addPermission(
        self, id, title, permission, REQUEST=None):
        """ Add a TTW permission.
        """
        i=Permission(id, title, permission)
        self._setObject(id, i)
        if REQUEST is not None:
            return self.manage_main(self, REQUEST, update_menu=1)

InitializeClass(PermissionManager)
