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
"""Marker interfaces adapter.

Allows for arbitrary application of marker interfaces to objects.
"""

from zope.component.interface import getInterface
from zope.component.interface import interfaceToName
from zope.component.interface import searchInterface
from zope.interface import directlyProvidedBy
from zope.interface import directlyProvides
from zope.interface import implementedBy
from zope.interface import implementer
from zope.interface import providedBy
from zope.interface.interfaces import IInterface

from .interfaces import IMarkerInterfaces


def interfaceStringCheck(f):
    def wrapper(ob, interface):
        if isinstance(interface, str):
            interface = getInterface(ob, interface)
        return f(ob, interface)
    return wrapper


def mark(ob, interface):
    directlyProvides(ob, directlyProvidedBy(ob), interface)


def erase(ob, interface):
    directlyProvides(ob, directlyProvidedBy(ob) - interface)


mark = interfaceStringCheck(mark)
erase = interfaceStringCheck(erase)


@implementer(IMarkerInterfaces)
class MarkerInterfacesAdapter:

    mark = staticmethod(mark)
    erase = staticmethod(erase)

    def __init__(self, context):
        self.context = context

    def dottedToInterfaces(self, seq):
        return [getInterface(self.context, dotted) for dotted in seq]

    def getDirectlyProvided(self):
        return directlyProvidedBy(self.context)

    def getDirectlyProvidedNames(self):
        return self._getInterfaceNames(self.getDirectlyProvided())

    def getAvailableInterfaces(self):
        results = []
        todo = list(providedBy(self.context))
        done = []
        while todo:
            interface = todo.pop()
            done.append(interface)
            for base in interface.__bases__:
                if base not in todo and base not in done:
                    todo.append(base)
            markers = self._getDirectMarkersOf(interface)
            for interface in markers:
                if interface not in results and \
                   not interface.providedBy(self.context):
                    results.append(interface)
            todo += markers
        return tuple(results)

    def getAvailableInterfaceNames(self):
        names = self._getInterfaceNames(self.getAvailableInterfaces())
        names.sort()
        return names

    def getInterfaces(self):
        return tuple(implementedBy(self.context.__class__))

    def getInterfaceNames(self):
        return self._getInterfaceNames(self.getInterfaces())

    def getProvided(self):
        return providedBy(self.context)

    def getProvidedNames(self):
        return self._getInterfaceNames(self.getProvided())

    def update(self, add=(), remove=()):
        """Currently update adds and then removes, rendering duplicate null.
        """
        marker_ifaces = self.getAvailableInterfaces()
        if len(add):
            [mark(self.context, interface)
             for interface in set(marker_ifaces) & set(add)]

        direct_ifaces = self.getDirectlyProvided()
        if len(remove):
            [erase(self.context, interface)
             for interface in set(direct_ifaces) & set(remove)]

    def _getInterfaceNames(self, interfaces):
        return [interfaceToName(self, iface) for iface in interfaces]

    def _getDirectMarkersOf(self, base):
        """Get empty interfaces directly inheriting from the given one.
        """
        results = []
        interfaces = searchInterface(None, base=base)
        for interface in interfaces:
            # There are things registered with the interface service
            # that are not interfaces. Yay!
            if not IInterface.providedBy(interface):
                continue
            if base in interface.__bases__ and not interface.names():
                results.append(interface)
        results.sort()
        return tuple(results)
