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

import urllib
from Acquisition import aq_parent
from OFS.interfaces import ITraversable

from zope.component import getMultiAdapter
from zope.interface import implements
from zope.traversing.browser.interfaces import IAbsoluteURL
from zope.traversing.browser.absoluteurl import _insufficientContext, _safe
from zope.publisher.browser import BrowserView


class AbsoluteURL(BrowserView):
    """An absolute_url adapter for generic objects in Zope 2 that
    aren't OFS.Traversable (e.g. views, resources, etc.).

    This is very close to the generic implementation from
    zope.traversing.browser, but the Zope 2 request doesn't support
    all the methods that it uses yet.
    """
    implements(IAbsoluteURL)

    def __unicode__(self):
        return urllib.unquote(self.__str__()).decode('utf-8')

    def __str__(self):
        context = self.context
        request = self.request

        container = aq_parent(context)
        if container is None:
            raise TypeError(_insufficientContext)

        url = str(getMultiAdapter((container, request), name='absolute_url'))
        name = self._getContextName(context)
        if name is None:
            raise TypeError(_insufficientContext)

        if name:
            url += '/' + urllib.quote(name.encode('utf-8'), _safe)

        return url

    __call__ = __str__

    def _getContextName(self, context):
        if getattr(context, 'getId', None) is not None:
            return context.getId()
        return getattr(context, '__name__', None)

    def breadcrumbs(self):
        context = self.context
        request = self.request

        # We do this here do maintain the rule that we must be wrapped
        container = aq_parent(context)
        if container is None:
            raise TypeError(_insufficientContext)

        base = tuple(getMultiAdapter((container, request),
                                     name='absolute_url').breadcrumbs())

        name = self._getContextName(context)
        if name is None:
            raise TypeError(_insufficientContext)

        if name:
            base += ({'name': name,
                      'url': ("%s/%s" % (base[-1]['url'],
                                         urllib.quote(name.encode('utf-8'),
                                                      _safe)))
                      }, )

        return base


class OFSTraversableAbsoluteURL(BrowserView):
    """An absolute_url adapter for OFS.Traversable subclasses
    """
    implements(IAbsoluteURL)

    def __unicode__(self):
        return urllib.unquote(self.__str__()).decode('utf-8')

    def __str__(self):
        return self.context.absolute_url()

    __call__ = __str__

    def breadcrumbs(self):
        context = self.context
        container = aq_parent(context)
        request = self.request

        name = context.getId()
        
        if (container is None
            or self._isVirtualHostRoot()
            or not ITraversable.providedBy(container)):
            return ({'name': name, 'url': context.absolute_url()},)

        view = getMultiAdapter((container, request), IAbsoluteURL)
        base = tuple(view.breadcrumbs())
        base += (
            {'name': name, 'url': ("%s/%s" % (base[-1]['url'], name))},)

        return base

    def _isVirtualHostRoot(self):
        virtualrootpath = self.request.get('VirtualRootPhysicalPath', None)
        if virtualrootpath is None:
            return False
        context = self.context
        return context.restrictedTraverse(virtualrootpath) == context


class RootAbsoluteURL(OFSTraversableAbsoluteURL):
    """An absolute_url adapter for the root object (OFS.Application)
    """
    def breadcrumbs(self):
        context = self.context
        request = self.request

        return ({'name': context.getId(),
                 'url': context.absolute_url()
                 },)
