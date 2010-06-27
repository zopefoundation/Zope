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


# Implement the manage_addProduct method of object managers
import sys
import types

from AccessControl.class_init import InitializeClass
from AccessControl.owner import UnownableOwner
from AccessControl.SecurityInfo import ClassSecurityInfo
from AccessControl.PermissionMapping import aqwrap
from Acquisition import Acquired
from Acquisition import aq_base
from Acquisition import Implicit
from ExtensionClass import Base
from OFS.metaconfigure import get_registered_packages


def _product_packages():
    """Returns all product packages including the regularly defined
    zope2 packages and those without the Products namespace package.
    """
    import Products
    packages = {}
    for x in dir(Products):
        m = getattr(Products, x)
        if isinstance(m, types.ModuleType):
            packages[x] = m

    for m in get_registered_packages():
        packages[m.__name__] = m

    return packages


class Product(Base):
    """Model a non-persistent product wrapper.
    """

    security = ClassSecurityInfo()

    meta_type='Product'
    icon='p_/Product_icon'
    version=''
    configurable_objects_=()
    import_error_=None
    thisIsAnInstalledProduct = True
    title = 'This is a non-persistent product wrapper.'

    def __init__(self, id):
        self.id=id

    security.declarePublic('Destination')
    def Destination(self):
        "Return the destination for factory output"
        return self

    def getProductHelp(self):
        """Returns the ProductHelp object associated with the Product.
        """
        from HelpSys.HelpSys import ProductHelp
        return ProductHelp('Help', self.id).__of__(self)

InitializeClass(Product)


class ProductDispatcher(Implicit):
    " "
    # Allow access to factory dispatchers
    __allow_access_to_unprotected_subobjects__=1

    def __getitem__(self, name):
        return self.__bobo_traverse__(None, name)

    def __bobo_traverse__(self, REQUEST, name):
        # Try to get a custom dispatcher from a Python product
        dispatcher_class=getattr(
            _product_packages().get(name, None),
            '__FactoryDispatcher__',
            FactoryDispatcher)

        productfolder = self.aq_acquire('_getProducts')()
        try:
            product = productfolder._product(name)
        except AttributeError:
            # If we do not have a persistent product entry, return 
            product = Product(name)

        dispatcher=dispatcher_class(product, self.aq_parent, REQUEST)
        return dispatcher.__of__(self)

class FactoryDispatcher(Implicit):
    """Provide a namespace for product "methods"
    """

    security = ClassSecurityInfo()

    _owner=UnownableOwner

    def __init__(self, product, dest, REQUEST=None):
        product = aq_base(product)
        self._product=product
        self._d=dest
        if REQUEST is not None:
            try:
                v=REQUEST['URL']
            except KeyError: pass
            else:
                v=v[:v.rfind('/')]
                self._u=v[:v.rfind('/')]

    security.declarePublic('Destination')
    def Destination(self):
        "Return the destination for factory output"
        return self.__dict__['_d'] # we don't want to wrap the result!

    security.declarePublic('this')
    this=Destination

    security.declarePublic('DestinationURL')
    def DestinationURL(self):
        "Return the URL for the destination for factory output"
        url=getattr(self, '_u', None)
        if url is None:
            url=self.Destination().absolute_url()
        return url

    def __getattr__(self, name):
        p=self.__dict__['_product']
        d=p.__dict__
        if hasattr(p,name) and d.has_key(name):
            m=d[name]
            w=getattr(m, '_permissionMapper', None)
            if w is not None:
                m=aqwrap(m, aq_base(w), self)

            return m

        # Waaa
        m = 'Products.%s' % p.id
        if sys.modules.has_key(m) and sys.modules[m]._m.has_key(name):
            return sys.modules[m]._m[name]

        raise AttributeError, name

    # Provide acquired indicators for critical OM methods:
    _setObject = _getOb = Acquired

    # Make sure factory methods are unowned:
    _owner=UnownableOwner

    # Provide a replacement for manage_main that does a redirection:
    def manage_main(trueself, self, REQUEST, update_menu=0):
        """Implement a contents view by redirecting to the true view
        """
        d = update_menu and '/manage_main?update_menu=1' or '/manage_main'
        REQUEST['RESPONSE'].redirect(self.DestinationURL()+d)

InitializeClass(FactoryDispatcher)
