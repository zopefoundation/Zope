##############################################################################
#
# Copyright (c) 2002 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
"""Object-manager mix-in for ZClasses
"""

from App.special_dtml import DTMLFile
from OFS.ObjectManager import ObjectManager as BaseObjectManager
from OFS.PropertySheets import PropertySheet
from OFS.PropertySheets import PropertySheets
from OFS.PropertySheets import View

class SubobjectsSheet(PropertySheet, View):
    """Provide management view for selecting sub-objects.
    """
    manage = DTMLFile('dtml/subobjects', globals())

    def possible_meta_types(self):
        import Products
        return self.aq_acquire('_product_meta_types') + Products.meta_types

    def selected_meta_types(self):
        return map(lambda v: v['name'], self.getClassAttr('meta_types',()))

    def manage_edit(self, meta_types=(), isFolderish=None, REQUEST=None):
        "Edit object management properties"
        self.setClassAttr('meta_types', filter(
            lambda d, m=meta_types: d['name'] in m,
            self.possible_meta_types()
            ))
        self.setClassAttr('isPrincipiaFolderish', isFolderish)
        if REQUEST is not None:
            return self.manage(
                self, REQUEST,
                manage_tabs_message='Changes were applied'
                )

    def isFolderish(self):
        return self.getClassAttr('isPrincipiaFolderish', 0, 1)

class ZObjectManagerPropertySheets(PropertySheets):

    subobjects=SubobjectsSheet('subobjects')

class ObjectManager(BaseObjectManager):

    _zclass_method_meta_types=()

    def all_meta_types(self):
        return self.meta_types+self._zclass_method_meta_types

class ZObjectManager:
    """Mix-in for Object Management
    """
    _zclass_ = ObjectManager

    propertysheets=ZObjectManagerPropertySheets()

    manage_options=(
        {'label': 'Subobjects', 'action' :'propertysheets/subobjects/manage'},
        )
