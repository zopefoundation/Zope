##############################################################################
#
# Copyright (c) 2004, 2005 Zope Corporation and Contributors.
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

$Id: fiveconfigure.py 17361 2005-09-08 12:13:30Z regebro $
"""
import os
import sys
import glob
import warnings

import App
from zLOG import LOG, ERROR

from zope.interface import classImplements
from zope.configuration import xmlconfig
from zope.app.component.interface import provideInterface

from viewable import Viewable
from traversable import Traversable
from bridge import fromZ2Interface
from browser.metaconfigure import page

debug_mode = App.config.getConfiguration().debug_mode

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
    exc = sys.exc_info()
    LOG('Five', ERROR, 'Could not import Product %s' % name, error=exc)

def loadProducts(_context):
    products = findProducts()
    
    # first load meta.zcml files
    for product in products:
        zcml = os.path.join(os.path.dirname(product.__file__), 'meta.zcml')
        if os.path.isfile(zcml):
            try:
                xmlconfig.include(_context, zcml, package=product)
            except: # Yes, really, *any* kind of error.
                handleBrokenProduct(product)
                
    # now load their configure.zcml
    for product in products:
        zcml = os.path.join(os.path.dirname(product.__file__),
                            'configure.zcml')
        if os.path.isfile(zcml):
            try:
                xmlconfig.include(_context, zcml, package=product)
            except: # Yes, really, *any* kind of error.
                handleBrokenProduct(product)

def loadProductsOverrides(_context):
    for product in findProducts():
        zcml = os.path.join(os.path.dirname(product.__file__),
                            'overrides.zcml')
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

def isFiveMethod(m):
    return hasattr(m, '__five_method__')

_traversable_monkies = []
def classTraversable(class_):
    # If a class already has this attribute, it means it is either a
    # subclass of Traversable or was already processed with this
    # directive; in either case, do nothing... except in the case were
    # the class overrides __bobo_traverse__ instead of getting it from
    # a base class. In this case, we suppose that the class probably
    # didn't bother with the base classes __bobo_traverse__ anyway and
    # we step __fallback_traverse__.
    if hasattr(class_, '__five_traversable__'):
        if (hasattr(class_, '__bobo_traverse__') and
            isFiveMethod(class_.__bobo_traverse__)):
            return

    if hasattr(class_, '__bobo_traverse__'):
        if not isFiveMethod(class_.__bobo_traverse__):
            # if there's an existing bobo_traverse hook already, use that
            # as the traversal fallback method
            setattr(class_, '__fallback_traverse__', class_.__bobo_traverse__)
    if not hasattr(class_, '__fallback_traverse__'):
        setattr(class_, '__fallback_traverse__',
                Traversable.__fallback_traverse__.im_func)

    setattr(class_, '__bobo_traverse__',
            Traversable.__bobo_traverse__.im_func)
    setattr(class_, '__five_traversable__', True)
    # remember class for clean up
    _traversable_monkies.append(class_)

def traversable(_context, class_):
    _context.action(
        discriminator = None,
        callable = classTraversable,
        args = (class_,)
        )

_defaultviewable_monkies = []
def classDefaultViewable(class_):
    # If a class already has this attribute, it means it is either a
    # subclass of DefaultViewable or was already processed with this
    # directive; in either case, do nothing... except in the case were
    # the class overrides the attribute instead of getting it from
    # a base class. In this case, we suppose that the class probably
    # didn't bother with the base classes attribute anyway.
    if hasattr(class_, '__five_viewable__'):
        if (hasattr(class_, '__browser_default__') and
            isFiveMethod(class_.__browser_default__)):
            return

    if hasattr(class_, '__browser_default__'):
        # if there's an existing __browser_default__ hook already, use that
        # as the fallback
        if not isFiveMethod(class_.__browser_default__):
            setattr(class_, '__fallback_default__', class_.__browser_default__)
    if not hasattr(class_, '__fallback_default__'):
        setattr(class_, '__fallback_default__',
                Viewable.__fallback_default__.im_func)

    setattr(class_, '__browser_default__',
            Viewable.__browser_default__.im_func)
    setattr(class_, '__five_viewable__', True)
    # remember class for clean up
    _defaultviewable_monkies.append(class_)

def defaultViewable(_context, class_):
    _context.action(
        discriminator = None,
        callable = classDefaultViewable,
        args = (class_,)
        )

def viewable(_context, class_):
    # XXX do not need to mark where this is used, as simple search
    # should find all instances easily
    warnings.warn(
        'The five:viewable directive has been deprecated. '
        'Please use the five:traversable directive instead.',
        DeprecationWarning)

    _context.action(
        discriminator = None,
        callable = classTraversable,
        args=(class_,)
        )

def createZope2Bridge(zope2, package, name):
    # Map a Zope 2 interface into a Zope3 interface, seated within 'package'
    # as 'name'.
    z3i = fromZ2Interface(zope2)

    if name is not None:
        z3i.__dict__['__name__'] = name

    z3i.__dict__['__module__'] = package.__name__
    setattr(package, z3i.getName(), z3i)

def bridge(_context, zope2, package, name=None):
    # Directive handler for <five:bridge> directive.

    # N.B.:  We have to do the work early, or else we won't be able
    #        to use the synthesized interface in other ZCML directives.
    createZope2Bridge(zope2, package, name)

    # Faux action, only for conflict resolution.
    _context.action(
        discriminator = (zope2,),
        )

def pagesFromDirectory(_context, directory, module, for_=None,
                  layer='default', permission='zope.Public'):

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

# clean up code

def killMonkey(class_, name, fallback, attr=None):
    """Die monkey, die!"""
    method = getattr(class_, name, None)
    if isFiveMethod(method):
        original = getattr(class_, fallback, None)
        if original is None:
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

def untraversable(class_):
    """Restore class's initial state with respect to traversability"""
    killMonkey(class_, '__bobo_traverse__', '__fallback_traverse__',
               '__five_traversable__')

def undefaultViewable(class_):
    """Restore class's initial state with respect to being default
    viewable."""
    killMonkey(class_, '__browser_default__', '__fallback_default__',
               '__five_viewable__')

def cleanUp():
    for class_ in _traversable_monkies:
        untraversable(class_)
    for class_ in _defaultviewable_monkies:
        undefaultViewable(class_)

from zope.testing.cleanup import addCleanUp
addCleanUp(cleanUp)
del addCleanUp
