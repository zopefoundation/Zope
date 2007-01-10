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

$Id$
"""
import zope.component
from zope.contentprovider import interfaces as cp_interfaces
from zope.contentprovider.tales import addTALNamespaceData
from zope.interface import implements
from zope.tales.expressions import StringExpr

class Z2ProviderExpression(StringExpr):
    """Create a custom provider expression which overrides __call__ to
       acquisition wrap the provider so that security lookups can be done."""

    implements(cp_interfaces.ITALESProviderExpression)

    def __call__(self, econtext):
        name = super(Z2ProviderExpression, self).__call__(econtext)
        context = econtext.vars['context']
        request = econtext.vars['request']
        view = econtext.vars['view']

        # Try to look up the provider.
        provider = zope.component.queryMultiAdapter(
            (context, request, view), cp_interfaces.IContentProvider, name)

        # Provide a useful error message, if the provider was not found.
        if provider is None:
            raise cp_interfaces.ContentProviderLookupError(name)

        if getattr(provider, '__of__', None) is not None:
            provider = provider.__of__(context)

        # Insert the data gotten from the context
        addTALNamespaceData(provider, econtext)

        # Stage 1: Do the state update.
        provider.update()

        # Stage 2: Render the HTML content.
        return provider.render()
