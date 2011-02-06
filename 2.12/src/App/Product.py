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
"""Product objects
"""
# The new Product model:
#
#   Products may be defined in the Products folder or by placing directories
#   in lib/python/Products.
#
#   Products in lib/python/Products may have up to three sources of information:
#
#       - Static information defined via Python.  This information is
#         described and made available via __init__.py.
#
#       - Dynamic object data that gets copied into the Bobobase.
#         This is contained in product.dat (which is obfuscated).
#
#       - Static extensions supporting the dynamic data.  These too
#         are obfuscated.
#
#   Products may be copied and pasted only within the products folder.
#
#   If a product is deleted (or cut), it is automatically recreated
#   on restart if there is still a product directory.


import os

import transaction

from AccessControl.Owned import UnownableOwner
from AccessControl.SecurityInfo import ClassSecurityInfo
from AccessControl.unauthorized import Unauthorized
from App.class_init import InitializeClass
from App.special_dtml import DTMLFile
from OFS.Folder import Folder

from App.Permission import PermissionManager


class ProductFolder(Folder):
    "Manage a collection of Products"

    id = 'Products'
    name = title = 'Product Management'
    meta_type = 'Product Management'
    icon = 'p_/ProductFolder_icon'

    all_meta_types=()
    meta_types=()

    # This prevents subobjects from being owned!
    _owner = UnownableOwner

    def _product(self, name):
        return getattr(self, name)

    def _canCopy(self, op=0):
        return 0

InitializeClass(ProductFolder)


class Product(Folder, PermissionManager):
    """Model a product that can be created through the web.
    """

    security =  ClassSecurityInfo()

    meta_type='Product'
    icon='p_/Product_icon'
    version=''
    configurable_objects_=()
    import_error_=None

    meta_types=(
        PermissionManager.meta_types
        )

    manage_options = (
        (Folder.manage_options[0],) +
        tuple(Folder.manage_options[2:]) 
        )

    _properties = Folder._properties+(
        {'id':'version', 'type': 'string'},
        )

    _reserved_names=('Help',)

    def __init__(self, id, title):
        from HelpSys.HelpSys import ProductHelp

        self.id = id
        self.title = title
        self._setObject('Help', ProductHelp('Help', id))

    security.declarePublic('Destination')
    def Destination(self):
        "Return the destination for factory output"
        return self

    security.declarePublic('DestinationURL')
    def DestinationURL(self):
        "Return the URL for the destination for factory output"
        return self.REQUEST['BASE4']


    manage_traceback = DTMLFile('dtml/traceback', globals())
    manage_readme = DTMLFile('dtml/readme', globals())
    def manage_get_product_readme__(self):
        for name in ('README.txt', 'README.TXT', 'readme.txt'):
            path = os.path.join(self.home, name)
            if os.path.isfile(path):
                return open(path).read()
        return ''

    def permissionMappingPossibleValues(self):
        return self.possible_permissions()

    def getProductHelp(self):
        """Returns the ProductHelp object associated with the Product.
        """
        from HelpSys.HelpSys import ProductHelp
        if not hasattr(self, 'Help'):
            self._setObject('Help', ProductHelp('Help', self.id))
        return self.Help

    #
    # Product refresh
    #

    _refresh_dtml = DTMLFile('dtml/refresh', globals())

    def _readRefreshTxt(self, pid=None):
        import Products
        refresh_txt = None
        if pid is None:
            pid = self.id
        for productDir in Products.__path__:
            found = 0
            for name in ('refresh.txt', 'REFRESH.txt', 'REFRESH.TXT'):
                p = os.path.join(productDir, pid, name)
                if os.path.exists(p):
                    found = 1
                    break
            if found:
                try:
                    file = open(p)
                    text = file.read()
                    file.close()
                    refresh_txt = text
                    break
                except:
                    # Not found here.
                    pass
        return refresh_txt

    def manage_performRefresh(self, REQUEST=None):
        """ Attempts to perform a refresh operation.
        """
        from App.RefreshFuncs import performFullRefresh
        if self._readRefreshTxt() is None:
            raise Unauthorized, 'refresh.txt not found'
        message = None
        if performFullRefresh(self._p_jar, self.id):
            from ZODB import Connection
            Connection.resetCaches() # Clears cache in future connections.
            message = 'Product refreshed.'
        else:
            message = 'An exception occurred.'
        if REQUEST is not None:
            return self.manage_refresh(REQUEST, manage_tabs_message=message)

    def manage_enableAutoRefresh(self, enable=0, REQUEST=None):
        """ Changes the auto refresh flag for this product.
        """
        from App.RefreshFuncs import enableAutoRefresh
        if self._readRefreshTxt() is None:
            raise Unauthorized, 'refresh.txt not created'
        enableAutoRefresh(self._p_jar, self.id, enable)
        if enable:
            message = 'Enabled auto refresh.'
        else:
            message = 'Disabled auto refresh.'
        if REQUEST is not None:
            return self.manage_refresh(REQUEST, manage_tabs_message=message)

    def manage_selectDependentProducts(self, selections=(), REQUEST=None):
        """ Selects which products to refresh simultaneously.
        """
        from App.RefreshFuncs import setDependentProducts
        if self._readRefreshTxt() is None:
            raise Unauthorized, 'refresh.txt not created'
        setDependentProducts(self._p_jar, self.id, selections)
        if REQUEST is not None:
            return self.manage_refresh(REQUEST)

