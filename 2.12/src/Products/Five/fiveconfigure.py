##############################################################################
#
# Copyright (c) 2004, 2005 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Five-specific directive handlers

These directives are specific to Five and have no equivalents in Zope 3.

$Id$
"""
import os
import glob
import logging

import App.config
import Products
import Zope2

from zope.interface import classImplements, implementedBy
from zope.component import getUtility
from zope.component.interface import provideInterface
from zope.configuration import xmlconfig
from zope.configuration.exceptions import ConfigurationError
from zope.publisher.interfaces.browser import IDefaultBrowserLayer
from zope.security.interfaces import IPermission

from Products.Five import isFiveMethod
from Products.Five.browser.metaconfigure import page

debug_mode = App.config.getConfiguration().debug_mode
LOG = logging.getLogger('Five')

def findProducts():
    import Products
    from types import ModuleType
    products = []
    for name in dir(Products):
        product = getattr(Products, name)
        if isinstance(product, ModuleType) and hasattr(product, '__file__'):
            products.append(product)
    return products

def handleBrokenProduct(product):
    if debug_mode:
        # Just reraise the error and let Zope handle it.
        raise
    # Not debug mode. Zope should continue to load. Print a log message:
    # XXX It would be really cool if we could make this product appear broken
    # in the control panel. However, all attempts to do so has failed from my 
    # side. //regebro
    LOG.error('Could not import Product %s' % product.__name__, exc_info=True)

def loadProducts(_context, file=None):
    if file is None:
        # set the default
        file = 'configure.zcml'
    
    # now load the files if they exist
    for product in findProducts():
        zcml = os.path.join(os.path.dirname(product.__file__), file)
        if os.path.isfile(zcml):
            try:
                xmlconfig.include(_context, zcml, package=product)
            except: # Yes, really, *any* kind of error.
                handleBrokenProduct(product)

def loadProductsOverrides(_context, file=None):
    if file is None:
        # set the default
        file = 'overrides.zcml'
    
    # now load the files if they exist
    for product in findProducts():
        zcml = os.path.join(os.path.dirname(product.__file__), file)
        if os.path.isfile(zcml):
            try:
                xmlconfig.includeOverrides(_context, zcml, package=product)
            except: # Yes, really, *any* kind of error.
                handleBrokenProduct(product)

def implements(_context, class_, interface):
    for interface in interface:
        _context.action(
            discriminator = None,
            callable = classImplements,
            args = (class_, interface)
            )
        _context.action(
            discriminator = None,
            callable = provideInterface,
            args = (interface.__module__ + '.' + interface.getName(),
                    interface)
            )

def pagesFromDirectory(_context, directory, module, for_=None,
                       layer=IDefaultBrowserLayer, permission='zope.Public'):

    if isinstance(module, basestring):
        module = _context.resolve(module)

    _prefix = os.path.dirname(module.__file__)
    directory = os.path.join(_prefix, directory)

    if not os.path.isdir(directory):
        raise ConfigurationError(
            "Directory %s does not exist" % directory
            )

    for fname in glob.glob(os.path.join(directory, '*.pt')):
        name = os.path.splitext(os.path.basename(fname))[0]
        page(_context, name=name, permission=permission,
             layer=layer, for_=for_, template=fname)


_register_monkies = []
_meta_type_regs = []
def _registerClass(class_, meta_type, permission, addview, icon, global_):
    setattr(class_, 'meta_type', meta_type)

    permission_obj = getUtility(IPermission, permission)

    if icon:
        setattr(class_, 'icon', '++resource++%s' % icon)

    interfaces = tuple(implementedBy(class_))

    info = {'name': meta_type,
            'action': addview and ('+/%s' % addview) or '',
            'product': 'Five',
            'permission': str(permission_obj.title),
            'visibility': global_ and 'Global' or None,
            'interfaces': interfaces,
            'instance': class_,
            'container_filter': None}

    Products.meta_types += (info,)

    _register_monkies.append(class_)
    _meta_type_regs.append(meta_type)

def registerClass(_context, class_, meta_type, permission, addview=None,
                  icon=None, global_=True):
    _context.action(
        discriminator = ('registerClass', meta_type),
        callable = _registerClass,
        args = (class_, meta_type, permission, addview, icon, global_)
        )

def _registerPackage(module_, init_func=None):
    """Registers the given python package as a Zope 2 style product
    """
    
    if not hasattr(module_, '__path__'):
        raise ValueError("Must be a package and the " \
                         "package must be filesystem based")
    
    registered_packages = getattr(Products, '_registered_packages', None)
    if registered_packages is None:
        registered_packages = Products._registered_packages = []
    registered_packages.append(module_)
    
    # Delay the actual setup until the usual product loading time in
    # OFS.Application. Otherwise, we may get database write errors in
    # ZEO, when there's no connection with which to write an entry to
    # Control_Panel. We would also get multiple calls to initialize().
    to_initialize = getattr(Products, '_packages_to_initialize', None)
    if to_initialize is None:
        to_initialize = Products._packages_to_initialize = []
    to_initialize.append((module_, init_func,))

def registerPackage(_context, package, initialize=None):
    """ZCML directive function for registering a python package product
    """

    _context.action(
        discriminator = ('registerPackage', package),
        callable = _registerPackage,
        args = (package,initialize)
        )

# clean up code

def killMonkey(class_, name, fallback, attr=None):
    """Die monkey, die!"""
    method = getattr(class_, name, None)
    if isFiveMethod(method):
        original = getattr(class_, fallback, None)
        if original is not None:
            delattr(class_, fallback)
        if original is None or isFiveMethod(original):
            try:
                delattr(class_, name)
            except AttributeError:
                pass
        else:
            setattr(class_, name, original)

    if attr is not None:
        try:
            delattr(class_, attr)
        except (AttributeError, KeyError):
            pass

def unregisterClass(class_):
    delattr(class_, 'meta_type')
    try:
        delattr(class_, 'icon')
    except AttributeError:
        pass

def cleanUp():

    global _register_monkies
    for class_ in _register_monkies:
        unregisterClass(class_)
    _register_monkies = []

    global _meta_type_regs
    Products.meta_types = tuple([ info for info in getattr(Products, 'meta_types', [])
                                  if info['name'] not in _meta_type_regs ])
    _meta_type_regs = []

from zope.testing.cleanup import addCleanUp
addCleanUp(cleanUp)
del addCleanUp
