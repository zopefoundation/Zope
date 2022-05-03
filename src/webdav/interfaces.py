##############################################################################
#
# Copyright (c) 2005 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""webdav interfaces.
"""

from OFS.interfaces import IWriteLock
from zope.schema import Bool
from zope.schema import Tuple


# XXX: might contain non-API methods and outdated comments;
#      not synced with ZopeBook API Reference;
#      based on webdav.Resource.Resource
class IDAVResource(IWriteLock):

    """Provide basic WebDAV support for non-collection objects."""

    __dav_resource__ = Bool(
        title="Is DAV resource")

    __http_methods__ = Tuple(
        title="HTTP methods",
        description="Sequence of valid HTTP methods")

    def dav__init(request, response):
        """Init expected HTTP 1.1 / WebDAV headers which are not
        currently set by the base response object automagically.

        Also, we sniff for a ZServer response object, because we don't
        want to write duplicate headers (since ZS writes Date
        and Connection itself).
        """

    def dav__validate(object, methodname, REQUEST):
        """
        """

    def dav__simpleifhandler(request, response, method='PUT',
                             col=0, url=None, refresh=0):
        """
        """

    def HEAD(REQUEST, RESPONSE):
        """Retrieve resource information without a response body."""

    def PUT(REQUEST, RESPONSE):
        """Replace the GET response entity of an existing resource.
        Because this is often object-dependent, objects which handle
        PUT should override the default PUT implementation with an
        object-specific implementation. By default, PUT requests
        fail with a 405 (Method Not Allowed)."""

    def OPTIONS(REQUEST, RESPONSE):
        """Retrieve communication options."""

    def TRACE(REQUEST, RESPONSE):
        """Return the HTTP message received back to the client as the
        entity-body of a 200 (OK) response. This will often usually
        be intercepted by the web server in use. If not, the TRACE
        request will fail with a 405 (Method Not Allowed), since it
        is not often possible to reproduce the HTTP request verbatim
        from within the Zope environment."""

    def DELETE(REQUEST, RESPONSE):
        """Delete a resource. For non-collection resources, DELETE may
        return either 200 or 204 (No Content) to indicate success."""

    def PROPFIND(REQUEST, RESPONSE):
        """Retrieve properties defined on the resource."""

    def PROPPATCH(REQUEST, RESPONSE):
        """Set and/or remove properties defined on the resource."""

    def MKCOL(REQUEST, RESPONSE):
        """Create a new collection resource. If called on an existing
        resource, MKCOL must fail with 405 (Method Not Allowed)."""

    def COPY(REQUEST, RESPONSE):
        """Create a duplicate of the source resource whose state
        and behavior match that of the source resource as closely
        as possible. Though we may later try to make a copy appear
        seamless across namespaces (e.g. from Zope to Apache), COPY
        is currently only supported within the Zope namespace."""

    def MOVE(REQUEST, RESPONSE):
        """Move a resource to a new location. Though we may later try to
        make a move appear seamless across namespaces (e.g. from Zope
        to Apache), MOVE is currently only supported within the Zope
        namespace."""

    def LOCK(REQUEST, RESPONSE):
        """Lock a resource"""

    def UNLOCK(REQUEST, RESPONSE):
        """Remove an existing lock on a resource."""

    def manage_DAVget():
        """Gets the document source"""

    def listDAVObjects():
        """
        """


# XXX: might contain non-API methods and outdated comments;
#      not synced with ZopeBook API Reference;
#      based on webdav.Collection.Collection
class IDAVCollection(IDAVResource):

    """The Collection class provides basic WebDAV support for
    collection objects. It provides default implementations
    for all supported WebDAV HTTP methods. The behaviors of some
    WebDAV HTTP methods for collections are slightly different
    than those for non-collection resources."""

    __dav_collection__ = Bool(
        title="Is a DAV collection",
        description="Should be true")

    def PUT(REQUEST, RESPONSE):
        """The PUT method has no inherent meaning for collection
        resources, though collections are not specifically forbidden
        to handle PUT requests. The default response to a PUT request
        for collections is 405 (Method Not Allowed)."""

    def DELETE(REQUEST, RESPONSE):
        """Delete a collection resource. For collection resources, DELETE
        may return either 200 (OK) or 204 (No Content) to indicate total
        success, or may return 207 (Multistatus) to indicate partial
        success. Note that in Zope a DELETE currently never returns 207."""
