##############################################################################
#
# Copyright (c) 2007 Zope Foundation and Contributors.
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
"""Legacy browser view tests.

Here we nake sure that legacy implementations of views (e.g. those
which mix-in one of the Acquisition base classes without knowing
better) still work.
"""
import Acquisition
import OFS.SimpleItem

from zope.interface import implements
from zope.traversing.interfaces import ITraversable
from zope.contentprovider.interfaces import IContentProvider
from Products.Five import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

class LegacyAttributes(BrowserView):
    """Make sure that those old aq_* attributes on Five BrowserViews
    still work, in particular aq_chain, even though BrowserView may
    not be an Acquisition-decendant class anymore...
    """

    def __call__(self):
        return repr([obj for obj in self.aq_chain])

class ExplicitLegacyAttributes(Acquisition.Explicit):
    """Make sure that those old aq_* attributes work on browser views
    that only inherit from Explicit as well."""

    def __call__(self):
        return repr([obj for obj in self.aq_chain])

class LegacyTemplate(BrowserView):

    template = ViewPageTemplateFile('falcon.pt')

    def __call__(self):
        return self.template()

class LegacyTemplateTwo(BrowserView):

    def __init__(self, context, request):
        self.__parent__ = context
        self.context = context
        self.request = request
        self.template = ViewPageTemplateFile('falcon.pt')

    def __call__(self):
        return self.template()

class Explicit(Acquisition.Explicit):

    def render(self):
        return 'Explicit'

class ExplicitWithTemplate(Acquisition.Explicit):

    template = ViewPageTemplateFile('falcon.pt')

class Implicit(Acquisition.Implicit):

    index_html = None  # we don't want to acquire this!
    def render(self):
        return 'Implicit'

class ImplicitWithTemplate(Acquisition.Implicit):

    template = ViewPageTemplateFile('falcon.pt')


class ExplicitContentProvider(Acquisition.Explicit):
    implements(IContentProvider)

    def __init__(self, context, request, view):
        self.context = context
        self.request = request
        self.view = view
        # A content provider must set __parent__ to view or context.
        self.__parent__ = context

    def update(self):
        pass

    def render(self):
        return 'Content provider inheriting from Explicit'

class ExplicitViewlet(Acquisition.Explicit):

    def __init__(self, context, request, view, manager):
        self.context = context
        self.request = request

    def update(self):
        # Make sure that the viewlet has the legacy attributes and
        # they point to the right objects.
        assert self.aq_parent == self.context
        assert self.aq_base == self

    def render(self):
        return 'Viewlet inheriting from Explicit'

class BrowserViewViewlet(BrowserView):

    def __init__(self, context, request, view, manager):
        # This is the tricky bit.  super(...).__init__ wouldn't
        # necessarily have to resolve to BrowserView.__init__ because
        # <browser:viewlet /> generates classes on the fly with a
        # mix-in base class...
        super(BrowserViewViewlet, self).__init__(context, request)
        self.view = view
        self.manager = manager

    def update(self):
        pass

    def render(self):
        return 'BrowserView viewlet'


class LegacyNamespace(object):
    implements(ITraversable)

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def traverse(self, name, ignored):
        return LegacyNamespaceObject(name)

class LegacyNamespaceObject(OFS.SimpleItem.SimpleItem):

    def __init__(self, name):
        self.id = name
