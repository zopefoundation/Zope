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
'''
Functions for refreshing products.
$Id: RefreshFuncs.py,v 1.1 2001/05/17 18:35:08 shane Exp $
'''

import os, sys
from time import time
from string import split, join
import Products
from ExtensionClass import Base
from Globals import PersistentMapping
from zLOG import format_exception, LOG, ERROR, INFO

global_classes_timestamp = 0
products_mod_times = {}

_marker = []  # create a new marker object.

refresh_exc_info = {}

class dummyClass: pass
class dummyClass2 (Base): pass
def dummyFunc(): pass

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

# Functions for sorting modules by dependency.

def listRequiredModulesByClass(klass, rval):
    if hasattr(klass, '__module__'):
        rval[klass.__module__] = 1 # klass.__module__ is a string.
    if hasattr(klass, '__bases__'):
        for b in klass.__bases__:
            listRequiredModulesByClass(b, rval)

def listRequiredModules(module):
    rval = {}

    if hasattr(module, '__dict__'):
        for key, value in module.__dict__.items():
            t = type(value)
            if t in ClassTypes:
                listRequiredModulesByClass(value, rval)
            elif t is ModuleType and hasattr(value, '__name__'):
                rval[value.__name__] = 1
            elif t is FuncType and value.func_globals.has_key('__name__'):
                rval[value.func_globals['__name__']] = 1
    return rval

def sortModulesByDependency(modlist):
    unchosen = {}
    for name, module in modlist:
        unchosen[name] = (module, listRequiredModules(module))
    chose = 1
    rval = []
    while chose:
        chose = 0
        for name, (module, req) in unchosen.items():
            all_satisfied = 1
            for n in unchosen.keys():
                if name == n:
                    continue  # Skip self.
                if req.has_key(n):
                    # There is still a dependency.  Can't
                    # include this module in the list yet.
                    all_satisfied = 0
                    break
            if all_satisfied:
                chose = 1
                rval.append((name, module))
                del unchosen[name]
    # There might be some modules left over that are interdependent.
    for name, (module, req) in unchosen.items():
        rval.append((name, module))
    return rval

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
            if callable(reload_var) or reload_var:
                rval.append((name, module))
    return rval

def logBadRefresh(productid):
    exc = sys.exc_info()
    try:
        LOG('Refresh', ERROR, 'Exception while refreshing %s'
            % productid, error=exc)
        if hasattr(exc[0], '__name__'):
            error_type = exc[0].__name__
        else:
            error_type = str(exc[0])
        error_value = str(exc[1])
        info = format_exception(exc[0], exc[1], exc[2], limit=200)
        refresh_exc_info[productid] = (error_type, error_value, info)
    finally:
        exc = None

def performRefresh(jar, productid):
    '''Attempts to perform a refresh operation.
    '''
    refresh_exc_info[productid] = None
    setupModTimes(productid)  # Refresh again only if changed again.

    modlist = listRefreshableModules(productid)
    modlist = sortModulesByDependency(modlist)

    for name, module in modlist:
        # Remove the __import_error__ attribute.
        try: del module.__import_error__
        except: pass
        # Ask the module how it should be reloaded.
        reload_var = getReloadVar(module)
        if callable(reload_var):
            try:
                reload_var()
            except:
                logBadRefresh(productid)
                return 0
        else:
            try:
                reload(module)
            except:
                logBadRefresh(productid)
                return 0

    # Reinitialize and reinstall the product.
    from OFS import Application
    Application.reimport_product(productid)
    app = jar.root()['Application']
    Application.reinstall_product(app, productid)
    return 1

def performSafeRefresh(jar, productid):
    try:
        LOG('Refresh', INFO, 'Refreshing product %s' % productid)
        if not performRefresh(jar, productid):
            return 0
    except:
        logBadRefresh(productid)
        return 0
    else:
        return 1

def performFullRefresh(jar, productid):
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
            splitname = split(name, '.')[2:]
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
    auto_refresh_ids = checkAutoRefresh(jar)
    if auto_refresh_ids:
        finishAutoRefresh(jar, auto_refresh_ids)
        from ZODB import Connection
        Connection.updateCodeTimestamp()
        get_transaction().commit()
        jar._resetCache()
        get_transaction().begin()

def setupAutoRefresh(jar):
    # Install hook.
    from ZODB.ZApplication import connection_open_hooks
    connection_open_hooks.append(autoRefresh)
    # Init mod times.
    checkAutoRefresh(jar)

