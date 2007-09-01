##############################################################################
#
# Copyright (c) 2006 Zope Corporation and Contributors.
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
"""Provider expression.
"""
import zope.event
import zope.interface
import zope.component

from zope.tales import expressions
from zope.contentprovider import interfaces, tales
from zope.location.interfaces import ILocation

from Acquisition.interfaces import IAcquirer

class Z2ProviderExpression(expressions.StringExpr):
    zope.interface.implements(interfaces.ITALESProviderExpression)

    # This is mostly a copy of
    # zope.contentprovider.tales.TALESProviderExpression's __call__
    # method.
    def __call__(self, econtext):
        name = super(Z2ProviderExpression, self).__call__(econtext)
        context = econtext.vars['context']
        request = econtext.vars['request']
        view = econtext.vars['view']

        # Try to look up the provider.
        provider = zope.component.queryMultiAdapter(
            (context, request, view), interfaces.IContentProvider, name)

        # Provide a useful error message, if the provider was not found.
        if provider is None:
            raise interfaces.ContentProviderLookupError(name)

        # add the __name__ attribute if it implements ILocation
        if ILocation.providedBy(provider):
            provider.__name__ = name

        # ATTN: This is where we are different from
        # TALESProviderExpression: We support Acquisition wrapping.
        if IAcquirer.providedBy(provider):
            provider = provider.__of__(context)

        # Insert the data gotten from the context
        tales.addTALNamespaceData(provider, econtext)

        # Stage 1: Do the state update.
        zope.event.notify(interfaces.BeforeUpdateEvent(provider, request))
        provider.update()

        # Stage 2: Render the HTML content.
        return provider.render()
