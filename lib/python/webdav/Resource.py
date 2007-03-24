##############################################################################
#
# Copyright (c) 2002 Zope Corporation and Contributors. All Rights Reserved.
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

$Id$
"""

import mimetypes
import sys
import warnings
from urllib import unquote

import ExtensionClass
import Globals
from AccessControl import getSecurityManager
from Acquisition import aq_base, aq_inner, aq_parent
from zExceptions import BadRequest, MethodNotAllowed
from zExceptions import Unauthorized, Forbidden, NotFound
from zope.interface import implements
from ZPublisher.HTTPRangeSupport import HTTPRangeInterface

import davcmds
import Lockable
from common import absattr, urlfix, rfc1123_date, tokenFinder, urlbase
from common import IfParser
from common import isDavCollection
from common import Locked, Conflict, PreconditionFailed
from interfaces import IDAVResource
from interfaces import IWriteLock
from WriteLockInterface import WriteLockInterface

from zope.event import notify
from zope.app.event.objectevent import ObjectCopiedEvent
from zope.app.container.contained import ObjectMovedEvent
from zope.app.container.contained import notifyContainerModified
from OFS.event import ObjectClonedEvent
from OFS.event import ObjectWillBeMovedEvent
import OFS.subscribers


class Resource(ExtensionClass.Base, Lockable.LockableItem):

    """The Resource mixin class provides basic WebDAV support for
    non-collection objects. It provides default implementations
    for most supported WebDAV HTTP methods, however certain methods
    such as PUT should be overridden to ensure correct behavior in
    the context of the object type."""

    implements(IDAVResource)

    __dav_resource__=1

    __http_methods__=('GET', 'HEAD', 'POST', 'PUT', 'DELETE', 'OPTIONS',
                      'TRACE', 'PROPFIND', 'PROPPATCH', 'MKCOL', 'COPY',
                      'MOVE', 'LOCK', 'UNLOCK',
                      )

    __ac_permissions__=(
        ('View',                             ('HEAD',)),
        ('WebDAV access',                    ('PROPFIND', 'manage_DAVget',
                                              'listDAVObjects'),
         ('Authenticated', 'Manager')),
        ('Manage properties',                ('PROPPATCH',)),
        ('Delete objects',                   ('DELETE',)),
        ('WebDAV Lock items',                ('LOCK',)),
        ('WebDAV Unlock items',              ('UNLOCK',)),
    )

    def dav__init(self, request, response):
        # Init expected HTTP 1.1 / WebDAV headers which are not
        # currently set by the base response object automagically.
        #
        # We sniff for a ZServer response object, because we don't
        # want to write duplicate headers (since ZS writes Date
        # and Connection itself).
        if not hasattr(response, '_server_version'):
            response.setHeader('Connection', 'close')
            response.setHeader('Date', rfc1123_date(), 1)

        # HTTP Range support
        if HTTPRangeInterface.isImplementedBy(self):
            response.setHeader('Accept-Ranges', 'bytes')
        else:
            response.setHeader('Accept-Ranges', 'none')

    def dav__validate(self, object, methodname, REQUEST):
        msg='<strong>You are not authorized to access this resource.</strong>'
        method=None
        if hasattr(object, methodname):
            method=getattr(object, methodname)
        else:
            try:    method=object.aq_acquire(methodname)
            except: method=None

        if method is not None:
            try:
                return getSecurityManager().validate(None, object,
                                                     methodname,
                                                     method)
            except: pass

        raise Unauthorized, msg

    def dav__simpleifhandler(self, request, response, method='PUT',
                             col=0, url=None, refresh=0):
        ifhdr = request.get_header('If', None)
        if Lockable.wl_isLocked(self) and (not ifhdr):
            raise Locked, "Resource is locked."

        if not ifhdr: return None
        if not Lockable.wl_isLocked(self): return None

        # Since we're a simple if handler, and since some clients don't
        # pass in the port information in the resource part of an If
        # header, we're only going to worry about if the paths compare
        if url is None: url = urlfix(request['URL'], method)
        url = urlbase(url)              # Gets just the path information

        # if 'col' is passed in, an operation is happening on a submember
        # of a collection, while the Lock may be on the parent.  Lob off
        # the final part of the URL  (ie '/a/b/foo.html' becomes '/a/b/')
        if col: url = url[:url.rfind('/')+1]

        havetag = lambda x, self=self: self.wl_hasLock(x)
        found = 0; resourcetagged = 0
        taglist = IfParser(ifhdr)
        for tag in taglist:

            if not tag.resource:
                # There's no resource (url) with this tag
                tag_list = map(tokenFinder, tag.list)
                wehave = filter(havetag, tag_list)

                if not wehave: continue
                if tag.NOTTED: continue
                if refresh:
                    for token in wehave: self.wl_getLock(token).refresh()
                resourcetagged = 1
                found = 1; break
            elif urlbase(tag.resource) == url:
                resourcetagged = 1
                tag_list = map(tokenFinder, tag.list)
                wehave = filter(havetag, tag_list)

                if not wehave: continue
                if tag.NOTTED: continue
                if refresh:
                    for token in wehave: self.wl_getLock(token).refresh()
                found = 1; break

        if resourcetagged and (not found):
            raise PreconditionFailed, 'Condition failed.'
        elif resourcetagged and found:
            return 1
        else:
            return 0


    # WebDAV class 1 support
    def HEAD(self, REQUEST, RESPONSE):
        """Retrieve resource information without a response body."""
        self.dav__init(REQUEST, RESPONSE)

        content_type=None
        if hasattr(self, 'content_type'):
            content_type=absattr(self.content_type)
        if content_type is None:
            url=urlfix(REQUEST['URL'], 'HEAD')
            name=unquote(filter(None, url.split( '/')[-1]))
            content_type, encoding=mimetypes.guess_type(name)
        if content_type is None:
            if hasattr(self, 'default_content_type'):
                content_type=absattr(self.default_content_type)
        if content_type is None:
            content_type = 'application/octet-stream'
        RESPONSE.setHeader('Content-Type', content_type.lower())

        if hasattr(aq_base(self), 'get_size'):
            RESPONSE.setHeader('Content-Length', absattr(self.get_size))
        if hasattr(self, '_p_mtime'):
            mtime=rfc1123_date(self._p_mtime)
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
        raise MethodNotAllowed, 'Method not supported for this resource.'

    OPTIONS__roles__=None
    def OPTIONS(self, REQUEST, RESPONSE):
        """Retrieve communication options."""
        self.dav__init(REQUEST, RESPONSE)
        RESPONSE.setHeader('Allow', ', '.join(self.__http_methods__))
        RESPONSE.setHeader('Content-Length', 0)
        RESPONSE.setHeader('DAV', '1,2', 1)
        RESPONSE.setStatus(200)
        return RESPONSE

    TRACE__roles__=None
    def TRACE(self, REQUEST, RESPONSE):
        """Return the HTTP message received back to the client as the
        entity-body of a 200 (OK) response. This will often usually
        be intercepted by the web server in use. If not, the TRACE
        request will fail with a 405 (Method Not Allowed), since it
        is not often possible to reproduce the HTTP request verbatim
        from within the Zope environment."""
        self.dav__init(REQUEST, RESPONSE)
        raise MethodNotAllowed, 'Method not supported for this resource.'

    def DELETE(self, REQUEST, RESPONSE):
        """Delete a resource. For non-collection resources, DELETE may
        return either 200 or 204 (No Content) to indicate success."""
        self.dav__init(REQUEST, RESPONSE)
        ifhdr = REQUEST.get_header('If', '')
        url = urlfix(REQUEST['URL'], 'DELETE')
        name = unquote(filter(None, url.split( '/')[-1]))
        parent = aq_parent(aq_inner(self))
        # Lock checking
        if Lockable.wl_isLocked(self):
            if ifhdr:
                self.dav__simpleifhandler(REQUEST, RESPONSE, 'DELETE')
            else:
                # We're locked, and no if header was passed in, so
                # the client doesn't own a lock.
                raise Locked, 'Resource is locked.'
        elif (IWriteLock.providedBy(parent) or
                WriteLockInterface.isImplementedBy(parent)) and \
                parent.wl_isLocked():
            if ifhdr:
                parent.dav__simpleifhandler(REQUEST, RESPONSE, 'DELETE', col=1)
            else:
                # Our parent is locked, and no If header was passed in.
                # When a parent is locked, members cannot be removed
                raise PreconditionFailed, 'Resource is locked, and no '\
                      'condition was passed in.'
        # Either we're not locked, or a succesful lock token was submitted
        # so we can delete the lock now.
        # ajung: Fix for Collector # 2196

        if parent.manage_delObjects([name],REQUEST=None)  is None:
            RESPONSE.setStatus(204)
        else:

            RESPONSE.setStatus(403)

        return RESPONSE

    def PROPFIND(self, REQUEST, RESPONSE):
        """Retrieve properties defined on the resource."""
        self.dav__init(REQUEST, RESPONSE)
        cmd=davcmds.PropFind(REQUEST)
        result=cmd.apply(self)
        # work around MSIE DAV bug for creation and modified date
        if (REQUEST.get_header('User-Agent') ==
            'Microsoft Data Access Internet Publishing Provider DAV 1.1'):
            result = result.replace('<n:getlastmodified xmlns:n="DAV:">',
                                    '<n:getlastmodified xmlns:n="DAV:" xmlns:b="urn:uuid:c2f41010-65b3-11d1-a29f-00aa00c14882/" b:dt="dateTime.rfc1123">')
            result = result.replace('<n:creationdate xmlns:n="DAV:">',
                                    '<n:creationdate xmlns:n="DAV:" xmlns:b="urn:uuid:c2f41010-65b3-11d1-a29f-00aa00c14882/" b:dt="dateTime.tz">')
        RESPONSE.setStatus(207)
        RESPONSE.setHeader('Content-Type', 'text/xml; charset="utf-8"')
        RESPONSE.setBody(result)
        return RESPONSE

    def PROPPATCH(self, REQUEST, RESPONSE):
        """Set and/or remove properties defined on the resource."""
        self.dav__init(REQUEST, RESPONSE)
        if not hasattr(aq_base(self), 'propertysheets'):
            raise MethodNotAllowed, (
                  'Method not supported for this resource.')
        # Lock checking
        ifhdr = REQUEST.get_header('If', '')
        if Lockable.wl_isLocked(self):
            if ifhdr:
                self.dav__simpleifhandler(REQUEST, RESPONSE, 'PROPPATCH')
            else:
                raise Locked, 'Resource is locked.'

        cmd=davcmds.PropPatch(REQUEST)
        result=cmd.apply(self)
        RESPONSE.setStatus(207)
        RESPONSE.setHeader('Content-Type', 'text/xml; charset="utf-8"')
        RESPONSE.setBody(result)
        return RESPONSE

    def MKCOL(self, REQUEST, RESPONSE):
        """Create a new collection resource. If called on an existing
        resource, MKCOL must fail with 405 (Method Not Allowed)."""
        self.dav__init(REQUEST, RESPONSE)
        raise MethodNotAllowed, 'The resource already exists.'

    COPY__roles__=('Anonymous',)
    def COPY(self, REQUEST, RESPONSE):
        """Create a duplicate of the source resource whose state
        and behavior match that of the source resource as closely
        as possible. Though we may later try to make a copy appear
        seamless across namespaces (e.g. from Zope to Apache), COPY
        is currently only supported within the Zope namespace."""
        self.dav__init(REQUEST, RESPONSE)
        if not hasattr(aq_base(self), 'cb_isCopyable') or \
           not self.cb_isCopyable():
            raise MethodNotAllowed, 'This object may not be copied.'

        depth=REQUEST.get_header('Depth', 'infinity')
        if not depth in ('0', 'infinity'):
            raise BadRequest, 'Invalid Depth header.'

        dest=REQUEST.get_header('Destination', '')
        while dest and dest[-1]=='/':
            dest=dest[:-1]
        if not dest:
            raise BadRequest, 'Invalid Destination header.'

        try: path = REQUEST.physicalPathFromURL(dest)
        except ValueError:
            raise BadRequest, 'Invalid Destination header'

        name = path.pop()

        oflag=REQUEST.get_header('Overwrite', 'F').upper()
        if not oflag in ('T', 'F'):
            raise BadRequest, 'Invalid Overwrite header.'

        try: parent=self.restrictedTraverse(path)
        except ValueError:
            raise Conflict, 'Attempt to copy to an unknown namespace.'
        except NotFound:
            raise Conflict, 'Object ancestors must already exist.'
        except:
            t, v, tb=sys.exc_info()
            raise t, v
        if hasattr(parent, '__null_resource__'):
            raise Conflict, 'Object ancestors must already exist.'
        existing=hasattr(aq_base(parent), name)
        if existing and oflag=='F':
            raise PreconditionFailed, 'Destination resource exists.'
        try:
            parent._checkId(name, allow_dup=1)
        except:
            raise Forbidden, sys.exc_info()[1]
        try:
            parent._verifyObjectPaste(self)
        except Unauthorized:
            raise
        except:
            raise Forbidden, sys.exc_info()[1]

        # Now check locks.  The If header on a copy only cares about the
        # lock on the destination, so we need to check out the destinations
        # lock status.
        ifhdr = REQUEST.get_header('If', '')
        if existing:
            # The destination itself exists, so we need to check its locks
            destob = aq_base(parent)._getOb(name)
            if (IWriteLock.providedBy(destob) or
                    WriteLockInterface.isImplementedBy(destob)) and \
                    destob.wl_isLocked():
                if ifhdr:
                    itrue = destob.dav__simpleifhandler(
                        REQUEST, RESPONSE, 'COPY', refresh=1)
                    if not itrue:
                        raise PreconditonFailed
                else:
                    raise Locked, 'Destination is locked.'
        elif (IWriteLock.providedBy(parent) or
                WriteLockInterface.isImplementedBy(parent)) and \
                parent.wl_isLocked():
            if ifhdr:
                parent.dav__simpleifhandler(REQUEST, RESPONSE, 'COPY',
                                            refresh=1)
            else:
                raise Locked, 'Destination is locked.'

        self._notifyOfCopyTo(parent, op=0)
        ob = self._getCopy(parent)
        ob._setId(name)

        if depth=='0' and isDavCollection(ob):
            for id in ob.objectIds():
                ob._delObject(id)

        notify(ObjectCopiedEvent(ob, self))

        if existing:
            object=getattr(parent, name)
            self.dav__validate(object, 'DELETE', REQUEST)
            parent._delObject(name)

        parent._setObject(name, ob)
        ob = parent._getOb(name)
        ob._postCopy(parent, op=0)

        OFS.subscribers.compatibilityCall('manage_afterClone', ob, ob)

        notify(ObjectClonedEvent(ob))

        # We remove any locks from the copied object because webdav clients
        # don't track the lock status and the lock token for copied resources
        ob.wl_clearLocks()
        RESPONSE.setStatus(existing and 204 or 201)
        if not existing:
            RESPONSE.setHeader('Location', dest)
        RESPONSE.setBody('')
        return RESPONSE

    MOVE__roles__=('Anonymous',)
    def MOVE(self, REQUEST, RESPONSE):
        """Move a resource to a new location. Though we may later try to
        make a move appear seamless across namespaces (e.g. from Zope
        to Apache), MOVE is currently only supported within the Zope
        namespace."""
        self.dav__init(REQUEST, RESPONSE)
        self.dav__validate(self, 'DELETE', REQUEST)
        if not hasattr(aq_base(self), 'cb_isMoveable') or \
           not self.cb_isMoveable():
            raise MethodNotAllowed, 'This object may not be moved.'

        dest=REQUEST.get_header('Destination', '')

        try: path = REQUEST.physicalPathFromURL(dest)
        except ValueError:
            raise BadRequest, 'No destination given'

        flag=REQUEST.get_header('Overwrite', 'F')
        flag=flag.upper()

        name = path.pop()
        parent_path = '/'.join(path)

        try: parent = self.restrictedTraverse(path)
        except ValueError:
            raise Conflict, 'Attempt to move to an unknown namespace.'
        except 'Not Found':
            raise Conflict, 'The resource %s must exist.' % parent_path
        except:
            t, v, tb=sys.exc_info()
            raise t, v
        if hasattr(parent, '__null_resource__'):
            raise Conflict, 'The resource %s must exist.' % parent_path
        existing=hasattr(aq_base(parent), name)
        if existing and flag=='F':
            raise PreconditionFailed, 'Resource %s exists.' % dest
        try:
            parent._checkId(name, allow_dup=1)
        except:
            raise Forbidden, sys.exc_info()[1]
        try:
            parent._verifyObjectPaste(self)
        except Unauthorized:
            raise
        except:
            raise Forbidden, sys.exc_info()[1]

        # Now check locks.  Since we're affecting the resource that we're
        # moving as well as the destination, we have to check both.
        ifhdr = REQUEST.get_header('If', '')
        if existing:
            # The destination itself exists, so we need to check its locks
            destob = aq_base(parent)._getOb(name)
            if (IWriteLock.providedBy(destob) or
                    WriteLockInterface.isImplementedBy(destob)) and \
                    destob.wl_isLocked():
                if ifhdr:
                    itrue = destob.dav__simpleifhandler(
                        REQUEST, RESPONSE, 'MOVE', url=dest, refresh=1)
                    if not itrue:
                        raise PreconditionFailed
                else:
                    raise Locked, 'Destination is locked.'
        elif (IWriteLock.providedBy(parent) or
                WriteLockInterface.isImplementedBy(parent)) and \
                parent.wl_isLocked():
            # There's no existing object in the destination folder, so
            # we need to check the folders locks since we're changing its
            # member list
            if ifhdr:
                itrue = parent.dav__simpleifhandler(REQUEST, RESPONSE, 'MOVE',
                                                    col=1, url=dest, refresh=1)
                if not itrue:
                    raise PreconditionFailed, 'Condition failed.'
            else:
                raise Locked, 'Destination is locked.'
        if Lockable.wl_isLocked(self):
            # Lastly, we check ourselves
            if ifhdr:
                itrue = self.dav__simpleifhandler(REQUEST, RESPONSE, 'MOVE',
                                                  refresh=1)
                if not itrue:
                    raise PreconditionFailed, 'Condition failed.'
            else:
                raise PreconditionFailed, 'Source is locked and no '\
                      'condition was passed in.'

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

        try:
            orig_container._delObject(orig_id, suppress_events=True)
        except TypeError:
            # BBB: removed in Zope 2.11
            orig_container._delObject(orig_id)
            warnings.warn(
                "%s._delObject without suppress_events is deprecated "
                "and will be removed in Zope 2.11." %
                orig_container.__class__.__name__, DeprecationWarning)

        if existing:
            object=getattr(parent, name)
            self.dav__validate(object, 'DELETE', REQUEST)
            parent._delObject(name)

        try:
            parent._setObject(name, ob, set_owner=0, suppress_events=True)
        except TypeError:
            # BBB: removed in Zope 2.11
            parent._setObject(name, ob, set_owner=0)
            warnings.warn(
                "%s._setObject without suppress_events is deprecated "
                "and will be removed in Zope 2.11." %
                parent.__class__.__name__, DeprecationWarning)
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

    def LOCK(self, REQUEST, RESPONSE):
        """Lock a resource"""
        self.dav__init(REQUEST, RESPONSE)
        security = getSecurityManager()
        creator = security.getUser()
        body = REQUEST.get('BODY', '')
        ifhdr = REQUEST.get_header('If', None)
        depth = REQUEST.get_header('Depth', 'infinity')
        alreadylocked = Lockable.wl_isLocked(self)

        if body and alreadylocked:
            # This is a full LOCK request, and the Resource is
            # already locked, so we need to raise the alreadylocked
            # exception.
            RESPONSE.setStatus(423)
        elif body:
            # This is a normal lock request with an XML payload
            cmd = davcmds.Lock(REQUEST)
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
                raise PreconditionFailed, 'If Header Missing'
            taglist = IfParser(ifhdr)
            found = 0
            for tag in taglist:
                for listitem in tag.list:
                    token = tokenFinder(listitem)
                    if token and self.wl_hasLock(token):
                        lock = self.wl_getLock(token)
                        timeout = REQUEST.get_header('Timeout', 'Infinite')
                        lock.setTimeout(timeout) # automatically refreshes
                        found = 1

                        RESPONSE.setStatus(200)
                        RESPONSE.setHeader('Content-Type',
                                           'text/xml; charset="utf-8"')
                        RESPONSE.setBody(lock.asXML())
                        break
                if found: break
            if not found:
                RESPONSE.setStatus(412) # Precondition failed

        return RESPONSE

    def UNLOCK(self, REQUEST, RESPONSE):
        """Remove an existing lock on a resource."""
        self.dav__init(REQUEST, RESPONSE)
        security = getSecurityManager()
        token = REQUEST.get_header('Lock-Token', '')
        url = REQUEST['URL']
        token = tokenFinder(token)

        cmd = davcmds.Unlock()
        result = cmd.apply(self, token, url)

        if result:
            RESPONSE.setStatus(207)
            RESPONSE.setHeader('Content-Type', 'text/xml; charset="utf-8"')
            RESPONSE.setBody(result)
        else:
            RESPONSE.setStatus(204)     # No Content response code
        return RESPONSE


    def manage_DAVget(self):
        """Gets the document source"""
        # The default implementation calls manage_FTPget
        return self.manage_FTPget()

    def listDAVObjects(self):
        return []

Globals.default__class_init__(Resource)
