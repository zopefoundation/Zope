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
"""WebDAV support - null resource objects.
"""

import os
import sys

from AccessControl.class_init import InitializeClass
from AccessControl.Permissions import add_folders
from AccessControl.Permissions import view
from AccessControl.Permissions import webdav_access
from AccessControl.Permissions import webdav_lock_items
from AccessControl.Permissions import webdav_unlock_items
from AccessControl.SecurityInfo import ClassSecurityInfo
from AccessControl.SecurityManagement import getSecurityManager
from Acquisition import Implicit
from Acquisition import aq_base
from Acquisition import aq_parent
from App.special_dtml import DTMLFile
from OFS.CopySupport import CopyError
from OFS.DTMLDocument import DTMLDocument
from OFS.Image import File
from OFS.Image import Image
from OFS.interfaces import IWriteLock
from OFS.SimpleItem import Item_w__name__
from Persistence import Persistent
from Products.PageTemplates.ZopePageTemplate import ZopePageTemplate
from webdav.common import Conflict
from webdav.common import IfParser
from webdav.common import Locked
from webdav.common import PreconditionFailed
from webdav.common import UnsupportedMediaType
from webdav.common import isDavCollection
from webdav.common import tokenFinder
from webdav.davcmds import Lock
from webdav.davcmds import Unlock
from webdav.Resource import Resource
from zExceptions import BadRequest
from zExceptions import Forbidden
from zExceptions import MethodNotAllowed
from zExceptions import NotFound
from zExceptions import Unauthorized
from zope.contenttype import guess_content_type


# XXX Originall in ZServer.Zope2.Startup.config
# XXX Unclear if it is still relevant
LARGE_FILE_THRESHOLD = 524288


