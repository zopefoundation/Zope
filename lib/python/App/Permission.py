##############################################################################
#
# Copyright (c) 2001 Zope Corporation and Contributors. All Rights Reserved.
# 
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
# 
##############################################################################
__doc__='''Zope registerable permissions

$Id: Permission.py,v 1.7 2001/11/28 15:50:52 matt Exp $'''
__version__='$Revision: 1.7 $'[11:-2]

import OFS.SimpleItem, Acquisition, Globals, ExtensionClass, AccessControl.Role

class Permission(
    AccessControl.Role.RoleManager,
    Globals.Persistent, Acquisition.Implicit, OFS.SimpleItem.Item
    ):
    "Model Permission meta-data"
    meta_type='Zope Permission'
    icon='p_/Permission_icon'

    manage_options=(
        (
        {'label':'Edit', 'action':'manage_main',
         'help':('OFSP','Zope-Permission_Edit.stx')},
        )
        +AccessControl.Role.RoleManager.manage_options
        +OFS.SimpleItem.Item.manage_options
        )
    
    def __init__(self, id, title, name):
        self.id=id
        self.title=title
        self.name=name

    def manage_edit(self, title, name, REQUEST=None):
        "Modify Permission properties."
        if title != self.title: self.title=title
        if name != self.name:
            self._unregister()
            self.name=name
            self._register()
        if REQUEST is not None: return self.manage_main(self, REQUEST)

    def manage_afterAdd(self, item, container):
        self._register()

    def manage_beforeDelete(self, item, container):
        self._unregister()

    def _register(self):
        # Register with the product folder
        product=self.aq_parent
        product.aq_acquire('_manage_add_product_permission')(
            product, self.name)

    def _unregister(self):
        # Unregister with the product folder
        product=self.aq_parent
        product.aq_acquire('_manage_remove_product_permission')(
            product, self.name)

    manage_main=Globals.DTMLFile('dtml/editPermission',globals())

    index_html=None

class PermissionManager(ExtensionClass.Base):

    __ac_permissions__=(
        ('Define permissions',
         ('manage_addPermissionForm', 'manage_addPermission')),
        )

    meta_types={
        'name': Permission.meta_type, 'action': 'manage_addPermissionForm'
        },

    manage_addPermissionForm=Globals.DTMLFile('dtml/addPermission',globals())
    def manage_addPermission(
        self, id, title, permission, REQUEST=None):
        ' '
        i=Permission(id, title, permission)
        self._setObject(id,i)
        if REQUEST is not None:
            return self.manage_main(self,REQUEST,update_menu=1)
    
