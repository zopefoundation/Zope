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
'''
Functions for refreshing products.
'''

from logging import getLogger
import os
import sys
from time import time
from traceback import format_exception

from ExtensionClass import Base
from Persistence import PersistentMapping

LOG = getLogger('RefreshFuncs')
global_classes_timestamp = 0
products_mod_times = {}

_marker = []  # create a new marker object.

refresh_exc_info = {}

class dummyClass:
    pass

class dummyClass2(Base):
    pass

def dummyFunc():
    pass

ClassTypes = (type(dummyClass), type(dummyClass2))
ModuleType = type(sys)
FuncType = type(dummyFunc)

next_auto_refresh_check = 0
AUTO_REFRESH_INTERVAL = 2  # 2 seconds.

# Functions for storing and retrieving the auto-refresh state for
# each product.

def _getCentralRefreshData(jar, create=0):
    root = jar.root()
    if root.has_key('RefreshData'):
        rd = root['RefreshData']
    else:
        rd = PersistentMapping()
        if create:
            root['RefreshData'] = rd
    return rd

def isAutoRefreshEnabled(jar, productid):
    rd = _getCentralRefreshData(jar)
    ids = rd.get('auto', None)
    if ids:
        return ids.get(productid, 0)
    else:
        return 0

def enableAutoRefresh(jar, productid, enable):
    productid = str(productid)
    rd = _getCentralRefreshData(jar, 1)
    ids = rd.get('auto', None)
    if ids is None:
        if enable:
            rd['auto'] = ids = PersistentMapping()
        else:
            return
    if enable:
        ids[productid] = 1
    else:
        if ids.has_key(productid):
            del ids[productid]

def listAutoRefreshableProducts(jar):
    rd = _getCentralRefreshData(jar)
    auto = rd.get('auto', None)
    if auto:
        ids = []
        for k, v in auto.items():
            if v:
                ids.append(k)
        return ids
    else:
        return ()

def getDependentProducts(jar, productid):
    rd = _getCentralRefreshData(jar)
    products = rd.get('products', None)
    if products is None:
        return ()
    product = products.get(productid, None)
    if product is None:
        return ()
    return product.get('dependent_products', ())

def setDependentProducts(jar, productid, dep_ids):
    productid = str(productid)
    rd = _getCentralRefreshData(jar, 1)
    products = rd.get('products', None)
    if products is None:
        rd['products'] = products = PersistentMapping()
    product = products.get(productid, None)
    if product is None:
        products[productid] = product = PersistentMapping()
    product['dependent_products'] = tuple(map(str, dep_ids))


# Functions for performing refresh.

def getReloadVar(module):
    reload_var = getattr(module, '__refresh_module__', _marker)
    if reload_var is _marker:
        reload_var = getattr(module, '__reload_module__', _marker)
    if reload_var is _marker:
        reload_var = 1
    return reload_var

def listRefreshableModules(productid):
    prefix = "Products.%s" % productid
    prefixdot = prefix + '.'
    lpdot = len(prefixdot)
    rval = []
    for name, module in sys.modules.items():
        if module and (name == prefix or name[:lpdot] == prefixdot):
            reload_var = getReloadVar(module)
            if reload_var:
                rval.append((name, module))
    return rval

def logBadRefresh(productid):
    exc = sys.exc_info()
    try:
        LOG.error('Exception while refreshing %s' % productid, exc_info=exc)
        if hasattr(exc[0], '__name__'):
            error_type = exc[0].__name__
        else:
            error_type = str(exc[0])
        error_value = str(exc[1])
        info = ''.join(format_exception(exc[0], exc[1], exc[2], limit=200))
        refresh_exc_info[productid] = (error_type, error_value, info)
    finally:
        exc = None

def performRefresh(jar, productid):
    '''Attempts to perform a refresh operation.
    '''
    refresh_exc_info[productid] = None
    setupModTimes(productid)  # Refresh again only if changed again.

    modlist = listRefreshableModules(productid)
    former_modules = {}
    try:
        # Remove modules from sys.modules but keep a handle
        # on the old modules in case there's a problem.
        for name, module in modlist:
            m = sys.modules.get(name, None)
            if m is not None:
                former_modules[name] = m
                del sys.modules[name]

        # Reimport and reinstall the product.
        from OFS import Application
        Application.reimport_product(productid)
        app = jar.root()['Application']
        Application.reinstall_product(app, productid)
        return 1
    except:
        # Couldn't refresh.  Reinstate removed modules.
        for name, module in former_modules.items():
            sys.modules[name] = module
        raise

