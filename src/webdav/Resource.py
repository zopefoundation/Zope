##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""WebDAV support - resource objects.
"""

import mimetypes
import re
import sys
from urllib.parse import unquote

from AccessControl import ClassSecurityInfo
from AccessControl import getSecurityManager
from AccessControl.class_init import InitializeClass
from AccessControl.Permissions import delete_objects
from AccessControl.Permissions import manage_properties
from AccessControl.Permissions import view
from AccessControl.Permissions import webdav_access
from AccessControl.Permissions import webdav_lock_items
from AccessControl.Permissions import webdav_unlock_items
from Acquisition import aq_base
from Acquisition import aq_inner
from Acquisition import aq_parent
from ExtensionClass import Base
from OFS.event import ObjectClonedEvent
from OFS.event import ObjectWillBeMovedEvent
from OFS.interfaces import IWriteLock
from OFS.Lockable import LockableItem
from OFS.Lockable import wl_isLockable
from OFS.Lockable import wl_isLocked
from OFS.subscribers import compatibilityCall
from webdav import enable_ms_public_header
from webdav.common import Conflict
from webdav.common import IfParser
from webdav.common import Locked
from webdav.common import PreconditionFailed
from webdav.common import absattr
from webdav.common import isDavCollection
from webdav.common import tokenFinder
from webdav.common import urlbase
from webdav.common import urlfix
from webdav.interfaces import IDAVResource
from zExceptions import BadRequest
from zExceptions import Forbidden
from zExceptions import MethodNotAllowed
from zExceptions import NotFound
from zExceptions import Unauthorized
from zope.container.contained import notifyContainerModified
from zope.datetime import rfc1123_date
from zope.event import notify
from zope.interface import implementer
from zope.lifecycleevent import ObjectCopiedEvent
from zope.lifecycleevent import ObjectMovedEvent
from ZPublisher.HTTPRangeSupport import HTTPRangeInterface


ms_dav_agent = re.compile("Microsoft.*Internet Publishing.*")


@implementer(IDAVResource)
class Resource(Base, LockableItem):

    """The Resource mixin class provides basic WebDAV support for
    non-collection objects. It provides default implementations
    for most supported WebDAV HTTP methods, however certain methods
    such as PUT should be overridden to ensure correct behavior in
    the context of the object type."""

    __dav_resource__ = 1

    __http_methods__ = ('GET', 'HEAD', 'POST', 'PUT', 'DELETE', 'OPTIONS',
                        'TRACE', 'PROPFIND', 'PROPPATCH', 'MKCOL', 'COPY',
                        'MOVE', 'LOCK', 'UNLOCK',
                        )

    security = ClassSecurityInfo()
    security.setPermissionDefault(webdav_access, ('Authenticated', 'Manager'))

    def dav__init(self, request, response):
        # Init expected HTTP 1.1 / WebDAV headers which are not
        # currently set by the base response object automagically.
        #
        # We sniff for a ZServer response object, because we don't
        # want to write duplicate headers (since ZS writes Date
        # and Connection itself).
        if not hasattr(response, '_server_version'):
            response.setHeader('Date', rfc1123_date(), 1)

        # Initialize ETag header
        self.http__etag()

        # HTTP Range support
        if HTTPRangeInterface.providedBy(self):
            response.setHeader('Accept-Ranges', 'bytes')
        else:
            response.setHeader('Accept-Ranges', 'none')

    def dav__validate(self, object, methodname, REQUEST):
        msg = ('<strong>You are not authorized '
               'to access this resource.</strong>')
        method = None
        if hasattr(object, methodname):
            method = getattr(object, methodname)
        else:
            try:
                method = object.aq_acquire(methodname)
            except Exception:
                method = None

        if method is not None:
            try:
                return getSecurityManager().validate(None, object,
                                                     methodname,
                                                     method)
            except Exception:
                pass

        raise Unauthorized(msg)

    def dav__simpleifhandler(self, request, response, method='PUT',
                             col=0, url=None, refresh=0):
        ifhdr = request.get_header('If', None)

        lockable = wl_isLockable(self)
        if not lockable:
            # degenerate case, we shouldnt have even called this method.
            return None

        locked = self.wl_isLocked()

        if locked and (not ifhdr):
            raise Locked('Resource is locked.')

        if not ifhdr:
            return None

        # Since we're a simple if handler, and since some clients don't
        # pass in the port information in the resource part of an If
        # header, we're only going to worry about if the paths compare
        if url is None:
            url = urlfix(request['URL'], method)
        url = urlbase(url)  # Gets just the path information

        # if 'col' is passed in, an operation is happening on a submember
        # of a collection, while the Lock may be on the parent.  Lob off
        # the final part of the URL  (ie '/a/b/foo.html' becomes '/a/b/')
        if col:
            url = url[:url.rfind('/') + 1]

        found = 0
        resourcetagged = 0
        taglist = IfParser(ifhdr)
        for tag in taglist:

            if not tag.resource:
                # There's no resource (url) with this tag
                tag_list = [tokenFinder(x) for x in tag.list]
                wehave = [t for t in tag_list if self.wl_hasLock(t)]

                if not wehave:
                    continue
                if tag.NOTTED:
                    continue
                if refresh:
                    for token in wehave:
                        self.wl_getLock(token).refresh()
                resourcetagged = 1
                found = 1
                break
            elif unquote(urlbase(tag.resource)) == unquote(url):
                resourcetagged = 1
                tag_list = [tokenFinder(x) for x in tag.list]
                wehave = [t for t in tag_list if self.wl_hasLock(t)]

                if not wehave:
                    continue
                if tag.NOTTED:
                    continue
                if refresh:
                    for token in wehave:
                        self.wl_getLock(token).refresh()
                found = 1
                break

        if resourcetagged and (not found):
            raise PreconditionFailed('Condition failed.')
        elif resourcetagged and found:
            return 1
        else:
            return 0

    # WebDAV class 1 support
    @security.protected(view)
    def HEAD(self, REQUEST, RESPONSE):
        """Retrieve resource information without a response body."""
        self.dav__init(REQUEST, RESPONSE)

        content_type = None
        if hasattr(self, 'content_type'):
            content_type = absattr(self.content_type)
        if content_type is None:
            url = urlfix(REQUEST['URL'], 'HEAD')
            name = unquote([_f for _f in url.split('/') if _f][-1])
            content_type, encoding = mimetypes.guess_type(name)
        if content_type is None:
            if hasattr(self, 'default_content_type'):
                content_type = absattr(self.default_content_type)
        if content_type is None:
            content_type = 'application/octet-stream'
        RESPONSE.setHeader('Content-Type', content_type.lower())

        if hasattr(aq_base(self), 'get_size'):
            RESPONSE.setHeader('Content-Length', absattr(self.get_size))
        if hasattr(self, '_p_mtime'):
            mtime = rfc1123_date(self._p_mtime)
            RESPONSE.setHeader('Last-Modified', mtime)
        if hasattr(aq_base(self), 'http__etag'):
            etag = self.http__etag(readonly=1)
            if etag:
                RESPONSE.setHeader('Etag', etag)
        RESPONSE.setStatus(200)
        return RESPONSE

    def PUT(self, REQUEST, RESPONSE):
        """Replace the GET response entity of an existing resource.
        Because this is often object-dependent, objects which handle
        PUT should override the default PUT implementation with an
        object-specific implementation. By default, PUT requests
        fail with a 405 (Method Not Allowed)."""
        self.dav__init(REQUEST, RESPONSE)
        raise MethodNotAllowed('Method not supported for this resource.')

    @security.public
    def OPTIONS(self, REQUEST, RESPONSE):
        """Retrieve communication options."""
        self.dav__init(REQUEST, RESPONSE)
        RESPONSE.setHeader('Allow', ', '.join(self.__http_methods__))
        RESPONSE.setHeader('Content-Length', 0)
        RESPONSE.setHeader('DAV', '1,2', 1)

        # Microsoft Web Folders compatibility, only enabled if
        # User-Agent matches.
        if ms_dav_agent.match(REQUEST.get_header('User-Agent', '')):
            if enable_ms_public_header:
                RESPONSE.setHeader('Public', ', '.join(self.__http_methods__))

        RESPONSE.setStatus(200)
        return RESPONSE

    @security.public
    def TRACE(self, REQUEST, RESPONSE):
        """Return the HTTP message received back to the client as the
        entity-body of a 200 (OK) response. This will often usually
        be intercepted by the web server in use. If not, the TRACE
        request will fail with a 405 (Method Not Allowed), since it
        is not often possible to reproduce the HTTP request verbatim
        from within the Zope environment."""
        self.dav__init(REQUEST, RESPONSE)
        raise MethodNotAllowed('Method not supported for this resource.')

    @security.protected(delete_objects)
    def DELETE(self, REQUEST, RESPONSE):
        """Delete a resource. For non-collection resources, DELETE may
        return either 200 or 204 (No Content) to indicate success."""
        self.dav__init(REQUEST, RESPONSE)
        ifhdr = REQUEST.get_header('If', '')
        url = urlfix(REQUEST['URL'], 'DELETE')
        name = unquote([_f for _f in url.split('/') if _f][-1])
        parent = aq_parent(aq_inner(self))
        # Lock checking
        if wl_isLocked(self):
            if ifhdr:
                self.dav__simpleifhandler(REQUEST, RESPONSE, 'DELETE')
            else:
                # We're locked, and no if header was passed in, so
                # the client doesn't own a lock.
                raise Locked('Resource is locked.')
        elif IWriteLock.providedBy(parent) and parent.wl_isLocked():
            if ifhdr:
                parent.dav__simpleifhandler(REQUEST, RESPONSE, 'DELETE', col=1)
            else:
                # Our parent is locked, and no If header was passed in.
                # When a parent is locked, members cannot be removed
                raise Locked('Parent of this resource is locked.')
        # Either we're not locked, or a succesful lock token was submitted
        # so we can delete the lock now.
        # ajung: Fix for Collector # 2196

        if parent.manage_delObjects([name], REQUEST=None) is None:
            RESPONSE.setStatus(204)
        else:

            RESPONSE.setStatus(403)

        return RESPONSE

    @security.protected(webdav_access)
    def PROPFIND(self, REQUEST, RESPONSE):
        """Retrieve properties defined on the resource."""
        from webdav.davcmds import PropFind
        self.dav__init(REQUEST, RESPONSE)
        cmd = PropFind(REQUEST)
        result = cmd.apply(self)
        # work around MSIE DAV bug for creation and modified date
        if REQUEST.get_header('User-Agent') == \
           'Microsoft Data Access Internet Publishing Provider DAV 1.1':
            result = result.replace('<n:getlastmodified xmlns:n="DAV:">',
                                    '<n:getlastmodified xmlns:n="DAV:" xmlns:b="urn:uuid:c2f41010-65b3-11d1-a29f-00aa00c14882/" b:dt="dateTime.rfc1123">')  # NOQA
            result = result.replace('<n:creationdate xmlns:n="DAV:">',
                                    '<n:creationdate xmlns:n="DAV:" xmlns:b="urn:uuid:c2f41010-65b3-11d1-a29f-00aa00c14882/" b:dt="dateTime.tz">')  # NOQA
        RESPONSE.setStatus(207)
        RESPONSE.setHeader('Content-Type', 'text/xml; charset="utf-8"')
        RESPONSE.setBody(result)
        return RESPONSE

    @security.protected(manage_properties)
    def PROPPATCH(self, REQUEST, RESPONSE):
        """Set and/or remove properties defined on the resource."""
        from webdav.davcmds import PropPatch
        self.dav__init(REQUEST, RESPONSE)
        if not hasattr(aq_base(self), 'propertysheets'):
            raise MethodNotAllowed(
                'Method not supported for this resource.')
        # Lock checking
        ifhdr = REQUEST.get_header('If', '')
        if wl_isLocked(self):
            if ifhdr:
                self.dav__simpleifhandler(REQUEST, RESPONSE, 'PROPPATCH')
            else:
                raise Locked('Resource is locked.')

        cmd = PropPatch(REQUEST)
        result = cmd.apply(self)
        RESPONSE.setStatus(207)
        RESPONSE.setHeader('Content-Type', 'text/xml; charset="utf-8"')
        RESPONSE.setBody(result)
        return RESPONSE

    def MKCOL(self, REQUEST, RESPONSE):
        """Create a new collection resource. If called on an existing
        resource, MKCOL must fail with 405 (Method Not Allowed)."""
        self.dav__init(REQUEST, RESPONSE)
        raise MethodNotAllowed('The resource already exists.')

    @security.public
    def COPY(self, REQUEST, RESPONSE):
        """Create a duplicate of the source resource whose state
        and behavior match that of the source resource as closely
        as possible. Though we may later try to make a copy appear
        seamless across namespaces (e.g. from Zope to Apache), COPY
        is currently only supported within the Zope namespace."""
        self.dav__init(REQUEST, RESPONSE)
        if not hasattr(aq_base(self), 'cb_isCopyable') or \
           not self.cb_isCopyable():
            raise MethodNotAllowed('This object may not be copied.')

        depth = REQUEST.get_header('Depth', 'infinity')
        if depth not in ('0', 'infinity'):
            raise BadRequest('Invalid Depth header.')

        dest = REQUEST.get_header('Destination', '')
        while dest and dest[-1] == '/':
            dest = dest[:-1]
        if not dest:
            raise BadRequest('Invalid Destination header.')

        try:
            path = REQUEST.physicalPathFromURL(dest)
        except ValueError:
            raise BadRequest('Invalid Destination header')

        name = path.pop()

        oflag = REQUEST.get_header('Overwrite', 'F').upper()
        if oflag not in ('T', 'F'):
            raise BadRequest('Invalid Overwrite header.')

        try:
            parent = self.restrictedTraverse(path)
        except ValueError:
            raise Conflict('Attempt to copy to an unknown namespace.')
        except NotFound:
            raise Conflict('Object ancestors must already exist.')
        except Exception:
            raise

        if hasattr(parent, '__null_resource__'):
            raise Conflict('Object ancestors must already exist.')
        existing = hasattr(aq_base(parent), name)
        if existing and oflag == 'F':
            raise PreconditionFailed('Destination resource exists.')
        try:
            parent._checkId(name, allow_dup=1)
        except Exception:
            raise Forbidden(sys.exc_info()[1])
        try:
            parent._verifyObjectPaste(self)
        except Unauthorized:
            raise
        except Exception:
            raise Forbidden(sys.exc_info()[1])

        # Now check locks.  The If header on a copy only cares about the
        # lock on the destination, so we need to check out the destinations
        # lock status.
        ifhdr = REQUEST.get_header('If', '')
        if existing:
            # The destination itself exists, so we need to check its locks
            destob = aq_base(parent)._getOb(name)
            if IWriteLock.providedBy(destob) and destob.wl_isLocked():
                if ifhdr:
                    itrue = destob.dav__simpleifhandler(
                        REQUEST, RESPONSE, 'COPY', refresh=1)
                    if not itrue:
                        raise PreconditionFailed()
                else:
                    raise Locked('Destination is locked.')
        elif IWriteLock.providedBy(parent) and parent.wl_isLocked():
            if ifhdr:
                parent.dav__simpleifhandler(REQUEST, RESPONSE, 'COPY',
                                            refresh=1)
            else:
                raise Locked('Destination is locked.')

        self._notifyOfCopyTo(parent, op=0)
        ob = self._getCopy(parent)
        ob._setId(name)

        if depth == '0' and isDavCollection(ob):
            for id in ob.objectIds():
                ob._delObject(id)

        notify(ObjectCopiedEvent(ob, self))

        if existing:
            object = getattr(parent, name)
            self.dav__validate(object, 'DELETE', REQUEST)
            parent._delObject(name)

        parent._setObject(name, ob)
        ob = parent._getOb(name)
        ob._postCopy(parent, op=0)

        compatibilityCall('manage_afterClone', ob, ob)

        notify(ObjectClonedEvent(ob))

        # We remove any locks from the copied object because webdav clients
        # don't track the lock status and the lock token for copied resources
        ob.wl_clearLocks()
        RESPONSE.setStatus(existing and 204 or 201)
        if not existing:
            RESPONSE.setHeader('Location', dest)
        RESPONSE.setBody('')
        return RESPONSE

    @security.public
    def MOVE(self, REQUEST, RESPONSE):
        """Move a resource to a new location. Though we may later try to
        make a move appear seamless across namespaces (e.g. from Zope
        to Apache), MOVE is currently only supported within the Zope
        namespace."""
        self.dav__init(REQUEST, RESPONSE)
        self.dav__validate(self, 'DELETE', REQUEST)
        if not hasattr(aq_base(self), 'cb_isMoveable') or \
           not self.cb_isMoveable():
            raise MethodNotAllowed('This object may not be moved.')

        dest = REQUEST.get_header('Destination', '')

        try:
            path = REQUEST.physicalPathFromURL(dest)
        except ValueError:
            raise BadRequest('No destination given')

        flag = REQUEST.get_header('Overwrite', 'F')
        flag = flag.upper()

        name = path.pop()
        parent_path = '/'.join(path)

        try:
            parent = self.restrictedTraverse(path)
        except ValueError:
            raise Conflict('Attempt to move to an unknown namespace.')
        except 'Not Found':
            raise Conflict('The resource %s must exist.' % parent_path)
        except Exception:
            raise

        if hasattr(parent, '__null_resource__'):
            raise Conflict('The resource %s must exist.' % parent_path)
        existing = hasattr(aq_base(parent), name)
        if existing and flag == 'F':
            raise PreconditionFailed('Resource %s exists.' % dest)
        try:
            parent._checkId(name, allow_dup=1)
        except Exception:
            raise Forbidden(sys.exc_info()[1])
        try:
            parent._verifyObjectPaste(self)
        except Unauthorized:
            raise
        except Exception:
            raise Forbidden(sys.exc_info()[1])

        # Now check locks.  Since we're affecting the resource that we're
        # moving as well as the destination, we have to check both.
        ifhdr = REQUEST.get_header('If', '')
        if existing:
            # The destination itself exists, so we need to check its locks
            destob = aq_base(parent)._getOb(name)
            if IWriteLock.providedBy(destob) and destob.wl_isLocked():
                if ifhdr:
                    itrue = destob.dav__simpleifhandler(
                        REQUEST, RESPONSE, 'MOVE', url=dest, refresh=1)
                    if not itrue:
                        raise PreconditionFailed
                else:
                    raise Locked('Destination is locked.')
        elif IWriteLock.providedBy(parent) and parent.wl_isLocked():
            # There's no existing object in the destination folder, so
            # we need to check the folders locks since we're changing its
            # member list
            if ifhdr:
                itrue = parent.dav__simpleifhandler(REQUEST, RESPONSE, 'MOVE',
                                                    col=1, url=dest, refresh=1)
                if not itrue:
                    raise PreconditionFailed('Condition failed.')
            else:
                raise Locked('Destination is locked.')
        if wl_isLocked(self):
            # Lastly, we check ourselves
            if ifhdr:
                itrue = self.dav__simpleifhandler(REQUEST, RESPONSE, 'MOVE',
                                                  refresh=1)
                if not itrue:
                    raise PreconditionFailed('Condition failed.')
            else:
                raise Locked('Source is locked and no condition was passed in')

        orig_container = aq_parent(aq_inner(self))
        orig_id = self.getId()

        self._notifyOfCopyTo(parent, op=1)

        notify(ObjectWillBeMovedEvent(self, orig_container, orig_id,
                                      parent, name))

        # try to make ownership explicit so that it gets carried
        # along to the new location if needed.
        self.manage_changeOwnershipType(explicit=1)

        ob = self._getCopy(parent)
        ob._setId(name)

        orig_container._delObject(orig_id, suppress_events=True)

        if existing:
            object = getattr(parent, name)
            self.dav__validate(object, 'DELETE', REQUEST)
            parent._delObject(name)

        parent._setObject(name, ob, set_owner=0, suppress_events=True)
        ob = parent._getOb(name)

        notify(ObjectMovedEvent(ob, orig_container, orig_id, parent, name))
        notifyContainerModified(orig_container)
        if aq_base(orig_container) is not aq_base(parent):
            notifyContainerModified(parent)

        ob._postCopy(parent, op=1)

        # try to make ownership implicit if possible
        ob.manage_changeOwnershipType(explicit=0)

        RESPONSE.setStatus(existing and 204 or 201)
        if not existing:
            RESPONSE.setHeader('Location', dest)
        RESPONSE.setBody('')
        return RESPONSE

    # WebDAV Class 2, Lock and Unlock

    @security.protected(webdav_lock_items)
    def LOCK(self, REQUEST, RESPONSE):
        """Lock a resource"""
        from webdav.davcmds import Lock
        self.dav__init(REQUEST, RESPONSE)
        security = getSecurityManager()
        creator = security.getUser()
        body = REQUEST.get('BODY', '')
        ifhdr = REQUEST.get_header('If', None)
        depth = REQUEST.get_header('Depth', 'infinity')
        alreadylocked = wl_isLocked(self)

        if body and alreadylocked:
            # This is a full LOCK request, and the Resource is
            # already locked, so we need to raise the alreadylocked
            # exception.
            RESPONSE.setStatus(423)
        elif body:
            # This is a normal lock request with an XML payload
            cmd = Lock(REQUEST)
            token, result = cmd.apply(self, creator, depth=depth)
            if result:
                # Return the multistatus result (there were multiple
                # errors.  Note that davcmds.Lock.apply aborted the
                # transaction already.
                RESPONSE.setStatus(207)
                RESPONSE.setHeader('Content-Type', 'text/xml; charset="utf-8"')
                RESPONSE.setBody(result)
            else:
                # Success
                lock = self.wl_getLock(token)
                RESPONSE.setStatus(200)
                RESPONSE.setHeader('Content-Type', 'text/xml; charset="utf-8"')
                RESPONSE.setHeader('Lock-Token', 'opaquelocktoken:' + token)
                RESPONSE.setBody(lock.asXML())
        else:
            # There's no body, so this likely to be a refresh request
            if not ifhdr:
                raise PreconditionFailed('If Header Missing')
            taglist = IfParser(ifhdr)
            found = 0
            for tag in taglist:
                for listitem in tag.list:
                    token = tokenFinder(listitem)
                    if token and self.wl_hasLock(token):
                        lock = self.wl_getLock(token)
                        timeout = REQUEST.get_header('Timeout', 'Infinite')
                        lock.setTimeout(timeout)  # automatically refreshes
                        found = 1

                        RESPONSE.setStatus(200)
                        RESPONSE.setHeader('Content-Type',
                                           'text/xml; charset="utf-8"')
                        RESPONSE.setBody(lock.asXML())
                        break
                if found:
                    break
            if not found:
                RESPONSE.setStatus(412)  # Precondition failed

        return RESPONSE

    @security.protected(webdav_unlock_items)
    def UNLOCK(self, REQUEST, RESPONSE):
        """Remove an existing lock on a resource."""
        from webdav.davcmds import Unlock
        self.dav__init(REQUEST, RESPONSE)
        token = REQUEST.get_header('Lock-Token', '')
        url = REQUEST['URL']
        token = tokenFinder(token)

        cmd = Unlock()
        result = cmd.apply(self, token, url)

        if result:
            RESPONSE.setStatus(207)
            RESPONSE.setHeader('Content-Type', 'text/xml; charset="utf-8"')
            RESPONSE.setBody(result)
        else:
            RESPONSE.setStatus(204)     # No Content response code
        return RESPONSE

    @security.protected(webdav_access)
    def manage_DAVget(self):
        """Gets the document source or file data.

        This implementation is a last resort fallback. The subclass should
        override this method to provide a more appropriate implementation.

        Using PrincipiaSearchSource, if it exists. It is one of the few shared
        interfaces still around in common Zope content objects.
        """
        if getattr(aq_base(self), 'PrincipiaSearchSource', None) is not None:
            return self.PrincipiaSearchSource()

        # If it doesn't exist, give up.
        return ''

    @security.protected(webdav_access)
    def listDAVObjects(self):
        return []


InitializeClass(Resource)
