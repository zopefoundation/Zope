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
"""Machinery for making things traversable through adaptation

$Id: traversable.py 12915 2005-05-31 10:23:19Z philikon $
"""
from zExceptions import NotFound
from zope.exceptions import NotFoundError
from zope.component import getView, ComponentLookupError
from zope.interface import implements
from zope.publisher.interfaces.browser import IBrowserRequest
from zope.app.traversing.interfaces import ITraverser, ITraversable
from zope.app.traversing.adapters import DefaultTraversable
from zope.app.traversing.adapters import traversePathElement

from AccessControl import getSecurityManager
from Products.Five.security import newInteraction

_marker = object

class FakeRequest:
    implements(IBrowserRequest)

    def getPresentationSkin(self):
        return None

    def has_key(self, key):
        return False

class Traversable:
    """A mixin to make an object traversable using an ITraverser adapter.
    """
    __five_traversable__ = True

    def __fallback_traverse__(self, REQUEST, name):
        """Method hook for fallback traversal

        This method is called by __bobo_traverse___ when Zope3-style
        ITraverser traversal fails.

        Just raise a AttributeError to indicate traversal has failed
        and let Zope do it's job.
        """
        raise AttributeError, name

    def __bobo_traverse__(self, REQUEST, name):
        """Hook for Zope 2 traversal

        This method is called by Zope 2's ZPublisher upon traversal.
        It allows us to trick it into faking the Zope 3 traversal system
        by using an ITraverser adapter.
        """
        if not IBrowserRequest.providedBy(REQUEST):
            # Try to get the REQUEST by acquisition
            REQUEST = getattr(self, 'REQUEST', None)
            if not IBrowserRequest.providedBy(REQUEST):
                REQUEST = FakeRequest()
        # con Zope 3 into using Zope 2's checkPermission
        newInteraction()
        try:
            return ITraverser(self).traverse(
                path=[name], request=REQUEST).__of__(self)
        except (ComponentLookupError, NotFoundError,
                AttributeError, KeyError, NotFound):
            pass
        try:
            return getattr(self, name)
        except AttributeError:
            pass
        try:
            return self[name]
        except (AttributeError, KeyError):
            pass
        return self.__fallback_traverse__(REQUEST, name)
    __bobo_traverse__.__five_method__ = True


class FiveTraversable(DefaultTraversable):

    def traverse(self, name, furtherPath):
        context = self._subject
        __traceback_info__ = (context, name, furtherPath)
        # Find the REQUEST
        REQUEST = getattr(context, 'REQUEST', None)
        if not IBrowserRequest.providedBy(REQUEST):
            REQUEST = FakeRequest()
        # Try to lookup a view first
        try:
            return getView(context, name, REQUEST)
        except ComponentLookupError:
            pass
        # If a view can't be found, then use default traversable
        return super(FiveTraversable, self).traverse(name, furtherPath)
