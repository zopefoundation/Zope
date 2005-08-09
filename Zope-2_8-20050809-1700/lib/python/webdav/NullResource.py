##############################################################################
#
# Copyright (c) 2001 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################

"""WebDAV support - null resource objects."""

__version__='$Revision: 1.43 $'[11:-2]

import sys, Globals, davcmds
import Acquisition, OFS.content_types
from common import aq_base, tokenFinder, IfParser
from AccessControl import getSecurityManager
from Resource import Resource
from Globals import Persistent, DTMLFile
from WriteLockInterface import WriteLockInterface
import OFS.SimpleItem
from zExceptions import Unauthorized, NotFound, Forbidden, BadRequest
from zExceptions import MethodNotAllowed
from common import isDavCollection
from common import Locked, Conflict, PreconditionFailed, UnsupportedMediaType
from OFS.CopySupport import CopyError

class NullResource(Persistent, Acquisition.Implicit, Resource):
    """Null resources are used to handle HTTP method calls on
    objects which do not yet exist in the url namespace."""

    __implements__ = (WriteLockInterface,)
    __null_resource__=1

    __ac_permissions__=(
        ('View',                             ('HEAD',)),
        ('Add Folders',                      ('MKCOL',)),
        ('WebDAV Lock items',                ('LOCK',)),
    )

    def __init__(self, parent, name, request=None):
        self.__name__=name
        self.__parent__=parent

    def __bobo_traverse__(self, REQUEST, name=None):
        # We must handle traversal so that we can recognize situations
        # where a 409 Conflict must be returned instead of the normal
        # 404 Not Found, per [WebDAV 8.3.1].
        try:    return getattr(self, name)
        except: pass
        method=REQUEST.get('REQUEST_METHOD', 'GET')
        if method in ('PUT', 'MKCOL', 'LOCK'):
            raise Conflict, 'Collection ancestors must already exist.'
        raise NotFound, 'The requested resource was not found.'

    def HEAD(self, REQUEST, RESPONSE):
        """Retrieve resource information without a response message body."""
        self.dav__init(REQUEST, RESPONSE)
        raise NotFound, 'The requested resource does not exist.'

    # Most methods return 404 (Not Found) for null resources.
    DELETE=TRACE=PROPFIND=PROPPATCH=COPY=MOVE=HEAD
    index_html = HEAD

    def _default_PUT_factory( self, name, typ, body ):
        # Return DTMLDoc/PageTemplate/Image/File, based on sniffing.
        if name and name.endswith('.pt'):
            from Products.PageTemplates.ZopePageTemplate import ZopePageTemplate
            ob = ZopePageTemplate(name, body, content_type=typ)
        elif typ in ('text/html', 'text/xml', 'text/plain'):
            from OFS.DTMLDocument import DTMLDocument
            ob = DTMLDocument( '', __name__=name )
        elif typ[:6]=='image/':
            from OFS.Image import Image
            ob=Image(name, '', body, content_type=typ)
        else:
            from OFS.Image import File
            ob=File(name, '', body, content_type=typ)
        return ob

    PUT__roles__ = ('Anonymous',)
    def PUT(self, REQUEST, RESPONSE):
        """Create a new non-collection resource.
        """
        from ZServer import LARGE_FILE_THRESHOLD

        self.dav__init(REQUEST, RESPONSE)

        name = self.__name__
        parent = self.__parent__

        ifhdr = REQUEST.get_header('If', '')
        if WriteLockInterface.isImplementedBy(parent) and parent.wl_isLocked():
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
        # LARGE_FILE_THRESHOLD, otherwise read LARGE_FILE_THRESHOLD
        # bytes from the file which should be enough to trigger
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
            file.seek(0)
        else:
            body = REQUEST.get('BODY', '')

        typ=REQUEST.get_header('content-type', None)
        if typ is None:
            typ, enc=OFS.content_types.guess_content_type(name, body)

        factory = getattr(parent, 'PUT_factory', self._default_PUT_factory )
        ob = factory(name, typ, body)
        if ob is None:
            ob = self._default_PUT_factory(name, typ, body)

        # We call _verifyObjectPaste with verify_src=0, to see if the
        # user can create this type of object (and we don't need to
        # check the clipboard.
        try:
            parent._verifyObjectPaste(ob.__of__(parent), 0)
        except CopyError:
            raise Unauthorized, sys.exc_info()[1]

        # Delegate actual PUT handling to the new object,
        # SDS: But just *after* it has been stored.
        self.__parent__._setObject(name, ob)
        ob = self.__parent__._getOb(name)
        ob.PUT(REQUEST, RESPONSE)

        RESPONSE.setStatus(201)
        RESPONSE.setBody('')
        return RESPONSE

    def MKCOL(self, REQUEST, RESPONSE):
        """Create a new collection resource."""
        self.dav__init(REQUEST, RESPONSE)
        if REQUEST.get('BODY', ''):
            raise UnsupportedMediaType, 'Unknown request body.'

        name=self.__name__
        parent = self.__parent__

        if hasattr(aq_base(parent), name):
            raise MethodNotAllowed, 'The name %s is in use.' % name
        if not isDavCollection(parent):
            raise Forbidden, 'Cannot create collection at this location.'

        ifhdr = REQUEST.get_header('If', '')
        if WriteLockInterface.isImplementedBy(parent) and parent.wl_isLocked():
            if ifhdr:
                parent.dav__simpleifhandler(REQUEST, RESPONSE, col=1)
            else:
                raise Locked
        elif ifhdr:
            # There was an If header, but the parent is not locked
            raise PreconditionFailed

        # Add hook for webdav/FTP MKCOL (Collector #2254) (needed for CMF)
