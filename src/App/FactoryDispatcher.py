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
from AccessControl.PermissionMapping import aqwrap
from AccessControl.SecurityInfo import ClassSecurityInfo
from Acquisition import Acquired
from Acquisition import Implicit
from Acquisition import aq_base
from ExtensionClass import Base
from OFS.metaconfigure import get_registered_packages


def _product_packages():
    """Returns all product packages including the regularly defined
    zope2 packages and those without the Products namespace package.
    """
    import Products

    _packages = {}
    for x in dir(Products):
        m = getattr(Products, x)
        if isinstance(m, types.ModuleType):
            _packages[x] = m

    for m in get_registered_packages():
        _packages[m.__name__] = m

    return _packages


class Product(Base):
    """Model a non-persistent product wrapper.
    """

    security = ClassSecurityInfo()

    meta_type = 'Product'
    version = ''
    thisIsAnInstalledProduct = True
    title = 'This is a non-persistent product wrapper.'

    def __init__(self, id):
        self.id = id

    @security.public
    def Destination(self):
        "Return the destination for factory output"
        return self


InitializeClass(Product)


class ProductDispatcher(Implicit):
    " "
    # Allow access to factory dispatchers
    __allow_access_to_unprotected_subobjects__ = 1

    def __getitem__(self, name):
        return self.__bobo_traverse__(None, name)

    def __bobo_traverse__(self, REQUEST, name):
        # Try to get a custom dispatcher from a Python product
        global _packages
        try:
            package = _packages[name]
        except (NameError, KeyError):
            _packages = _product_packages()
            package = _packages.get(name, None)

        dispatcher_class = getattr(
            package,
            '__FactoryDispatcher__',
            FactoryDispatcher)

        product = Product(name)
        dispatcher = dispatcher_class(product, self.__parent__, REQUEST)
        return dispatcher.__of__(self)


class FactoryDispatcher(Implicit):
    """Provide a namespace for product "methods"
    """

    security = ClassSecurityInfo()

    _owner = UnownableOwner

    def __init__(self, product, dest, REQUEST=None):
        product = aq_base(product)
        self._product = product
        self._d = dest
        if REQUEST is not None:
            try:
                v = REQUEST['URL']
            except KeyError:
                pass
            else:
                v = v[:v.rfind('/')]
                self._u = v[:v.rfind('/')]

    @security.public
    def Destination(self):
        "Return the destination for factory output"
        return self.__dict__['_d']  # we don't want to wrap the result!

    security.declarePublic('this')  # NOQA: D001
    this = Destination

    @security.public
    def DestinationURL(self):
        "Return the URL for the destination for factory output"
        url = getattr(self, '_u', None)
        if url is None:
            url = self.Destination().absolute_url()
        return url

    def __getattr__(self, name):
        p = self.__dict__['_product']
        d = p.__dict__
        if hasattr(p, name) and name in d:
            m = d[name]
            w = getattr(m, '_permissionMapper', None)
            if w is not None:
                m = aqwrap(m, aq_base(w), self)

            return m

        # Waaa
        m = 'Products.%s' % p.id
        if m in sys.modules and name in sys.modules[m]._m:  # NOQA
            return sys.modules[m]._m[name]

        raise AttributeError(name)

    # Provide acquired indicators for critical OM methods:
    _setObject = _getOb = Acquired

    # Make sure factory methods are unowned:
    _owner = UnownableOwner

    # Provide a replacement for manage_main that does a redirection:
    def manage_main(trueself, self, REQUEST, update_menu=0):
        """Implement a contents view by redirecting to the true view
        """
        REQUEST.RESPONSE.redirect(self.DestinationURL() + '/manage_main')


InitializeClass(FactoryDispatcher)
