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
__doc__='''Factory objects

$Id$'''
__version__='$Revision: 1.27 $'[11:-2]

import OFS.SimpleItem, Acquisition, Globals, AccessControl.Role

class Factory(
    AccessControl.Role.RoleManager,
    Globals.Persistent, Acquisition.Implicit, OFS.SimpleItem.Item
    ):
    "Model factory meta-data"
    meta_type='Zope Factory'
    icon='p_/Factory_icon'

    permission='' # Waaaa

    _setObject=_getOb=Acquisition.Acquired

    __ac_permissions__=(
        ('Edit Factories', ('manage_edit','manage_main')),
        ('Use Factories', ('index_html','')),
        )

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

    initializePermission__roles__ = ()
    def initializePermission(self):
        self.manage_setPermissionMapping(('Use Factories',),
                                         (self.permission,))

    def manage_edit(self, title, object_type, initial, permission='',
                    REQUEST=None):
        "Modify factory properties."
        self._unregister()
        self.title=title
        self.object_type=object_type
        self.initial=initial
        self.permission=permission
        self.manage_setPermissionMapping(('Use Factories',), (permission,))
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

    manage_main=Globals.DTMLFile('dtml/editFactory',globals())

    def index_html(self, REQUEST):
        " "
        return getattr(self, self.initial)(self.aq_parent, REQUEST)

    def objectIds(self):
        return filter(
            lambda id, myid=self.id: id != myid,
            self.aq_parent.objectIds()
            )

class ProductFactory(Factory): pass