class NullResource(Persistent, Implicit, Resource):

    """Null resources are used to handle HTTP method calls on
    objects which do not yet exist in the url namespace."""

    __null_resource__ = 1
    zmi_icon = 'fas fa-edit'

    security = ClassSecurityInfo()

    def __init__(self, parent, name, request=None):
        self.__name__ = name
        self.__parent__ = parent

    def __bobo_traverse__(self, REQUEST, name=None):
        # We must handle traversal so that we can recognize situations
        # where a 409 Conflict must be returned instead of the normal
        # 404 Not Found, per [WebDAV 8.3.1].
        try:
            return getattr(self, name)
        except Exception:
            pass
        method = REQUEST.get('REQUEST_METHOD', 'GET')
        if method in ('PUT', 'MKCOL', 'LOCK'):
            raise Conflict('Collection ancestors must already exist.')
        raise NotFound('The requested resource was not found.')

    @security.protected(view)
    def HEAD(self, REQUEST, RESPONSE):
        """Retrieve resource information without a response message body."""
        self.dav__init(REQUEST, RESPONSE)
        RESPONSE.setBody('', lock=True)
        raise NotFound('The requested resource does not exist.')

    # Most methods return 404 (Not Found) for null resources.
    DELETE = TRACE = PROPFIND = PROPPATCH = COPY = MOVE = HEAD
    index_html = HEAD

    def _default_PUT_factory(self, name, typ, body):
        # See if the name contains a file extension
        shortname, ext = os.path.splitext(name)
        ext = ext.lower()

        # Make sure the body is bytes
        if not isinstance(body, bytes):
            body = body.encode('UTF-8')

        # Guess the type of file if the passed content-type is
        # just the generic application/octet-stream
        if not typ or typ == 'application/octet-stream':
            typ, encoding = guess_content_type(name, body)

        if ext == '.dtml':
            ob = DTMLDocument('', __name__=name)
        elif typ in ('text/html', 'text/xml'):
            ob = ZopePageTemplate(name, body, content_type=typ)
        elif typ.startswith('image/'):
            ob = Image(name, '', body, content_type=typ)
        else:
            ob = File(name, '', body, content_type=typ)

        return ob

    @security.public
    def PUT(self, REQUEST, RESPONSE):
        """Create a new non-collection resource.
        """
        self.dav__init(REQUEST, RESPONSE)

        name = self.__name__
        parent = self.__parent__

        ifhdr = REQUEST.get_header('If', '')
        if IWriteLock.providedBy(parent) and parent.wl_isLocked():
            if ifhdr:
                parent.dav__simpleifhandler(REQUEST, RESPONSE, col=1)
            else:
                # There was no If header at all, and our parent is locked,
                # so we fail here
                raise Locked
        elif ifhdr:
            # There was an If header, but the parent is not locked
            raise PreconditionFailed

        # SDS: Only use BODY if the file size is smaller than
        # LARGE_FILE_THRESHOLD, otherwise read
        # LARGE_FILE_THRESHOLD bytes from the file
        # which should be enough to trigger
        # content_type detection, and possibly enough for CMF's
        # content_type_registry too.
        #
        # Note that body here is really just used for detecting the
        # content type and figuring out the correct factory. The correct
        # file content will be uploaded on ob.PUT(REQUEST, RESPONSE) after
        # the object has been created.
        #
        # A problem I could see is content_type_registry predicates
        # that do depend on the whole file being passed here as an
        # argument. There's none by default that does this though. If
        # they really do want to look at the file, they should use
        # REQUEST['BODYFILE'] directly and try as much as possible not
        # to read the whole file into memory.

        if int(REQUEST.get('CONTENT_LENGTH') or 0) > LARGE_FILE_THRESHOLD:
            file = REQUEST['BODYFILE']
            body = file.read(LARGE_FILE_THRESHOLD)
            if not isinstance(body, bytes):
                body = body.encode('UTF-8')
            file.seek(0)
        else:
            body = REQUEST.get('BODY', b'')

        typ = REQUEST.get_header('content-type', None)
        if typ is None:
            typ, enc = guess_content_type(name, body)

        factory = getattr(parent, 'PUT_factory', self._default_PUT_factory)
        ob = factory(name, typ, body)
        if ob is None:
            ob = self._default_PUT_factory(name, typ, body)

        # We call _verifyObjectPaste with verify_src=0, to see if the
        # user can create this type of object (and we don't need to
        # check the clipboard.
        try:
            parent._verifyObjectPaste(ob.__of__(parent), 0)
        except CopyError:
            sMsg = 'Unable to create object of class %s in %s: %s' % \
                   (ob.__class__, repr(parent), sys.exc_info()[1],)
            raise Unauthorized(sMsg)

        # A PUT factory may have changed the object's ID
        name = ob.getId() or name

        # Delegate actual PUT handling to the new object,
        # SDS: But just *after* it has been stored.
        self.__parent__._setObject(name, ob)
        ob = self.__parent__._getOb(name)
        ob.PUT(REQUEST, RESPONSE)

        RESPONSE.setStatus(201)
        RESPONSE.setBody('')
        return RESPONSE

    @security.protected(add_folders)
    def MKCOL(self, REQUEST, RESPONSE):
        """Create a new collection resource."""
        self.dav__init(REQUEST, RESPONSE)
        if REQUEST.get('BODY', ''):
            raise UnsupportedMediaType('Unknown request body.')

        name = self.__name__
        parent = self.__parent__

        if hasattr(aq_base(parent), name):
            raise MethodNotAllowed('The name %s is in use.' % name)
        if not isDavCollection(parent):
            raise Forbidden('Cannot create collection at this location.')

        ifhdr = REQUEST.get_header('If', '')
        if IWriteLock.providedBy(parent) and parent.wl_isLocked():
            if ifhdr:
                parent.dav__simpleifhandler(REQUEST, RESPONSE, col=1)
            else:
                raise Locked
        elif ifhdr:
            # There was an If header, but the parent is not locked
            raise PreconditionFailed

        # Add hook for webdav MKCOL (Collector #2254) (needed for CMF)
        mkcol_handler = getattr(parent, 'MKCOL_handler',
                                parent.manage_addFolder)
        mkcol_handler(name)

        RESPONSE.setStatus(201)
        RESPONSE.setBody('')
        return RESPONSE

    @security.protected(webdav_lock_items)
    def LOCK(self, REQUEST, RESPONSE):
        """ LOCK on a Null Resource makes a LockNullResource instance """
        self.dav__init(REQUEST, RESPONSE)
        security = getSecurityManager()
        creator = security.getUser()
        body = REQUEST.get('BODY', '')
        ifhdr = REQUEST.get_header('If', '')
        depth = REQUEST.get_header('Depth', 'infinity')

        name = self.__name__
        parent = self.__parent__

        if isinstance(parent, NullResource):
            # Can happen if someone specified a bad path to
            # the object. Missing path elements may be created
            # as NullResources. Give up in this case.
            raise BadRequest('Parent %s does not exist' % parent.__name__)

        if IWriteLock.providedBy(parent) and parent.wl_isLocked():
            if ifhdr:
                parent.dav__simpleifhandler(REQUEST, RESPONSE, col=1)
            else:
                raise Locked
            if not body:
                # No body means refresh lock, which makes no sense on
                # a null resource. But if the parent is locked it can be
                # interpreted as an indirect refresh lock for the parent.
                return parent.LOCK(REQUEST, RESPONSE)
        elif ifhdr:
            # There was an If header, but the parent is not locked.
            raise PreconditionFailed

        # The logic involved in locking a null resource is simpler than
        # a regular resource, since we know we're not already locked,
        # and the lock isn't being refreshed.
        if not body:
            raise BadRequest('No body was in the request')

        locknull = LockNullResource(name)
        parent._setObject(name, locknull)
        locknull = parent._getOb(name)

        cmd = Lock(REQUEST)
        token, result = cmd.apply(locknull, creator, depth=depth)
        if result:
            # Return the multistatus result (there were multiple errors)
            # This *shouldn't* happen for locking a NullResource, but it's
            # inexpensive to handle and is good coverage for any future
            # changes in davcmds.Lock
            RESPONSE.setStatus(207)
            RESPONSE.setHeader('Content-Type', 'text/xml; charset="utf-8"')
            RESPONSE.setBody(result)
        else:
            # The command was succesful
            lock = locknull.wl_getLock(token)
            RESPONSE.setStatus(201)
            RESPONSE.setHeader('Content-Type', 'text/xml; charset="utf-8"')
            RESPONSE.setHeader('Lock-Token', 'opaquelocktoken:' + token)
            RESPONSE.setBody(lock.asXML())