InitializeClass(Product)


def initializeProduct(productp, name, home, app):
    # Initialize a levered product
    import Globals  # to set data
    products = app.Control_Panel.Products
    fver = ''

    if hasattr(productp, '__import_error__'): ie=productp.__import_error__
    else: ie=None

    # Retrieve version number from any suitable version.txt
    for fname in ('version.txt', 'VERSION.txt', 'VERSION.TXT'):
        try:
            fpath = os.path.join(home, fname)
            fhandle = open(fpath, 'r')
            fver = fhandle.read().strip()
            fhandle.close()
            break
        except IOError:
            continue

    old=None
    try:
        if ihasattr(products,name):
            old=getattr(products, name)
            if ihasattr(old,'version') and old.version==fver:
                if hasattr(old, 'import_error_') and \
                   old.import_error_==ie:
                    # Version hasn't changed. Don't reinitialize.
                    return old
    except: pass

    f = fver and (" (%s)" % fver)
    product=Product(name, 'Installed product %s%s' % (name,f))

    if old is not None:
        app._manage_remove_product_meta_type(product)
        products._delObject(name)
        for id, v in old.objectItems():
            try: product._setObject(id, v)
            except: pass

    products._setObject(name, product)
    product.icon='p_/InstalledProduct_icon'
    product.version=fver
    product.home=home
    product.thisIsAnInstalledProduct=1

    if ie:
        product.import_error_=ie
        product.title='Broken product %s' % name
        product.icon='p_/BrokenProduct_icon'
        product.manage_options=(
            {'label':'Traceback', 'action':'manage_traceback'},
            )

    for name in ('README.txt', 'README.TXT', 'readme.txt'):
        path = os.path.join(home, name)
        if os.path.isfile(path):
            product.manage_options=product.manage_options+(
                {'label':'README', 'action':'manage_readme'},
                )
            break

    # Ensure this product has a refresh tab.
    found = 0
    for option in product.manage_options:
        if option.get('label') == 'Refresh':
            found = 1
            break
    if not found:
        product.manage_options = product.manage_options + (
            {'label':'Refresh', 'action':'manage_refresh',
             'help': ('OFSP','Product_Refresh.stx')},)

    if not doInstall():
        transaction.abort()
        return product

    return product

def ihasattr(o, name):
    return hasattr(o, name) and o.__dict__.has_key(name)


def doInstall():
    from App.config import getConfiguration
    return getConfiguration().enable_product_installation

