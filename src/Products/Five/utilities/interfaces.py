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
"""Utility Interface Definitions.
"""

from zope.interface import Interface


class IReadInterface(Interface):

    def getDirectlyProvided():
        """List the interfaces directly implemented by the object.
        """

    def getDirectlyProvidedNames():
        """List the names of interfaces directly implemented by the object.
        """

    def getAvailableInterfaces():
        """List the marker interfaces available for the object.
        """

    def getAvailableInterfaceNames():
        """List the names of marker interfaces available for the object.
        """

    def getInterfaces():
        """List interfaces provided by the class of the object.
        """

    def getInterfaceNames():
        """List the names of interfaces provided by the class of the object.
        """

    def getProvided():
        """List interfaces provided by the object.
        """

    def getProvidedNames():
        """List the names of interfaces provided by the object.
        """


class IWriteInterface(Interface):

    def update(add=(), remove=()):
        """Update directly provided interfaces of the object.
        """

    def mark(interface):
        """Add interface to interfaces the object directly provides.
        """

    def erase(interface):
        """Remove interfaces from interfaces the object directly provides.
        """


class IMarkerInterfaces(IReadInterface, IWriteInterface):

    """Provides methods for inspecting and assigning marker interfaces.
    """
