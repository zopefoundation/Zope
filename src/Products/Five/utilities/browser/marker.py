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
"""Marker interfaces adapter views.
"""

from Products.Five.utilities.interfaces import IMarkerInterfaces


class EditView:

    """Marker interface edit view.
    """

    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.adapted = IMarkerInterfaces(context)
        self.context_url = self.context.absolute_url()

    def __call__(self, SAVE=None, add=(), remove=()):
        if SAVE:
            self.update(add, remove)
            self.request.response.redirect(self.request.ACTUAL_URL)
            return ''
        return self.index()

    def _getLinkToInterfaceDetailsView(self, interfaceName):
        return (self.context_url +
            '/views-details.html?iface=%s&type=zope.publisher.interfaces.browser.IBrowserRequest' % interfaceName)

    def _getNameLinkDicts(self, interfaceNames):
        return [dict(name=name,
                     link=self._getLinkToInterfaceDetailsView(name))
                for name in interfaceNames]

    def getAvailableInterfaceNames(self):
        return self._getNameLinkDicts(
            self.adapted.getAvailableInterfaceNames())

    def getDirectlyProvidedNames(self):
        return self._getNameLinkDicts(self.adapted.getDirectlyProvidedNames())

    def getInterfaceNames(self):
        return self._getNameLinkDicts(self.adapted.getInterfaceNames())

    def update(self, add, remove):
        # this could return errors
        add = self.adapted.dottedToInterfaces(add)
        remove = self.adapted.dottedToInterfaces(remove)
        self.adapted.update(add=add, remove=remove)