#       parent.manage_addFolder(name)
        mkcol_handler = getattr(parent,'MKCOL_handler' ,parent.manage_addFolder)
        mkcol_handler(name)

        RESPONSE.setStatus(201)
        RESPONSE.setBody('')
        return RESPONSE

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

        if WriteLockInterface.isImplementedBy(parent) and parent.wl_isLocked():
            if ifhdr:
                parent.dav__simpleifhandler(REQUEST, RESPONSE, col=1)
            else:
                raise Locked
        elif ifhdr:
            # There was an If header, but the parent is not locked.
            raise PreconditionFailed

        # The logic involved in locking a null resource is simpler than
        # a regular resource, since we know we're not already locked,
        # and the lock isn't being refreshed.
        if not body:
            raise BadRequest, 'No body was in the request'

        locknull = LockNullResource(name)
        parent._setObject(name, locknull)
        locknull = parent._getOb(name)

        cmd = davcmds.Lock(REQUEST)
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
            RESPONSE.setStatus(200)                         
            RESPONSE.setHeader('Content-Type', 'text/xml; charset="utf-8"')
            RESPONSE.setHeader('Lock-Token', 'opaquelocktoken:' + token)
            RESPONSE.setBody(lock.asXML())


Globals.default__class_init__(NullResource)


