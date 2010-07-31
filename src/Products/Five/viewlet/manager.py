##############################################################################
#
# Copyright (c) 2006 Zope Foundation and Contributors.
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
"""Viewlet manager.
"""

from Acquisition import aq_base
from AccessControl.ZopeGuards import guarded_hasattr
import zope.interface
import zope.security
from zope.viewlet import interfaces
from zope.viewlet.manager import ViewletManagerBase as origManagerBase

from Products.Five.browser.pagetemplatefile import ZopeTwoPageTemplateFile

class ViewletManagerBase(origManagerBase):
    """A base class for Viewlet managers to work in Zope2"""

    template = None
    
    def __getitem__(self, name):
        """See zope.interface.common.mapping.IReadMapping"""
        # Find the viewlet
        viewlet = zope.component.queryMultiAdapter(
            (self.context, self.request, self.__parent__, self),
            interfaces.IViewlet, name=name)

        # If the viewlet was not found, then raise a lookup error
        if viewlet is None:
            raise zope.component.interfaces.ComponentLookupError(
                'No provider with name `%s` found.' %name)

        # If the viewlet cannot be accessed, then raise an
        # unauthorized error
        if not guarded_hasattr(viewlet, 'render'):
            raise zope.security.interfaces.Unauthorized(
                'You are not authorized to access the provider '
                'called `%s`.' %name)

        # Return the viewlet.
        return viewlet

    def filter(self, viewlets):
        """Sort out all content providers

        ``viewlets`` is a list of tuples of the form (name, viewlet).
        """
        results = []
        # Only return viewlets accessible to the principal
        # We need to wrap each viewlet in its context to make sure that
        # the object has a real context from which to determine owner
        # security.
        for name, viewlet in viewlets:
            if guarded_hasattr(viewlet, 'render'):
                results.append((name, viewlet))
        return results

    def sort(self, viewlets):
        """Sort the viewlets.

        ``viewlets`` is a list of tuples of the form (name, viewlet).
        """
        # By default, use the standard Python way of doing sorting. Unwrap the
        # objects first so that they are sorted as expected.  This is dumb
        # but it allows the tests to have deterministic results.
        return sorted(viewlets, lambda x, y: cmp(aq_base(x[1]), aq_base(y[1])))

def ViewletManager(name, interface, template=None, bases=()):
    attrDict = {'__name__': name}
    
    if template is not None:
        attrDict['template'] = ZopeTwoPageTemplateFile(template)

    if ViewletManagerBase not in bases:
        # Make sure that we do not get a default viewlet manager mixin, if the
        # provided base is already a full viewlet manager implementation.
        if not (len(bases) == 1 and
                interfaces.IViewletManager.implementedBy(bases[0])):
            bases = bases + (ViewletManagerBase,)

    ViewletManager = type(
        '<ViewletManager providing %s>' % interface.getName(), bases, attrDict)

    zope.interface.classImplements(ViewletManager, interface)
    return ViewletManager
