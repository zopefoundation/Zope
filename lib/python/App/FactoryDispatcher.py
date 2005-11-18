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


# Implement the manage_addProduct method of object managers
import Acquisition, sys, Products
from AccessControl.PermissionMapping import aqwrap
from AccessControl.Owned import UnownableOwner

class ProductDispatcher(Acquisition.Implicit):
    " "
    # Allow access to factory dispatchers
    __allow_access_to_unprotected_subobjects__=1

    def __getitem__(self, name):
        return self.__bobo_traverse__(None, name)

    def __bobo_traverse__(self, REQUEST, name):
        product=self.aq_acquire('_getProducts')()._product(name)

        # Try to get a custom dispatcher from a Python product
        dispatcher_class=getattr(
            getattr(Products, name, None),
            '__FactoryDispatcher__',
            FactoryDispatcher)

        dispatcher=dispatcher_class(product, self.aq_parent, REQUEST)
        return dispatcher.__of__(self)

class FactoryDispatcher(Acquisition.Implicit):
    """Provide a namespace for product "methods"
    """

    _owner=UnownableOwner

    def __init__(self, product, dest, REQUEST=None):
        if hasattr(product,'aq_base'): product=product.aq_base
        self._product=product
        self._d=dest
        if REQUEST is not None:
            try:
                v=REQUEST['URL']
            except KeyError: pass
            else:
                v=v[:v.rfind('/')]
                self._u=v[:v.rfind('/')]

    def Destination(self):
        "Return the destination for factory output"
        return self.__dict__['_d'] # we don't want to wrap the result!
    this=Destination
    this__roles__=Destination__roles__=None


    def DestinationURL(self):
        "Return the URL for the destination for factory output"
        url=getattr(self, '_u', None)
        if url is None:
            url=self.Destination().absolute_url()
        return url

    DestinationURL__roles__=None

    def __getattr__(self, name):
        p=self.__dict__['_product']
        d=p.__dict__
        if hasattr(p,name) and d.has_key(name):
            m=d[name]
            w=getattr(m, '_permissionMapper', None)
            if w is not None:
                m=aqwrap(m, getattr(w,'aq_base',w), self)

            return m

        # Waaa
        m='Products.%s' % p.id
        if sys.modules.has_key(m) and sys.modules[m]._m.has_key(name):
            return sys.modules[m]._m[name]

        raise AttributeError, name

    # Provide acquired indicators for critical OM methods:
    _setObject=_getOb=Acquisition.Acquired

    # Make sure factory methods are unowned:
    _owner=UnownableOwner

    # Provide a replacement for manage_main that does a redirection:
    def manage_main(trueself, self, REQUEST, update_menu=0):
        """Implement a contents view by redirecting to the true view
        """
        d = update_menu and '/manage_main?update_menu=1' or '/manage_main'
        REQUEST['RESPONSE'].redirect(self.DestinationURL()+d)

