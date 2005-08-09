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
"""Machinery for making things viewable

$Id: viewable.py 12915 2005-05-31 10:23:19Z philikon $
"""
import inspect
from zExceptions import NotFound
from zope.exceptions import NotFoundError
from zope.component import getView, getDefaultViewName, ComponentLookupError
from zope.interface import implements
from zope.publisher.interfaces.browser import IBrowserRequest
from traversable import FakeRequest
from interfaces import IBrowserDefault

_marker = object

class Viewable:
    """A mixin to make an object viewable.
    """
    __five_viewable__ = True

    def __fallback_default__(self, request):
        """Try to dispatch to existing index_html or __call__"""
        if getattr(self, 'index_html', None):
            return self, ('index_html',)
        if getattr(self, 'fallback_call__', None):
            return self, ('fallback_call__',)
        # XXX Should never get this far. But if it does?

    # def fallback_call__(self, *args, **kw):
    #    """By default, return self"""
    #    return self

    # we have a default view, tell zpublisher to go there
    def __browser_default__(self, request):
        obj = self
        path = None
        try:
            obj, path = IBrowserDefault(self).defaultView(request)
        except ComponentLookupError:
            pass
        if path:
            if len(path) == 1 and path[0] == '__call__':
                return obj, ('fallback_call__',)
            return obj, path
        return self.__fallback_default__(request)
    __browser_default__.__five_method__ = True

    # this is technically not needed because ZPublisher finds our
    # attribute through __browser_default__; but we also want to be
    # able to call pages from python modules, PythonScripts or ZPT
    # def __call__(self, *args, **kw):
    #    """ """
    #    request = kw.get('REQUEST')
    #    if not IBrowserRequest.providedBy(request):
    #        request = getattr(self, 'REQUEST', None)
    #        if not IBrowserRequest.providedBy(request):
    #            request = FakeRequest()
    #    obj, path = self.__browser_default__(request)
    #    if path and not simpleRecursion():
    #        meth = obj.unrestrictedTraverse(path)
    #        if meth is not None:
    #            return meth(*args, **kw)
    #    return self.fallback_call__(*args, **kw)
    # __call__.__five_method__ = True

# def simpleRecursion():
#     # This tests for simple recursion, which can easily happen
#     # in CMF, like the following:
#     # - Object has a method named 'view'
#     # - 'view' method calls '__call__'
#     # - five:viewable overrides call to use '__browser_default__'
#     #   to find a default view and call it
#     # - defaultView is set to 'view'
#     # Bang. Infinite recursion.
#     stack = inspect.stack()
#     try:
#         if len(stack) < 4:
#             return False
#         if stack[2][1:4] == stack[4][1:4]:
#             return True
#     finally:
#         del stack
#     return False

class BrowserDefault(object):

    implements(IBrowserDefault)

    def __init__(self, context):
        self.context = context

    def defaultView(self, request):
        context = self.context
        try:
            name = getDefaultViewName(context, request)
            return context, [name,]
        except ComponentLookupError:
            return context, None
