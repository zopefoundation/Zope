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

"""WebDAV support - resource objects."""

__version__='$Revision: 1.15 $'[11:-2]

import sys, os, string, mimetypes, xmlcmds
from common import absattr, aq_base, urlfix, rfc1123_date


class Resource:
    """The Resource mixin class provides basic WebDAV support for
    non-collection objects. It provides default implementations
    for most supported WebDAV HTTP methods, however certain methods
    such as PUT should be overridden to ensure correct behavior in
    the context of the object type."""

    __dav_resource__=1

    __http_methods__=('GET', 'HEAD', 'POST', 'PUT', 'DELETE', 'OPTIONS',
                      'TRACE', 'PROPFIND', 'PROPPATCH', 'MKCOL', 'COPY',
                      'MOVE',
                      )

    def dav__init(self, request, response):
        # Init expected HTTP 1.1 / WebDAV headers which are not
        # currently set by the response object automagically.
        response.setHeader('Connection', 'close', 1)
        response.setHeader('Date', rfc1123_date(), 1)
        response.setHeader('DAV', '1', 1)

    def dav__validate(self, object, methodname, REQUEST):
        msg='<strong>You are not authorized to access this resource.</strong>'
        method=None
        if hasattr(object, methodname):
            method=getattr(object, methodname)
        else:
            try:    method=object.aq_acquire(methodname)
            except: method=None
        if (method is not None) and hasattr(method, '__roles__'):
            roles=method.__roles__
            user=REQUEST.get('AUTHENTICATED_USER', None)
            __traceback_info__=methodname, str(roles), user
            if (not hasattr(user, 'hasRole') or not user.hasRole(None, roles)):
                raise 'Unauthorized', msg
            return 1
        raise 'Unauthorized', msg


    # WebDAV class 1 support

    def HEAD(self, REQUEST, RESPONSE):
        """Retrieve resource information without a response body."""
        self.dav__init(REQUEST, RESPONSE)
        if hasattr(self, 'content_type'):
            RESPONSE.setHeader('Content-Type', absattr(self.content_type))
        if hasattr(self, 'getSize'):
            RESPONSE.setHeader('Content-Length', absattr(self.getSize))
        RESPONSE.setStatus(200)
        return RESPONSE

    def PUT(self, REQUEST, RESPONSE):
        """Replace the GET response entity of an existing resource.        
        Because this is often object-dependent, objects which handle
        PUT should override the default PUT implementation with an
        object-specific implementation. By default, PUT requests
        fail with a 405 (Method Not Allowed)."""
        self.dav__init(REQUEST, RESPONSE)
        raise 'Method Not Allowed', 'Method not supported for this resource.'

    OPTIONS__roles__=None
    def OPTIONS(self, REQUEST, RESPONSE):
        """Retrieve communication options."""
        self.dav__init(REQUEST, RESPONSE)
        RESPONSE.setHeader('Allow', string.join(self.__http_methods__,', '))
        RESPONSE.setHeader('Content-Length', 0)
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
        raise 'Method Not Allowed', 'Method not supported for this resource.'

    def DELETE(self, REQUEST, RESPONSE):
        """Delete a resource. For non-collection resources, DELETE may
        return either 200 or 204 (No Content) to indicate success."""
        self.dav__init(REQUEST, RESPONSE)
        url=urlfix(REQUEST['URL'], 'DELETE')
        name=filter(None, string.split(url, '/'))[-1]
        # TODO: add lock checking here
        self.aq_parent._delObject(name)
        RESPONSE.setStatus(204)
        return RESPONSE

    def PROPFIND(self, REQUEST, RESPONSE):
        """Retrieve properties defined on the resource."""
        self.dav__init(REQUEST, RESPONSE)
        cmd=xmlcmds.PropFind(REQUEST)
        result=cmd.apply(self)
        RESPONSE.setStatus(207)
        RESPONSE.setHeader('Content-Type', 'text/xml; charset="utf-8"')
        RESPONSE.setBody(result)
        return RESPONSE

    def PROPPATCH(self, REQUEST, RESPONSE):
        """Set and/or remove properties defined on the resource."""
        self.dav__init(REQUEST, RESPONSE)
        if not hasattr(self, '__propsets__'):
            raise 'Method Not Allowed', (
                  'Method not supported for this resource.')
        # TODO: add lock checking here
        cmd=xmlcmds.PropPatch(REQUEST)
        result=cmd.apply(self)
        RESPONSE.setStatus(207)
        RESPONSE.setHeader('Content-Type', 'text/xml; charset="utf-8"')
        RESPONSE.setBody(result)
        return RESPONSE

    def MKCOL(self, REQUEST, RESPONSE):
        """Create a new collection resource. If called on an existing 
        resource, MKCOL must fail with 405 (Method Not Allowed)."""
        self.dav__init(REQUEST, RESPONSE)
        raise 'Method Not Allowed', 'The resource already exists.'

    def COPY(self, REQUEST, RESPONSE):
        """Create a duplicate of the source resource whose state
        and behavior match that of the source resource as closely
        as possible. Though we may later try to make a copy appear
        seamless across namespaces (e.g. from Zope to Apache), COPY 
        is currently only supported within the Zope namespace."""
        self.dav__init(REQUEST, RESPONSE)
        if not hasattr(aq_base(self), 'cb_isCopyable') or \
           not self.cb_isCopyable():
            raise 'Method Not Allowed', 'This object may not be copied.'
        depth=REQUEST.get_header('Depth', 'infinity')
        if not depth in ('0', 'infinity'):
            raise 'Bad Request', 'Invalid Depth header.'
        dest=REQUEST.get_header('Destination', '')
        while dest and dest[-1]=='/':
            dest=dest[:-1]
        if not dest:
            raise 'Bad Request', 'Invalid Destination header.'
        oflag=string.upper(REQUEST.get_header('Overwrite', 'F'))
        if not oflag in ('T', 'F'):
            raise 'Bad Request', 'Invalid Overwrite header.'
        path, name=os.path.split(dest)
        try: parent=REQUEST.resolve_url(path)
        except ValueError:
            raise 'Conflict', 'Attempt to copy to an unknown namespace.'
        except 'Not Found':
            raise 'Conflict', 'Object ancestors must already exist.'
        except: raise sys.exc_type, sys.exc_value
        if hasattr(parent, '__dav_null__'):
            raise 'Conflict', 'Object ancestors must already exist.'
        existing=hasattr(aq_base(parent), name)
        if existing and oflag=='F':
            raise 'Precondition Failed', 'Destination resource exists.'
        try: parent._checkId(name, allow_dup=1)
        except: raise 'Forbidden', sys.exc_value
        try: parent._verifyObjectPaste(self, REQUEST)
        except: raise 'Forbidden', sys.exc_value
        try: self._notifyOfCopyTo(parent, op=0)
        except: raise 'Forbidden', sys.exc_value
        ob=self._getCopy(parent)
        ob._setId(name)
        if depth=='0' and hasattr(ob, '__dav_collection__'):
            for id in ob.objectIds():
                ob._delObject(id)
        if existing:
            object=getattr(parent, name)
            obj.dav__validate(object, 'DELETE', request)
            parent._delObject(name)
        parent._setObject(name, ob)
        ob=ob.__of__(parent)
        ob._postCopy(parent, op=0)
        RESPONSE.setStatus(existing and 204 or 201)
        if not existing:
            RESPONSE.setHeader('Location', dest)
        RESPONSE.setBody('')
        return RESPONSE

    def MOVE(self, REQUEST, RESPONSE):
        """Move a resource to a new location. Though we may later try to
        make a move appear seamless across namespaces (e.g. from Zope
        to Apache), MOVE is currently only supported within the Zope
        namespace."""
        self.dav__init(REQUEST, RESPONSE)
        self.dav__validate(self, 'DELETE', REQUEST)
        if not hasattr(aq_base(self), 'cb_isMoveable') or \
           not self.cb_isMoveable():
            raise 'Method Not Allowed', 'This object may not be moved.'
        dest=REQUEST.get_header('Destination', '')
        while dest and dest[-1]=='/':
            dest=dest[:-1]
        if not dest:
            raise 'Bad Request', 'No destination given'
        flag=REQUEST.get_header('Overwrite', 'F')
        flag=string.upper(flag)
        body=REQUEST.get('BODY', '')
        path, name=os.path.split(dest)
        try: parent=REQUEST.resolve_url(path)
        except ValueError:
            raise 'Conflict', 'Attempt to move to an unknown namespace.'
        except 'Not Found':
            raise 'Conflict', 'The resource %s must exist.' % path
        except: raise sys.exc_type, sys.exc_value
        if hasattr(parent, '__dav_null__'):
            raise 'Conflict', 'The resource %s must exist.' % path
        existing=hasattr(aq_base(parent), name)
        if existing and flag=='F':
            raise 'Precondition Failed', 'Resource %s exists.' % dest
        try: parent._checkId(name, allow_dup=1)
        except: raise 'Forbidden', sys.exc_value
        try: parent._verifyObjectPaste(self, REQUEST)
        except: raise 'Forbidden', sys.exc_value
        try: self._notifyOfCopyTo(parent, op=1)
        except: raise 'Forbidden', sys.exc_value        
        ob=aq_base(self._getCopy(parent))
        self.aq_parent._delObject(absattr(self.id))
        ob._setId(name)
        if existing:
            object=getattr(parent, name)
            self.dav__validate(object, 'DELETE', REQUEST)
            parent._delObject(name)            
        parent._setObject(name, ob)
        ob=ob.__of__(parent)
        ob._postCopy(parent, op=1)
        RESPONSE.setStatus(existing and 204 or 201)
        if not existing:
            RESPONSE.setHeader('Location', dest)
        RESPONSE.setBody('')
        return RESPONSE


    # WebDAV Class 2 support

    def LOCK(self, REQUEST, RESPONSE):
        """A write lock MUST prevent a principal without the lock from
        successfully executing a PUT, POST, PROPPATCH, LOCK, UNLOCK, MOVE,
        DELETE, or MKCOL on the locked resource.  All other current methods,
        GET in particular, function independently of the lock.
        """
        self.dav__init(REQUEST, RESPONSE)
        raise 'Method Not Allowed', 'Method not supported for this resource.'
    
    def UNLOCK(self):
        """Remove an existing lock on a resource."""
        self.dav__init(REQUEST, RESPONSE)
        raise 'Method Not Allowed', 'Method not supported for this resource.'
