##############################################################################
#
# Copyright (c) 2005 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Lightweight Zope startup

Fast Zope startup is achieved by not installing (m)any
products. If your tests require a product you must
install it yourself using installProduct().

Typically used as in

  import ZopeLite as Zope2
  Zope2.installProduct('SomeProduct')
  app = Zope2.app()
"""

import os, sys, time
import layer

# Allow code to tell it is run by the test framework
os.environ['ZOPETESTCASE'] = '1'

# Increase performance on MP hardware
sys.setcheckinterval(2500)

# Shut up if we are not in control of the import process
#_quiet = sys.modules.has_key('Zope2')

# Always shut up
_quiet = True

def _print(msg):
    '''Writes 'msg' to stderr and flushes the stream.'''
    sys.stderr.write(msg)
    sys.stderr.flush()

def _write(msg):
    '''Writes 'msg' to stderr if not _quiet.'''
    if not _quiet:
        _print(msg)

def _exec(cmd):
    '''Prints the time it takes to execute 'cmd'.'''
    if os.environ.get('X', None):
        start = time.time()
        exec cmd
        _print('(%.3fs)' % (time.time() - start))

_write('Loading Zope, please stand by ')
_start = time.time()

def _configure_logging():
    # Initialize the logging module
    import logging
    root = logging.getLogger()
    if not root.handlers:
        class NullHandler(logging.Handler):
            def emit(self, record): pass
        root.addHandler(NullHandler())
        logging.basicConfig()

def _configure_debug_mode():
    # Switch off debug mode
    import App.config
    config = App.config.getConfiguration()
    config.debug_mode = 0
    App.config.setConfiguration(config)

def _configure_client_cache():
    # Make sure we use a temporary client cache
    import App.config
    config = App.config.getConfiguration()
    config.zeo_client_name = None
    App.config.setConfiguration(config)

_configure_logging()
_configure_debug_mode()
_configure_client_cache()

_exec('import Zope2')
import Zope2
_exec('import ZODB')
import ZODB
_write('.')

#_exec('import Globals')
#import Globals
_exec('import OFS.SimpleItem')
import OFS.SimpleItem
_exec('import OFS.ObjectManager')
import OFS.ObjectManager
_write('.')

_exec('import OFS.Application')
import OFS.Application
import App.ProductContext
_write('.')

_patched = False

@layer.onsetup
def _apply_patches():
    # Do not patch a running Zope
    if Zope2._began_startup:
        return

    # Avoid expensive product import
    def null_import_products(): pass
    OFS.Application.import_products = null_import_products

    # Avoid expensive product installation
    def null_initialize(app): pass
    OFS.Application.initialize = null_initialize

    # Avoid expensive help registration
    def null_register_topic(self,id,topic): pass
    App.ProductContext.ProductContext.registerHelpTopic = null_register_topic
    def null_register_title(self,title): pass
    App.ProductContext.ProductContext.registerHelpTitle = null_register_title
    def null_register_help(self,directory='',clear=1,title_re=None): pass
    App.ProductContext.ProductContext.registerHelp = null_register_help

    # Avoid loading any ZCML
    from Zope2.App import startup as zopeapp_startup
    def null_load_zcml(): pass
    zopeapp_startup.load_zcml = null_load_zcml

    # Note that we applied the monkey patches
    global _patched
    _patched = True

_apply_patches()

_theApp = None

@layer.onsetup
def _startup():
    global _theApp
    _theApp = Zope2.app()

# Start ZopeLite
_startup()

# Allow test authors to install Zope products into the test environment. Note
# that installProduct() must be called at module level -- never from tests.
from OFS.Application import get_folder_permissions, get_products
from OFS.Application import install_product, install_package
from OFS.Folder import Folder
import Products

_installedProducts = {}
_installedPackages = {}

def hasProduct(name):
    '''Checks if a product can be found along Products.__path__'''
    return name in [n[1] for n in get_products()]

@layer.onsetup
def installProduct(name, quiet=0):
    '''Installs a Zope product at layer setup time.'''
    quiet = 1 # Ignore argument
    _installProduct(name, quiet)

def _installProduct(name, quiet=0):
    '''Installs a Zope product.'''
    from AccessControl.class_init import InitializeClass
    start = time.time()
    meta_types = []
    if _patched and not _installedProducts.has_key(name):
        for priority, product_name, index, product_dir in get_products():
            if product_name == name:
                if not quiet: _print('Installing %s ... ' % product_name)
                # We want to fail immediately if a product throws an exception
                # during install, so we set the raise_exc flag.
                install_product(_theApp, product_dir, product_name, meta_types,
                                get_folder_permissions(), raise_exc=1)
                _installedProducts[product_name] = 1
                Products.meta_types = Products.meta_types + tuple(meta_types)
                InitializeClass(Folder)
                if not quiet: _print('done (%.3fs)\n' % (time.time() - start))
                break
        else:
            if name != 'SomeProduct':   # Ignore the skeleton tests :-P
                if not quiet: _print('Installing %s ... NOT FOUND\n' % name)

def hasPackage(name):
    '''Checks if a package has been registered with five:registerPackage.'''
    from OFS.metaconfigure import has_package
    return has_package(name)

def installPackage(name, quiet=0):
    '''Installs a registered Python package.'''
    quiet = 1 # Ignore argument
    _installPackage(name, quiet)

def _installPackage(name, quiet=0):
    '''Installs a registered Python package.'''
    from OFS.metaconfigure import get_packages_to_initialize
    start = time.time()
    if _patched and not _installedPackages.has_key(name):
        for module, init_func in get_packages_to_initialize():
            if module.__name__ == name:
                if not quiet: _print('Installing %s ... ' % module.__name__)
                # We want to fail immediately if a package throws an exception
                # during install, so we set the raise_exc flag.
                install_package(_theApp, module, init_func, raise_exc=1)
                _installedPackages[module.__name__] = 1
                if not quiet:
                    _print('done (%.3fs)\n' % (time.time() - start))
                break
        else:
            if not quiet: _print('Installing %s ... NOT FOUND\n' % name)

installProduct('PluginIndexes', 1)  # Must install first
installProduct('OFSP', 1)

# So people can use ZopeLite.app()
app = Zope2.app
debug = Zope2.debug
DB = Zope2.DB
configure = Zope2.configure
def startup(): pass
Zope = Zope2
active = _patched

# ZODB sandbox factory
from ZODB.DemoStorage import DemoStorage

def sandbox(base=None):
    '''Returns a sandbox copy of the base ZODB.'''
    if base is None: base = Zope2.DB
    storage = DemoStorage(base=base._storage)
    return ZODB.DB(storage)

_write(' done (%.3fs)\n' % (time.time() - _start))

