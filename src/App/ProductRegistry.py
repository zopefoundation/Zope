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

# Product registry and new product factory model.  There will be a new
# mechanism for defining actions for meta types.  If an action is of
# the form:
#
#  manage_addProduct-name-factoryid
#
# Then the machinery that invokes an add-product form
# will return:
# ....what?

class ProductRegistryMixin:
    # This class implements a protocol for registering products that
    # are defined through the web.

    # This class is a mix-in class for the top-level application object.

    def _manage_remove_product_meta_type(self, product,
                                         id=None, meta_type=None):
        r=[]
        pid=product.id
        for mt in self._getProductRegistryMetaTypes():
            if 'product' in mt:
                if mt['product']==pid and (
                    meta_type is None or meta_type==mt['name']):
                    continue
                elif meta_type==mt['name']: continue
                r.append(mt)

        self._setProductRegistryMetaTypes(tuple(r))

    def _constructor_prefix_string(self, pid):
        return 'manage_addProduct/%s/' % pid

    def _manage_add_product_meta_type(self, product, id, meta_type,
                                      permission=''):
        pid=product.id

        meta_types=self._getProductRegistryMetaTypes()

        for mt in meta_types:
            if mt['name']==meta_type:
                if 'product' not in mt: mt['product']=pid
                if mt['product'] != pid:
                    raise ValueError, (
                        'The type <em>%s</em> is already defined.' % meta_type)
                mt['action']='%s%s' % (
                    self._constructor_prefix_string(pid), id)
                if permission: mt['permission']=permission
                return

        mt={
            'name': meta_type,
            'action': ('%s%s' % (
                self._constructor_prefix_string(pid), id)),
            'product': pid
            }
        if permission: mt['permission']=permission

        self._setProductRegistryMetaTypes(meta_types+(mt,))

    # HACK - sometimes an unwrapped App object seems to be passed as
    # self to these methods, which means that they dont have an aq_aquire
    # method. Until Jim has time to look into this, this aq_maybe method
    # appears to be an effective work-around...
    def aq_maybe(self, name):
        if hasattr(self, name):
            return getattr(self, name)
        return self.aq_acquire(name)

    def _manage_add_product_data(self, type, product, id, **data):
        values=filter(
            lambda d, product=product, id=id:
            not (d['product']==product and d['id']==id),
            list(self.aq_maybe('_getProductRegistryData')(type))
            )

        data['product']=product
        data['id']=id
        values.append(data)

        self.aq_maybe('_setProductRegistryData')(type, tuple(values))

    def _manage_remove_product_data(self, type, product, id):
        values=filter(
            lambda d, product=product, id=id:
            not (d['product']==product and d['id']==id),
            self.aq_maybe('_getProductRegistryData')(type)
            )

        self.aq_maybe('_setProductRegistryData')(type, tuple(values))


class ProductRegistry(ProductRegistryMixin):
    # This class implements a protocol for registering products that
    # are defined through the web.  It also provides methods for
    # getting hold of the Product Registry, Control_Panel.Products.

    # This class is a mix-in class for the top-level application object.

    def _getProducts(self): return self.Control_Panel.Products

    _product_meta_types=()

    def _getProductRegistryMetaTypes(self):
        return self._product_meta_types

    def _setProductRegistryMetaTypes(self, v):
        self._product_meta_types=v

    def _getProductRegistryData(self, name):
        return getattr(self, '_product_%s' % name)

    def _setProductRegistryData(self, name, v):
        name='_product_%s' % name
        if hasattr(self, name):
            return setattr(self, name, v)
        else:
            raise AttributeError, name
