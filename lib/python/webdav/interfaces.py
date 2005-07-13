##############################################################################
#
# Copyright (c) 2005 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""webdav z3 interfaces.

$Id$
"""

from zope.interface import Interface
from zope.schema import Bool, Tuple


class IWriteLock(Interface):

    """Basic protocol needed to support the write lock machinery.

    It must be able to answer the questions:

     o Is the object locked?

     o Is the lock owned by the current user?

     o What lock tokens are associated with the current object?

     o What is their state (how long until they're supposed to time out?,
       what is their depth?  what type are they?

    And it must be able to do the following:

     o Grant a write lock on the object to a specified user.

       - *If lock depth is infinite, this must also grant locks on **all**
         subobjects, or fail altogether*

     o Revoke a lock on the object.

       - *If lock depth is infinite, this must also revoke locks on all
         subobjects*

    **All methods in the WriteLock interface that deal with checking valid
    locks MUST check the timeout values on the lockitem (ie, by calling
    'lockitem.isValid()'), and DELETE the lock if it is no longer valid**
    """

    def wl_lockItems(killinvalids=0):
        """ Returns (key, value) pairs of locktoken, lock.

        if 'killinvalids' is true, invalid locks (locks whose timeout
        has been exceeded) will be deleted"""

    def wl_lockValues(killinvalids=0):
        """ Returns a sequence of locks.  if 'killinvalids' is true,
        invalid locks will be deleted"""

    def wl_lockTokens(killinvalids=0):
        """ Returns a sequence of lock tokens.  if 'killinvalids' is true,
        invalid locks will be deleted"""

    def wl_hasLock(token, killinvalids=0):
        """ Returns true if the lock identified by the token is attached
        to the object. """

    def wl_isLocked():
        """ Returns true if 'self' is locked at all.  If invalid locks
        still exist, they should be deleted."""

    def wl_setLock(locktoken, lock):
        """ Store the LockItem, 'lock'.  The locktoken will be used to fetch
        and delete the lock.  If the lock exists, this MUST
        overwrite it if all of the values except for the 'timeout' on the
        old and new lock are the same. """

    def wl_getLock(locktoken):
        """ Returns the locktoken identified by the locktokenuri """

    def wl_delLock(locktoken):
        """ Deletes the locktoken identified by the locktokenuri """

    def wl_clearLocks():
        """ Deletes ALL DAV locks on the object - should only be called
        by lock management machinery. """


# XXX: might contain non-API methods and outdated comments;
#      not synced with ZopeBook API Reference;
#      based on webdav.Resource.Resource
class IDAVResource(IWriteLock):

    """Provide basic WebDAV support for non-collection objects."""

    __dav_resource__ = Bool(
        title=u"Is DAV resource"
        )

    __http_methods__ = Tuple(
        title=u"HTTP methods",
        description=u"Sequence of valid HTTP methods"
        )

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
        title=u"Is a DAV collection",
        description=u"Should be true",
        )

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
