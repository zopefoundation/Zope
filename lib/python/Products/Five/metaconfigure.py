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
"""Generic Components ZCML Handlers

$Id: metaconfigure.py 12915 2005-05-31 10:23:19Z philikon $
"""
from types import ModuleType

from zope.interface import classImplements
from zope.configuration.exceptions import ConfigurationError

from security import CheckerPublic
from security import protectName, initializeClass

class ContentDirective:

    def __init__(self, _context, class_):
        self.__class = class_
        if isinstance(self.__class, ModuleType):
            raise ConfigurationError('Content class attribute must be a class')
        self.__context = _context

    def implements(self, _context, interface):
        for interface in interface:
            _context.action(
                discriminator = (
                'five::directive:content', self.__class, object()),
                callable = classImplements,
                args = (self.__class, interface),
                )
            interface(_context, interface)

    def require(self, _context, permission=None,
                attributes=None, interface=None):
        """Require a the permission to access a specific aspect"""

        if not (interface or attributes):
            raise ConfigurationError("Nothing required")

        if interface:
            for i in interface:
                if i:
                    self.__protectByInterface(i, permission)
        if attributes:
            self.__protectNames(attributes, permission)

    def allow(self, _context, attributes=None, interface=None):
        """Like require, but with permission_id zope.Public"""
        return self.require(_context, CheckerPublic, attributes, interface)

    def __protectByInterface(self, interface, permission_id):
        "Set a permission on names in an interface."
        for n, d in interface.namesAndDescriptions(1):
            self.__protectName(n, permission_id)
        interface(self.__context, interface)

    def __protectName(self, name, permission_id):
        "Set a permission on a particular name."
        self.__context.action(
            discriminator = ('five:protectName', self.__class, name),
            callable = protectName,
            args = (self.__class, name, permission_id)
            )

    def __protectNames(self, names, permission_id):
        "Set a permission on a bunch of names."
        for name in names:
            self.__protectName(name, permission_id)

    def __call__(self):
        "Handle empty/simple declaration."
        return self.__context.action(
            discriminator = ('five:initialize:class', self.__class),
            callable = initializeClass,
            args = (self.__class,)
            )
