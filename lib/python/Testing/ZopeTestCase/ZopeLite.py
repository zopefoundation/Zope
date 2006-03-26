##############################################################################
#
# Copyright (c) 2005 Zope Corporation and Contributors. All Rights Reserved.
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

$Id$
"""

import os, sys, time

# Allow code to tell it is run by the test framework
os.environ['ZOPETESTCASE'] = '1'

# Increase performance on MP hardware
sys.setcheckinterval(2500)

# Shut up if we are not in control of the import process
_quiet = sys.modules.has_key('Zope2')

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

_exec('import Globals')
import Globals
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

def _apply_patches():
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

    # Note that we applied the monkey patches
    global _patched
    _patched = True

# Do not patch a running Zope
if not Zope2._began_startup:
    _apply_patches()

# Allow test authors to install Zope products into the test environment. Note
# that installProduct() must be called at module level -- never from tests.
from OFS.Application import get_folder_permissions, get_products, install_product
from OFS.Folder import Folder
import Products

_theApp = Zope2.app()
_installedProducts = {}

def hasProduct(name):
    '''Checks if a product can be found along Products.__path__'''
    return name in [n[1] for n in get_products()]

def installProduct(name, quiet=0):
    '''Installs a Zope product.'''
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
                Globals.default__class_init__(Folder)
                if not quiet: _print('done (%.3fs)\n' % (time.time() - start))
                break
        else:
            if name != 'SomeProduct':   # Ignore the skeleton tests :-P
                if not quiet: _print('Installing %s ... NOT FOUND\n' % name)

def _load_control_panel():
    # Loading the Control_Panel of an existing ZODB may take
    # a while; print another dot if it does.
    start = time.time()
    max = (start - _start) / 4
    _exec('_theApp.Control_Panel')
    _theApp.Control_Panel
    if (time.time() - start) > max:
        _write('.')

def _install_products():
    installProduct('PluginIndexes', 1)  # Must install first
    installProduct('OFSP', 1)
    #installProduct('ExternalMethod', 1)
    #installProduct('ZSQLMethods', 1)
    #installProduct('ZGadflyDA', 1)
    #installProduct('MIMETools', 1)
    #installProduct('MailHost', 1)

_load_control_panel()
_install_products()

# So people can use ZopeLite.app()
app = Zope2.app
debug = Zope2.debug
DB = Zope2.DB
configure = Zope2.configure
def startup(): pass
Zope = Zope2

# ZODB sandbox factory
from ZODB.DemoStorage import DemoStorage

def sandbox(base=None):
    '''Returns a sandbox copy of the base ZODB.'''
    if base is None: base = Zope2.DB
    base_storage = base._storage
    quota = getattr(base_storage, '_quota', None)
    storage = DemoStorage(base=base_storage, quota=quota)
    return ZODB.DB(storage)

_write(' done (%.3fs)\n' % (time.time() - _start))

