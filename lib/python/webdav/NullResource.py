##############################################################################
# 
# Zope Public License (ZPL) Version 1.0
# -------------------------------------
# 
# Copyright (c) Digital Creations.  All rights reserved.
# 
# This license has been certified as Open Source(tm).
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
# 
# 1. Redistributions in source code must retain the above copyright
#    notice, this list of conditions, and the following disclaimer.
# 
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions, and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
# 
# 3. Digital Creations requests that attribution be given to Zope
#    in any manner possible. Zope includes a "Powered by Zope"
#    button that is installed by default. While it is not a license
#    violation to remove this button, it is requested that the
#    attribution remain. A significant investment has been put
#    into Zope, and this effort will continue if the Zope community
#    continues to grow. This is one way to assure that growth.
# 
# 4. All advertising materials and documentation mentioning
#    features derived from or use of this software must display
#    the following acknowledgement:
# 
#      "This product includes software developed by Digital Creations
#      for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
#    In the event that the product being advertised includes an
#    intact Zope distribution (with copyright and license included)
#    then this clause is waived.
# 
# 5. Names associated with Zope or Digital Creations must not be used to
#    endorse or promote products derived from this software without
#    prior written permission from Digital Creations.
# 
# 6. Modified redistributions of any form whatsoever must retain
#    the following acknowledgment:
# 
#      "This product includes software developed by Digital Creations
#      for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
#    Intact (re-)distributions of any official Zope release do not
#    require an external acknowledgement.
# 
# 7. Modifications are encouraged but must be packaged separately as
#    patches to official Zope releases.  Distributions that do not
#    clearly separate the patches from the original work must be clearly
#    labeled as unofficial distributions.  Modifications which do not
#    carry the name Zope may be packaged in any form, as long as they
#    conform to all of the clauses above.
# 
# 
# Disclaimer
# 
#   THIS SOFTWARE IS PROVIDED BY DIGITAL CREATIONS ``AS IS'' AND ANY
#   EXPRESSED OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
#   IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
#   PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL DIGITAL CREATIONS OR ITS
#   CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
#   SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
#   LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF
#   USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#   ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
#   OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT
#   OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
#   SUCH DAMAGE.
# 
# 
# This software consists of contributions made by Digital Creations and
# many individuals on behalf of Digital Creations.  Specific
# attributions are listed in the accompanying credits file.
# 
##############################################################################

"""WebDAV support - null resource objects."""

__version__='$Revision: 1.25 $'[11:-2]

import sys, os, string, mimetypes, Globals, davcmds
import Acquisition, OFS.content_types
from common import absattr, aq_base, urlfix, tokenFinder, IfParser
from AccessControl.Permission import Permission
from AccessControl import getSecurityManager
from Resource import Resource
from Globals import Persistent, DTMLFile
from WriteLockInterface import WriteLockInterface
import OFS.SimpleItem