def performSafeRefresh(jar, productid):
    try:
        LOG.info('Refreshing product %s' % productid)
        if not performRefresh(jar, productid):
            return 0
    except:
        logBadRefresh(productid)
        return 0
    else:
        return 1

def performFullRefresh(jar, productid):
    # Refresh dependent products also.
    if performSafeRefresh(jar, productid):
        dep_ids = getDependentProducts(jar, productid)
        for dep_id in dep_ids:
            if isAutoRefreshEnabled(jar, dep_id):
                if not performSafeRefresh(jar, dep_id):
                    return 0
    else:
        return 0
    return 1

def getLastRefreshException(productid):
    return refresh_exc_info.get(productid, None)

# Functions for quickly scanning the dates of product modules.

def tryFindProductDirectory(productid):
    import Products
    path_join = os.path.join
    isdir = os.path.isdir
    exists = os.path.exists

    for products_dir in Products.__path__:
        product_dir = path_join(products_dir, productid)
        if not isdir(product_dir): continue
        if not exists(path_join(product_dir, '__init__.py')):
            if not exists(path_join(product_dir, '__init__.pyc')):
                continue
        return product_dir
    return None

def tryFindModuleFilename(product_dir, filename):
    # Try different variations of the filename of a module.
    path_join = os.path.join
    isdir = os.path.isdir
    exists = os.path.exists

    found = None
    fn = path_join(product_dir, filename + '.py')
    if exists(fn):
        found = fn
    if not found:
        fn = fn + 'c'
        if exists(fn):
            found = fn
    if not found:
        fn = path_join(product_dir, filename)
        if isdir(fn):
            fn = path_join(fn, '__init__.py')
            if exists(fn):
                found = fn
            else:
                fn = fn + 'c'
                if exists(fn):
                    found = fn
    return found

def setupModTimes(productid):
    mod_times = []
    product_dir = tryFindProductDirectory(productid)
    if product_dir is not None:
        modlist = listRefreshableModules(productid)

        path_join = os.path.join
        exists = os.path.exists

        for name, module in modlist:
            splitname = name.split( '.')[2:]
            if not splitname:
                filename = '__init__'
            else:
                filename = apply(path_join, splitname)
            found = tryFindModuleFilename(product_dir, filename)

            if found:
                try: mtime = os.stat(found)[8]
                except: mtime = 0
                mod_times.append((found, mtime))
    products_mod_times[productid] = mod_times

def checkModTimes(productid):
    # Returns 1 if there were changes.
    mod_times = products_mod_times.get(productid, None)
    if mod_times is None:
        # Initialize the mod times.
        setupModTimes(productid)
        return 0
    for filename, mod_time in mod_times:
        try: mtime = os.stat(filename)[8]
        except: mtime = 0
        if mtime != mod_time:
            # Something changed!
            return 1
    return 0

# Functions for performing auto-refresh.

def checkAutoRefresh(jar):
    '''
    Returns the IDs of products that need to be auto-refreshed.
    '''
    # Note: this function is NOT allowed to change the database!
    global next_auto_refresh_check
    now = time()
    if next_auto_refresh_check and next_auto_refresh_check > now:
        # Not enough time has passed.
        return ()
    next_auto_refresh_check = now + AUTO_REFRESH_INTERVAL

    rd = _getCentralRefreshData(jar)
    ids = rd.get('auto', None)
    if not ids:
        return ()
    auto_refresh_ids = []
    for productid in ids.keys():
        if checkModTimes(productid):
            auto_refresh_ids.append(productid)
    return auto_refresh_ids

def finishAutoRefresh(jar, productids):
    # This function is allowed to change the database.
    for productid in productids:
        performFullRefresh(jar, productid)

def autoRefresh(jar):
    # Must be called before there are any changes made
    # by the connection to the database!
    import transaction
    auto_refresh_ids = checkAutoRefresh(jar)
    if auto_refresh_ids:
        finishAutoRefresh(jar, auto_refresh_ids)
        from ZODB import Connection
        Connection.resetCaches()
        transaction.commit()
        jar._resetCache()
        transaction.begin()

def setupAutoRefresh(jar):
    # Install hook.
    from App.ZApplication import connection_open_hooks
    connection_open_hooks.append(autoRefresh)
    # Init mod times.
    checkAutoRefresh(jar)
