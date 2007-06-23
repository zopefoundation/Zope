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
__doc__='''Factory objects

$Id$'''
__version__='$Revision: 1.27 $'[11:-2]

import OFS.SimpleItem, Acquisition, Globals, AccessControl.Role
from Globals import InitializeClass
from AccessControl import ClassSecurityInfo
from AccessControl.Permissions import edit_factories
from AccessControl.Permissions import use_factories

class Factory(
    AccessControl.Role.RoleManager,
    Globals.Persistent, Acquisition.Implicit, OFS.SimpleItem.Item
    ):
    "Model factory meta-data"
    meta_type='Zope Factory'
    icon='p_/Factory_icon'

    security = ClassSecurityInfo()
    security.declareObjectProtected(use_factories)

    permission='' # Waaaa

    _setObject=_getOb=Acquisition.Acquired

    manage_options=(
        (
        {'label':'Edit', 'action':'manage_main',
         'help':('OFSP','Zope-Factory_Edit.stx')},
        )
        +AccessControl.Role.RoleManager.manage_options
        +OFS.SimpleItem.Item.manage_options
        )

    def __init__(self, id, title, object_type, initial, permission=''):
        self.id=id
        self.title=title
        self.object_type=object_type
        self.initial=initial
        self.permission=permission

    security.declarePrivate('initializePermission')
    def initializePermission(self):
        self.manage_setPermissionMapping((use_factories,),
                                         (self.permission,))

    security.declareProtected(edit_factories, 'manage_edit')
    def manage_edit(self, title, object_type, initial, permission='',
                    REQUEST=None):
        "Modify factory properties."
        self._unregister()
        self.title=title
        self.object_type=object_type
        self.initial=initial
        self.permission=permission
        self.manage_setPermissionMapping((use_factories,), (permission,))
        self._register()
        if REQUEST is not None: return self.manage_main(self, REQUEST)

    def manage_afterAdd(self, item, container):
        import Product  # local to avoid circular import
        if hasattr(self, 'aq_parent'):
            container=self.aq_parent
        elif item is not self:
            container=None
        if (item is self or
            getattr(container, '__class__', None) is Product.Product):
            self._register()

    def manage_beforeDelete(self, item, container):
        import Product  # local to avoid circular import
        if hasattr(self, 'aq_parent'):
            container=self.aq_parent
        elif item is not self:
            container=None

        if (item is self or
            getattr(container, '__class__', None) is Product.Product):
            self._unregister()

    def _register(self):
        # Register with the product folder
        product=self.aq_parent
        product.aq_acquire('_manage_add_product_meta_type')(
            product, self.id, self.object_type, self.permission)

    def _unregister(self):
        # Unregister with the product folder
        product=self.aq_parent
        product.aq_acquire('_manage_remove_product_meta_type')(
            product, self.id, self.object_type)

    security.declareProtected(edit_factories, 'manage_main')
    manage_main=Globals.DTMLFile('dtml/editFactory',globals())

    security.declareProtected(use_factories, 'index_html')
    def index_html(self, REQUEST):
        " "
        return getattr(self, self.initial)(self.aq_parent, REQUEST)

    def objectIds(self):
        return filter(
            lambda id, myid=self.id: id != myid,
            self.aq_parent.objectIds()
            )

InitializeClass(Factory)


class ProductFactory(Factory): pass