class NullResource(Persistent, Acquisition.Implicit, Resource):
    """Null resources are used to handle HTTP method calls on
    objects which do not yet exist in the url namespace."""

    __null_resource__=1

    __ac_permissions__=(
        ('View',                             ('HEAD',)),
        ('Add Documents, Images, and Files', ('PUT',)),
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
            raise 'Conflict', 'Collection ancestors must already exist.'
        raise 'Not Found', 'The requested resource was not found.'

    def HEAD(self, REQUEST, RESPONSE):
        """Retrieve resource information without a response message body."""
        self.dav__init(REQUEST, RESPONSE)
        raise 'Not Found', 'The requested resource does not exist.'

    # Most methods return 404 (Not Found) for null resources.
    DELETE=OPTIONS=TRACE=PROPFIND=PROPPATCH=COPY=MOVE=HEAD

    def _default_PUT_factory( self, name, typ, body ):
        #   Return DTMLDoc/Image/File, based on sniffing.
        from OFS.Image import Image, File
        from OFS.DTMLDocument import DTMLDocument
        if typ in ('text/html', 'text/xml', 'text/plain'):
            ob = DTMLDocument( '', __name__=name )
        elif typ[:6]=='image/':
            ob=Image(name, '', body, content_type=typ)
        else:
            ob=File(name, '', body, content_type=typ)
        return ob

    def PUT(self, REQUEST, RESPONSE):
        """Create a new non-collection resource."""
        self.dav__init(REQUEST, RESPONSE)

        name=self.__name__
        parent=self.__parent__

        ifhdr = REQUEST.get_header('If', '')
        if WriteLockInterface.isImplementedBy(parent) and parent.wl_isLocked():
            if ifhdr:
                parent.dav__simpleifhandler(REQUEST, RESPONSE, col=1)
            else:
                # There was no If header at all, and our parent is locked,
                # so we fail here
                raise 'Locked'
        elif ifhdr:
            # There was an If header, but the parent is not locked
            raise 'Precondition Failed'

        body=REQUEST.get('BODY', '')
        typ=REQUEST.get_header('content-type', None)
        if typ is None:
            typ, enc=OFS.content_types.guess_content_type(name, body)

        factory = getattr(parent, 'PUT_factory', self._default_PUT_factory )
        ob = (factory(name, typ, body) or
              self._default_PUT_factory(name, typ, body)
              )

        # Delegate actual PUT handling to the new object.
        ob.PUT(REQUEST, RESPONSE)
        self.__parent__._setObject(name, ob)

        RESPONSE.setStatus(201)
        RESPONSE.setBody('')
        return RESPONSE

    def MKCOL(self, REQUEST, RESPONSE):
        """Create a new collection resource."""
        self.dav__init(REQUEST, RESPONSE)
        if REQUEST.get('BODY', ''):
            raise 'Unsupported Media Type', 'Unknown request body.'

        name=self.__name__
        parent = self.__parent__

        if hasattr(aq_base(parent), name):
            raise 'Method Not Allowed', 'The name %s is in use.' % name
        if not hasattr(parent, '__dav_collection__'):
            raise 'Forbidden', 'Cannot create collection at this location.'

        ifhdr = REQUEST.get_header('If', '')
        if WriteLockInterface.isImplementedBy(parent) and parent.wl_isLocked():
            if ifhdr:
                parent.dav__simpleifhandler(REQUEST, RESPONSE, col=1)
            else:
                raise 'Locked'
        elif ifhdr:
            # There was an If header, but the parent is not locked
            raise 'Precondition Failed'

        parent.manage_addFolder(name)
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
        depth = REQUEST.get_header('Depth', 'infinite')

        name = self.__name__
        parent = self.__parent__

        if WriteLockInterface.isImplementedBy(parent) and parent.wl_isLocked():
            if ifhdr:
                parent.dav__simpleifhandler(REQUEST, RESPONSE, col=1)
            else:
                raise 'Locked'
        elif ifhdr:
            # There was an If header, but the parent is not locked.
            raise 'Precondition Failed'
        
        # The logic involved in locking a null resource is simpler than
        # a regular resource, since we know we're not already locked,
        # and the lock isn't being refreshed.
        if not body:
            raise 'Bad Request', 'No body was in the request'

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
            RESPONSE.setBody(lock.asXML())


Globals.default__class_init__(NullResource)


class LockNullResource(NullResource, OFS.SimpleItem.Item_w__name__):
    """ A Lock-Null Resource is created when a LOCK command is succesfully
    executed on a NullResource, essentially locking the Name.  A PUT or
    MKCOL deletes the LockNull resource from its container and replaces it
    with the target object.  An UNLOCK deletes it. """

    __locknull_resource__ = 1
    meta_type = 'WebDAV LockNull Resource'

    __ac_permissions__ = (
        ('WebDAV Unlock items',              ('UNLOCK',)),
        ('View',                             ('manage_main',
                                              'manage_workspace', 'manage')),
        ('Add Documents, Images, and Files', ('PUT',)),
        ('Add Folders',                      ('MKCOL',)),
        ('WebDAV Lock items',                ('LOCK',)),
        )

    manage_options = ({'label': 'Info', 'action': 'manage_main'},)

    manage = manage_main = DTMLFile('dtml/locknullmain', globals())
    manage_workspace = manage

    def __no_valid_write_locks__(self):
        # A special hook (for better or worse) called when there are no
        # valid locks left.  We have to delete ourselves from our container
        # now.
        parent = self.aq_parent
        parent._delObject(self.id)
                       
    def __init__(self, name):
        self.id = self.__name__ = name
        self.title = "LockNull Resource '%s'" % name

    title_or_id__roles__=None
    def title_or_id(self):
        return 'Foo'
    
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
            if not ifhdr: raise 'Precondition Failed'
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
        if token: token = tokenFinder(token)
        else: raise 'Bad Request', 'No lock token was submitted in the request'

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
        if not ifhdr: raise 'Precondition Failed', 'No If-header'

        # First we need to see if the parent of the locknull is locked, and
        # if the user owns that lock (checked by handling the information in
        # the If header).
        if WriteLockInterface.isImplementedBy(parent) and parent.wl_isLocked():
            itrue = parent.dav__simpleifhandler(REQUEST, RESPONSE, 'PUT',
                                                col=1, url=parenturl,
                                                refresh=1)
            if not itrue: raise 'Precondition Failed', (
                'Condition failed against resources parent')

        # Now we need to check the If header against our own lock state
        itrue = self.dav__simpleifhandler(REQUEST, RESPONSE, 'PUT', refresh=1)
        if not itrue: raise 'Precondition Failed', (
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

        # Put the locks on the new object
        if not WriteLockInterface.isImplementedBy(ob):
            raise 'Method Not Allowed', (
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
            raise 'Unsupported Media Type', 'Unknown request body.'

        name = self.__name__
        parent = self.aq_parent
        parenturl = parent.absolute_url()
        ifhdr = REQUEST.get_header('If', '')

        if not ifhdr: raise 'Precondition Failed', 'No If-header'

        # If the parent object is locked, that information should be in the
        # if-header if the user owns a lock on the parent
        if WriteLockInterface.isImplementedBy(parent) and parent.wl_isLocked():
            itrue = parent.dav__simpleifhandler(REQUEST, RESPONSE, 'MKCOL',
                                                col=1, url=parenturl,
                                                refresh=1)
            if not itrue: raise 'Precondition Failed', (
                'Condition failed against resources parent')
        # Now we need to check the If header against our own lock state
        itrue = self.dav__simpleifhandler(REQUEST,RESPONSE,'MKCOL',refresh=1)
        if not itrue: raise 'Precondition Failed', (
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