InitializeClass(NullResource)


class LockNullResource(NullResource, Item_w__name__):
    """ A Lock-Null Resource is created when a LOCK command is succesfully
    executed on a NullResource, essentially locking the Name.  A PUT or
    MKCOL deletes the LockNull resource from its container and replaces it
    with the target object.  An UNLOCK deletes it. """

    __locknull_resource__ = 1
    meta_type = 'WebDAV LockNull Resource'

    security = ClassSecurityInfo()

    manage_options = ({'label': 'Info', 'action': 'manage_main'},)

    security.declareProtected(view, 'manage')  # NOQA: D001
    security.declareProtected(view, 'manage_main')  # NOQA: D001
    manage = manage_main = DTMLFile('dtml/locknullmain', globals())
    security.declareProtected(view, 'manage_workspace')  # NOQA: D001
    manage_workspace = manage
    manage_main._setName('manage_main')  # explicit

    def __no_valid_write_locks__(self):
        # A special hook (for better or worse) called when there are no
        # valid locks left.  We have to delete ourselves from our container
        # now.
        parent = aq_parent(self)
        if parent:
            parent._delObject(self.id)

    def __init__(self, name):
        self.id = self.__name__ = name
        self.title = "LockNull Resource '%s'" % name

    @security.public
    def title_or_id(self):
        return 'Foo'

    @security.protected(webdav_access)
    def PROPFIND(self, REQUEST, RESPONSE):
        """Retrieve properties defined on the resource."""
        return Resource.PROPFIND(self, REQUEST, RESPONSE)

    @security.protected(webdav_lock_items)
    def LOCK(self, REQUEST, RESPONSE):
        """ A Lock command on a LockNull resource should only be a
        refresh request (one without a body) """
        self.dav__init(REQUEST, RESPONSE)
        body = REQUEST.get('BODY', '')
        ifhdr = REQUEST.get_header('If', '')

        if body:
            # If there's a body, then this is a full lock request
            # which conflicts with the fact that we're already locked
            RESPONSE.setStatus(423)
        else:
            # There's no body, so this is likely to be a refresh request
            if not ifhdr:
                raise PreconditionFailed
            taglist = IfParser(ifhdr)
            found = 0
            for tag in taglist:
                for listitem in tag.list:
                    token = tokenFinder(listitem)
                    if token and self.wl_hasLock(token):
                        lock = self.wl_getLock(token)
                        timeout = REQUEST.get_header('Timeout', 'infinite')
                        lock.setTimeout(timeout)  # Automatically refreshes
                        found = 1

                        RESPONSE.setStatus(200)
                        RESPONSE.setHeader('Content-Type',
                                           'text/xml; charset="utf-8"')
                        RESPONSE.setBody(lock.asXML())
                if found:
                    break
            if not found:
                RESPONSE.setStatus(412)  # Precondition failed

        return RESPONSE

    @security.protected(webdav_unlock_items)
    def UNLOCK(self, REQUEST, RESPONSE):
        """ Unlocking a Null Resource removes it from its parent """
        self.dav__init(REQUEST, RESPONSE)
        token = REQUEST.get_header('Lock-Token', '')
        url = REQUEST['URL']
        if token:
            token = tokenFinder(token)
        else:
            raise BadRequest('No lock token was submitted in the request')

        cmd = Unlock()
        result = cmd.apply(self, token, url)

        parent = aq_parent(self)
        parent._delObject(self.id)

        if result:
            RESPONSE.setStatus(207)
            RESPONSE.setHeader('Content-Type', 'text/xml; charset="utf-8"')
            RESPONSE.setBody(result)
        else:
            RESPONSE.setStatus(204)
        return RESPONSE

    @security.public
    def PUT(self, REQUEST, RESPONSE):
        """ Create a new non-collection resource, deleting the LockNull
        object from the container before putting the new object in. """

        self.dav__init(REQUEST, RESPONSE)
        name = self.__name__
        parent = self.aq_parent
        parenturl = parent.absolute_url()
        ifhdr = REQUEST.get_header('If', '')

        # Since a Lock null resource is always locked by definition, all
        # operations done by an owner of the lock that affect the resource
        # MUST have the If header in the request
        if not ifhdr:
            raise PreconditionFailed('No If-header')

        # First we need to see if the parent of the locknull is locked, and
        # if the user owns that lock (checked by handling the information in
        # the If header).
        if IWriteLock.providedBy(parent) and parent.wl_isLocked():
            itrue = parent.dav__simpleifhandler(REQUEST, RESPONSE, 'PUT',
                                                col=1, url=parenturl,
                                                refresh=1)
            if not itrue:
                raise PreconditionFailed(
                    'Condition failed against resources parent')

        # Now we need to check the If header against our own lock state
        itrue = self.dav__simpleifhandler(REQUEST, RESPONSE, 'PUT', refresh=1)
        if not itrue:
            raise PreconditionFailed(
                'Condition failed against locknull resource')

        # All of the If header tests succeeded, now we need to remove ourselves
        # from our parent.  We need to transfer lock state to the new object.
        locks = self.wl_lockItems()
        parent._delObject(name)

        # Now we need to go through the regular operations of PUT
        body = REQUEST.get('BODY', '')
        typ = REQUEST.get_header('content-type', None)
        if typ is None:
            typ, enc = guess_content_type(name, body)

        factory = getattr(parent, 'PUT_factory', self._default_PUT_factory)
        ob = factory(name, typ, body) or self._default_PUT_factory(name,
                                                                   typ, body)

        # Verify that the user can create this type of object
        try:
            parent._verifyObjectPaste(ob.__of__(parent), 0)
        except Unauthorized:
            raise
        except Exception:
            raise Forbidden(sys.exc_info()[1])

        # Put the locks on the new object
        if not IWriteLock.providedBy(ob):
            raise MethodNotAllowed(
                'The target object type cannot be locked')
        for token, lock in locks:
            ob.wl_setLock(token, lock)

        # Delegate actual PUT handling to the new object.
        ob.PUT(REQUEST, RESPONSE)
        parent._setObject(name, ob)

        RESPONSE.setStatus(201)
        RESPONSE.setBody('')
        return RESPONSE

    @security.protected(add_folders)
    def MKCOL(self, REQUEST, RESPONSE):
        """ Create a new Collection (folder) resource.  Since this is being
        done on a LockNull resource, this also involves removing the LockNull
        object and transferring its locks to the newly created Folder """
        self.dav__init(REQUEST, RESPONSE)
        if REQUEST.get('BODY', ''):
            raise UnsupportedMediaType('Unknown request body.')

        name = self.__name__
        parent = self.aq_parent
        parenturl = parent.absolute_url()
        ifhdr = REQUEST.get_header('If', '')

        if not ifhdr:
            raise PreconditionFailed('No If-header')

        # If the parent object is locked, that information should be in the
        # if-header if the user owns a lock on the parent
        if IWriteLock.providedBy(parent) and parent.wl_isLocked():
            itrue = parent.dav__simpleifhandler(
                REQUEST, RESPONSE, 'MKCOL', col=1, url=parenturl, refresh=1)
            if not itrue:
                raise PreconditionFailed(
                    'Condition failed against resources parent')
        # Now we need to check the If header against our own lock state
        itrue = self.dav__simpleifhandler(
            REQUEST, RESPONSE, 'MKCOL', refresh=1)
        if not itrue:
            raise PreconditionFailed(
                'Condition failed against locknull resource')

        # All of the If header tests succeeded, now we need to remove ourselves
        # from our parent.  We need to transfer lock state to the new folder.
        locks = self.wl_lockItems()
        parent._delObject(name)

        parent.manage_addFolder(name)
        folder = parent._getOb(name)
        for token, lock in locks:
            folder.wl_setLock(token, lock)

        RESPONSE.setStatus(201)
        RESPONSE.setBody('')
        return RESPONSE


InitializeClass(LockNullResource)
