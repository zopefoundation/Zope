##############################################################################
# 
# Zope Public License (ZPL) Version 1.0
# -------------------------------------
# 
# Copyright (c) Digital Creations.  All rights reserved.
# 
# This license has been certified as Open Source(tm).
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
# 
# 1. Redistributions in source code must retain the above copyright
#    notice, this list of conditions, and the following disclaimer.
# 
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions, and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
# 
# 3. Digital Creations requests that attribution be given to Zope
#    in any manner possible. Zope includes a "Powered by Zope"
#    button that is installed by default. While it is not a license
#    violation to remove this button, it is requested that the
#    attribution remain. A significant investment has been put
#    into Zope, and this effort will continue if the Zope community
#    continues to grow. This is one way to assure that growth.
# 
# 4. All advertising materials and documentation mentioning
#    features derived from or use of this software must display
#    the following acknowledgement:
# 
#      "This product includes software developed by Digital Creations
#      for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
#    In the event that the product being advertised includes an
#    intact Zope distribution (with copyright and license included)
#    then this clause is waived.
# 
# 5. Names associated with Zope or Digital Creations must not be used to
#    endorse or promote products derived from this software without
#    prior written permission from Digital Creations.
# 
# 6. Modified redistributions of any form whatsoever must retain
#    the following acknowledgment:
# 
#      "This product includes software developed by Digital Creations
#      for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
#    Intact (re-)distributions of any official Zope release do not
#    require an external acknowledgement.
# 
# 7. Modifications are encouraged but must be packaged separately as
#    patches to official Zope releases.  Distributions that do not
#    clearly separate the patches from the original work must be clearly
#    labeled as unofficial distributions.  Modifications which do not
#    carry the name Zope may be packaged in any form, as long as they
#    conform to all of the clauses above.
# 
# 
# Disclaimer
# 
#   THIS SOFTWARE IS PROVIDED BY DIGITAL CREATIONS ``AS IS'' AND ANY
#   EXPRESSED OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
#   IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
#   PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL DIGITAL CREATIONS OR ITS
#   CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
#   SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
#   LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF
#   USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#   ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
#   OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT
#   OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
#   SUCH DAMAGE.
# 
# 
# This software consists of contributions made by Digital Creations and
# many individuals on behalf of Digital Creations.  Specific
# attributions are listed in the accompanying credits file.
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

from OFS.Folder import Folder

class ProductRegistryMixin:
    # This class implements a protocol for registering products that
    # are defined through the web.

    # This class is a mix-in class for the top-level application object.
    
    def _manage_remove_product_meta_type(self, product,
                                         id=None, meta_type=None):
        r=[]
        pid=product.id
        for mt in self._getProductRegistryMetaTypes():
            if mt.has_key('product'):
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
                if not mt.has_key('product'): mt['product']=pid
                if mt['product'] != pid:
                    raise 'Type Exists', (
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
    
    def _manage_remove_product_permission(self, product, permission=None):
        r=[]
        r2=[]
        pid=product.id
        for d in self._getProductRegistryData('permissions'):
            if d.has_key('product'):
                if d['product']==pid and (
                    permission is None or permission==d['name']):
                    continue
                elif permission==d['name']: continue
                r.append(d)
                r2.append((d['name'], d['methods'], d['default']))
            
        self._setProductRegistryData('permissions', tuple(r))
        self._setProductRegistryData('ac_permissions', tuple(r2))

    def _manage_add_product_permission(
        self, product, permission, methods=(), default=('Manager',)
        ):

        permissions=self._getProductRegistryData('permissions')

        for d in permissions:
            if d['name']==permission:
                raise 'Type Exists', (
                    'The permission <em>%s</em> is already defined.'
                    % permission)
        
        d={'name': permission, 'methods': methods, 'permission': permission,
                'default': default, 'product': product.id}
        
        self._setProductRegistryData('permissions', permissions + (d,))
        self._setProductRegistryData(
            'ac_permissions',
            self._getProductRegistryData('ac_permissions')
            +((d['name'], d['methods'], d['default']),)
            )

    def _manage_add_product_data(self, type, product, id, **data):
        values=filter(
            lambda d, product=product, id=id:
            not (d['product']==product and d['id']==id),
            list(self.aq_acquire('_getProductRegistryData')(type))
            )

        data['product']=product
        data['id']=id
        values.append(data)

        self.aq_acquire('_setProductRegistryData')(type, tuple(values))

    def _manage_remove_product_data(self, type, product, id):
        values=filter(
            lambda d, product=product, id=id:
            not (d['product']==product and d['id']==id),
            self.aq_acquire('_getProductRegistryData')(type)
            )

        self.aq_acquire('_setProductRegistryData')(type, tuple(values))



class ProductRegistry(ProductRegistryMixin):
    # This class implements a protocol for registering products that
    # are defined through the web.  It also provides methods for
    # getting hold of the Product Registry, Control_Panel.Products.

    # This class is a mix-in class for the top-level application object.

    def _getProducts(self): return self.Control_Panel.Products

    _product_meta_types=()
    _product_permissions=()
    _product_ac_permissions=()

    _product_zclasses=() # product, id, meta_type, class


    def _getProductRegistryMetaTypes(self): return self._product_meta_types
    def _setProductRegistryMetaTypes(self, v): self._product_meta_types=v

    def _getProductRegistryData(self, name):
        return getattr(self, '_product_%s' % name)

    def _setProductRegistryData(self, name, v):
        name='_product_%s' % name
        if hasattr(self, name):
            return setattr(self, name, v)
        else:
            raise AttributeError, name


