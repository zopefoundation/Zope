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
"""Provide basic resource functionality

$Id: browser.py 5259 2004-06-23 15:59:52Z philikon $
"""
import os
import urllib

from Acquisition import Explicit, aq_inner, aq_parent
from ComputedAttribute import ComputedAttribute
from browser import BrowserView
from OFS.Traversable import Traversable as OFSTraversable
from zope.exceptions import NotFoundError
from zope.interface import implements
from zope.component.interfaces import IResource
from zope.component import getViewProviding
from zope.publisher.interfaces.browser import IBrowserPublisher
from zope.app.traversing.browser.interfaces import IAbsoluteURL
from zope.app.datetimeutils import time as timeFromDateTimeString
from zope.app.publisher.fileresource import File, Image
from zope.app.publisher.pagetemplateresource import PageTemplate
from zope.app.publisher.browser.resources import empty

_marker = []

class Resource(Explicit):
    """A publishable resource
    """
    implements(IResource)

    def __init__(self, request):
        self.request = request

    def __call__(self):
        name = self.__name__
        container = self.__parent__

        url = str(getViewProviding(container, IAbsoluteURL, self.request))
        url = urllib.unquote(url)
        if not isinstance(container, DirectoryResource):
            name = '++resource++%s' % name
        return "%s/%s" % (url, name)

class PageTemplateResource(BrowserView, Resource):
    #implements(IBrowserPublisher)

    def __browser_default__(self, request):
        return self, ('render', )

    def render(self):
        """Rendered content"""
        pt = self.context
        return pt(self.request)

class FileResource(BrowserView, Resource):
    """A publishable file-based resource"""
    #implements(IBrowserPublisher)

    def __browser_default__(self, request):
        return self, (request.REQUEST_METHOD,)

    def GET(self):
        """Default content"""
        file = self.context
        request = self.request
        response = request.response

        # HTTP If-Modified-Since header handling. This is duplicated
        # from OFS.Image.Image - it really should be consolidated
        # somewhere...
        header = request.environ.get('If-Modified-Since', None)
        if header is not None:
            header = header.split(';')[0]
            # Some proxies seem to send invalid date strings for this
            # header. If the date string is not valid, we ignore it
            # rather than raise an error to be generally consistent
            # with common servers such as Apache (which can usually
            # understand the screwy date string as a lucky side effect
            # of the way they parse it).
            try:    mod_since=long(timeFromDateTimeString(header))
            except: mod_since=None
            if mod_since is not None:
                if getattr(file, 'lmt', None):
                    last_mod = long(file.lmt)
                else:
                    last_mod = long(0)
                if last_mod > 0 and last_mod <= mod_since:
                    response.setStatus(304)
                    return ''

        response.setHeader('Content-Type', file.content_type)
        response.setHeader('Last-Modified', file.lmh)

        # Cache for one day
        response.setHeader('Cache-Control', 'public,max-age=86400')
        f = open(file.path, 'rb')
        data = f.read()
        f.close()

        return data

    def HEAD(self):
        file = self.context
        response = self.request.response
        response = self.request.response
        response.setHeader('Content-Type', file.content_type)
        response.setHeader('Last-Modified', file.lmh)
        # Cache for one day
        response.setHeader('Cache-Control', 'public,max-age=86400')
        return ''

class ResourceFactory:

    factory = None
    resource = None

    def __init__(self, name, path, resource_factory=None):
        self.__name = name
        self.__rsrc = self.factory(path, name)
        if resource_factory is not None:
            self.resource = resource_factory

    def __call__(self, request):
        resource = self.resource(self.__rsrc, request)
        return resource

def _PageTemplate(self, path, name):
    # PageTemplate doesn't take a name parameter,
    # which makes it different from FileResource.
    # This is probably an error.
    template = PageTemplate(path)
    template.__name__ = name
    return template

class PageTemplateResourceFactory(ResourceFactory):
    """A factory for Page Template resources"""

    factory = _PageTemplate
    resource = PageTemplateResource

class FileResourceFactory(ResourceFactory):
    """A factory for File resources"""

    factory = File
    resource = FileResource

class ImageResourceFactory(ResourceFactory):
    """A factory for Image resources"""

    factory = Image
    resource = FileResource


# we only need this class a context for DirectoryResource
class Directory:

    def __init__(self, path, name):
        self.path = path
        self.__name__ = name

class DirectoryResource(BrowserView, Resource, OFSTraversable):
    #implements(IBrowserPublisher)

    resource_factories = {
        'gif':  ImageResourceFactory,
        'png':  ImageResourceFactory,
        'jpg':  ImageResourceFactory,
        'pt':   PageTemplateResourceFactory,
        'zpt':  PageTemplateResourceFactory,
        'html': PageTemplateResourceFactory,
        }

    default_factory = FileResourceFactory

    def __init__(self, context, request):
        BrowserView.__init__(self, context, request)
        # OFSTraversable.absolute_url() assumes self.REQUEST being
        # accessible:
        self.REQUEST = request

    def getId(self):
        name = self.__name__
        if not name.startswith('++resource++'):
            name = '++resource++%s' % self.__name__
        return name

    def __browser_default__(self, request):
        '''See interface IBrowserPublisher'''
        return empty, ()

    def __getitem__(self, name):
        res = self.get(name, None)
        if res is None:
            raise KeyError, name
        return res

    def get(self, name, default=_marker):
        path = self.context.path
        filename = os.path.join(path, name)
        if not os.path.isfile(filename):
            if default is _marker:
                raise NotFoundError(name)
            return default
        ext = name.split('.')[-1]
        factory = self.resource_factories.get(ext, self.default_factory)
        resource = factory(name, filename)(self.request)
        resource.__name__ = name
        resource.__parent__ = self
        # XXX __of__ wrapping is usually done on traversal.
        # However, we don't want to subclass Traversable (or do we?)
        # The right thing should probably be a specific (and very simple)
        # traverser that does __getitem__ and __of__.
        return resource.__of__(self)

class DirectoryResourceFactory(ResourceFactory):

    factory = Directory
    resource = DirectoryResource