class LockNullResource(NullResource, OFS.SimpleItem.Item_w__name__):
    """ A Lock-Null Resource is created when a LOCK command is succesfully
    executed on a NullResource, essentially locking the Name.  A PUT or
    MKCOL deletes the LockNull resource from its container and replaces it
    with the target object.  An UNLOCK deletes it. """

    __implements__ = (WriteLockInterface,)
    __locknull_resource__ = 1
    meta_type = 'WebDAV LockNull Resource'

    __ac_permissions__ = (
        ('WebDAV Unlock items',              ('UNLOCK',)),
        ('View',                             ('manage_main',
                                              'manage_workspace', 'manage')),
        ('Add Folders',                      ('MKCOL',)),
        ('WebDAV Lock items',                ('LOCK',)),
        )

    manage_options = ({'label': 'Info', 'action': 'manage_main'},)

    manage = manage_main = DTMLFile('dtml/locknullmain', globals())
    manage_workspace = manage
    manage_main._setName('manage_main')  # explicit

    def __no_valid_write_locks__(self):
        # A special hook (for better or worse) called when there are no
        # valid locks left.  We have to delete ourselves from our container
        # now.
        parent = Acquisition.aq_parent(self)
        if parent: parent._delObject(self.id)

    def __init__(self, name):
        self.id = self.__name__ = name
        self.title = "LockNull Resource '%s'" % name

    title_or_id__roles__=None
    def title_or_id(self):
        return 'Foo'

    def PROPFIND(self, REQUEST, RESPONSE):
        """Retrieve properties defined on the resource."""
        return Resource.PROPFIND(self, REQUEST, RESPONSE)

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
                        lock.setTimeout(timeout) # Automatically refreshes
                        found = 1

                        RESPONSE.setStatus(200)
                        RESPONSE.setHeader('Content-Type',
                                           'text/xml; charset="utf-8"')
                        RESPONSE.setBody(lock.asXML())
                if found: break
            if not found:
                RESPONSE.setStatus(412) # Precondition failed

        return RESPONSE


    def UNLOCK(self, REQUEST, RESPONSE):
        """ Unlocking a Null Resource removes it from its parent """
        self.dav__init(REQUEST, RESPONSE)
        security = getSecurityManager()
        user = security.getUser()
        token = REQUEST.get_header('Lock-Token', '')
        url = REQUEST['URL']
        if token:
            token = tokenFinder(token)
        else:
            raise BadRequest, 'No lock token was submitted in the request'

        cmd = davcmds.Unlock()
        result = cmd.apply(self, token, url)

        parent = Acquisition.aq_parent(self)
        parent._delObject(self.id)

        if result:
            RESPONSE.setStatus(207)
            RESPONSE.setHeader('Content-Type', 'text/xml; charset="utf-8"')
            RESPONSE.setBody(result)
        else:
            RESPONSE.setStatus(204)
        return RESPONSE

    PUT__roles__ = ('Anonymous',)
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
            raise PreconditionFailed, 'No If-header'

        # First we need to see if the parent of the locknull is locked, and
        # if the user owns that lock (checked by handling the information in
        # the If header).
        if WriteLockInterface.isImplementedBy(parent) and parent.wl_isLocked():
            itrue = parent.dav__simpleifhandler(REQUEST, RESPONSE, 'PUT',
                                                col=1, url=parenturl,
                                                refresh=1)
            if not itrue:
                raise PreconditionFailed, (
                'Condition failed against resources parent')

        # Now we need to check the If header against our own lock state
        itrue = self.dav__simpleifhandler(REQUEST, RESPONSE, 'PUT', refresh=1)
        if not itrue:
            raise PreconditionFailed, (
            'Condition failed against locknull resource')

        # All of the If header tests succeeded, now we need to remove ourselves
        # from our parent.  We need to transfer lock state to the new object.
        locks = self.wl_lockItems()
        parent._delObject(name)

        # Now we need to go through the regular operations of PUT
        body = REQUEST.get('BODY', '')
        typ = REQUEST.get_header('content-type', None)
        if typ is None:
            typ, enc = OFS.content_types.guess_content_type(name, body)

        factory = getattr(parent, 'PUT_factory', self._default_PUT_factory)
        ob = (factory(name, typ, body) or
              self._default_PUT_factory(name, typ, body))

        # Verify that the user can create this type of object
        try:
            parent._verifyObjectPaste(ob.__of__(parent), 0)
        except Unauthorized:
            raise
        except:
            raise Forbidden, sys.exc_info()[1]

        # Put the locks on the new object
        if not WriteLockInterface.isImplementedBy(ob):
            raise MethodNotAllowed, (
                'The target object type cannot be locked')
        for token, lock in locks:
            ob.wl_setLock(token, lock)

        # Delegate actual PUT handling to the new object.
        ob.PUT(REQUEST, RESPONSE)
        parent._setObject(name, ob)

        RESPONSE.setStatus(201)
        RESPONSE.setBody('')
        return RESPONSE

    def MKCOL(self, REQUEST, RESPONSE):
        """ Create a new Collection (folder) resource.  Since this is being
        done on a LockNull resource, this also involves removing the LockNull
        object and transferring its locks to the newly created Folder """
        self.dav__init(REQUEST, RESPONSE)
        if REQUEST.get('BODY', ''):
            raise UnsupportedMediaType, 'Unknown request body.'

        name = self.__name__
        parent = self.aq_parent
        parenturl = parent.absolute_url()
        ifhdr = REQUEST.get_header('If', '')

        if not ifhdr:
            raise PreconditionFailed, 'No If-header'

        # If the parent object is locked, that information should be in the
        # if-header if the user owns a lock on the parent
        if WriteLockInterface.isImplementedBy(parent) and parent.wl_isLocked():
            itrue = parent.dav__simpleifhandler(REQUEST, RESPONSE, 'MKCOL',
                                                col=1, url=parenturl,
                                                refresh=1)
            if not itrue:
                raise PreconditionFailed, (
                'Condition failed against resources parent')
        # Now we need to check the If header against our own lock state
        itrue = self.dav__simpleifhandler(REQUEST,RESPONSE,'MKCOL',refresh=1)
        if not itrue:
            raise PreconditionFailed, (
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


Globals.default__class_init__(LockNullResource)
