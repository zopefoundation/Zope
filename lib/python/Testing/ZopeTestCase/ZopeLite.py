#
# Lightweight Zope startup
#
# Fast Zope startup is achieved by not installing (m)any
# products. If your tests require a product you must
# install it yourself using installProduct().
#
# Typically used as in
#
#   import ZopeLite as Zope2
#   Zope2.installProduct('SomeProduct')
#   app = Zope2.app()
#

# $Id: ZopeLite.py,v 1.24 2004/08/18 09:28:54 shh42 Exp $

import os, sys, time

# Increase performance on MP hardware
sys.setcheckinterval(2500)

# Shut up if we are not in control of the import process
_quiet = sys.modules.has_key('Zope')

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

# Configure logging
if not sys.modules.has_key('logging'):
    import logging
    logging.basicConfig()

# Debug mode is dog slow ...
import App.config
config = App.config.getConfiguration()
config.debug_mode = 0
App.config.setConfiguration(config)

# Need to import Zope2 early on as the 
# ZTUtils package relies on it
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

# Avoid expensive product import
def _null_import_products(): pass
OFS.Application.import_products = _null_import_products

# Avoid expensive product installation
def _null_initialize(app): pass
OFS.Application.initialize = _null_initialize

# Avoid expensive help registration
def _null_register_topic(self,id,topic): pass
App.ProductContext.ProductContext.registerHelpTopic = _null_register_topic
def _null_register_title(self,title): pass
App.ProductContext.ProductContext.registerHelpTitle = _null_register_title
def _null_register_help(self,directory='',clear=1,title_re=None): pass
App.ProductContext.ProductContext.registerHelp = _null_register_help

# Make sure to use a temporary client cache
if os.environ.get('ZEO_CLIENT'): del os.environ['ZEO_CLIENT']

from OFS.Application import get_folder_permissions, get_products, install_product
from OFS.Folder import Folder
import Products

_theApp = Zope2.app()
_installedProducts = {}

def hasProduct(name):
    '''Tests if a product can be found along Products.__path__'''
    return name in [n[1] for n in get_products()]

def installProduct(name, quiet=0):
    '''Installs a Zope product.'''
    start = time.time()
    app = _theApp
    meta_types = []
    if not _installedProducts.has_key(name):
        for priority, product_name, index, product_dir in get_products():
            if product_name == name:
                if not quiet: _print('Installing %s ... ' % product_name)
                # We want to fail immediately if a product throws an exception
                # during install, so we set the raise_exc flag.
                install_product(app, product_dir, product_name, meta_types,
                                get_folder_permissions(), raise_exc=1)
                _installedProducts[product_name] = 1
                Products.meta_types = Products.meta_types + tuple(meta_types)
                Globals.default__class_init__(Folder)
                if not quiet: _print('done (%.3fs)\n' % (time.time() - start))
                break
        else:
            if name != 'SomeProduct':   # Ignore the skeleton tests :-P
                if not quiet: _print('Installing %s ... NOT FOUND\n' % name)

# Loading the Control_Panel of an existing ZODB may take 
# a while; print another dot if it does.
_s = time.time(); _max = (_s - _start) / 4
_exec('_theApp.Control_Panel')
_cp = _theApp.Control_Panel
if hasattr(_cp, 'initialize_cache'):
    _cp.initialize_cache()
if (time.time() - _s) > _max: 
    _write('.')

installProduct('PluginIndexes', 1)  # Must install first
installProduct('OFSP', 1)
#installProduct('ExternalMethod', 1)
#installProduct('ZSQLMethods', 1)
#installProduct('ZGadflyDA', 1)
#installProduct('MIMETools', 1)
#installProduct('MailHost', 1)

# So people can use ZopeLite.app()
app = Zope2.app
debug = Zope2.debug
DB = Zope2.DB
configure = Zope2.configure
def startup(): pass

from ZODB.DemoStorage import DemoStorage
def sandbox(base=None):
    '''Returns what amounts to a sandbox copy of the base ZODB.'''
    if base is None: base = Zope2.DB
    base_storage = base._storage
    quota = getattr(base_storage, '_quota', None)
    storage = DemoStorage(base=base_storage, quota=quota)
    return ZODB.DB(storage)

_write(' done (%.3fs)\n' % (time.time() - _start))

