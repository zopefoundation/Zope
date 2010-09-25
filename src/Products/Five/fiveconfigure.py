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

These directives are specific to Five and have no equivalents outside of it.
"""

import logging
import os
import glob
import warnings

from App.config import getConfiguration
from zope.interface import classImplements
from zope.component.interface import provideInterface
from zope.configuration.exceptions import ConfigurationError
from zope.publisher.interfaces.browser import IDefaultBrowserLayer

from Products.Five.browser.metaconfigure import page

logger = logging.getLogger('Products.Five')


def implements(_context, class_, interface):
    warnings.warn('Using <five:implements /> in %s is deprecated. Please use '
                  'the <class class="foo.Bar">'
                  '<implements interface="foo.interfaces.IBar" /></class> '
                  'directive instead.' % _context.info,
                  DeprecationWarning, stacklevel=2)
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


def handleBrokenProduct(product):
    if getConfiguration().debug_mode:
        # Just reraise the error and let Zope handle it.
        raise
    # Not debug mode. Zope should continue to load. Print a log message:
    logger.exception('Could not import Product %s' % product.__name__)


from zope.deferredimport import deprecated

deprecated("Please import from OFS.metaconfigure",
    findProducts = 'OFS.metaconfigure:findProducts',
    loadProducts = 'OFS.metaconfigure:loadProducts',
    loadProductsOverrides = 'OFS.metaconfigure:loadProductsOverrides',
    _register_monkies = 'OFS.metaconfigure:_register_monkies',
    _meta_type_regs = 'OFS.metaconfigure:_meta_type_regs',
    _registerClass = 'OFS.metaconfigure:_registerClass',
    registerClass = 'OFS.metaconfigure:registerClass',
    _registerPackage = 'OFS.metaconfigure:_registerPackage',
    registerPackage = 'OFS.metaconfigure:registerPackage',
    unregisterClass = 'OFS.metaconfigure:unregisterClass',
)
