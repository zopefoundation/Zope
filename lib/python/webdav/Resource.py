##############################################################################
#
# Zope Public License (ZPL) Version 0.9.4
# ---------------------------------------
# 
# Copyright (c) Digital Creations.  All rights reserved.
# 
# Redistribution and use in source and binary forms, with or
# without modification, are permitted provided that the following
# conditions are met:
# 
# 1. Redistributions in source code must retain the above
#    copyright notice, this list of conditions, and the following
#    disclaimer.
# 
# 2. Redistributions in binary form must reproduce the above
#    copyright notice, this list of conditions, and the following
#    disclaimer in the documentation and/or other materials
#    provided with the distribution.
# 
# 3. Any use, including use of the Zope software to operate a
#    website, must either comply with the terms described below
#    under "Attribution" or alternatively secure a separate
#    license from Digital Creations.
# 
# 4. All advertising materials, documentation, or technical papers
#    mentioning features derived from or use of this software must
#    display the following acknowledgement:
# 
#      "This product includes software developed by Digital
#      Creations for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
# 5. Names associated with Zope or Digital Creations must not be
#    used to endorse or promote products derived from this
#    software without prior written permission from Digital
#    Creations.
# 
# 6. Redistributions of any form whatsoever must retain the
#    following acknowledgment:
# 
#      "This product includes software developed by Digital
#      Creations for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
# 7. Modifications are encouraged but must be packaged separately
#    as patches to official Zope releases.  Distributions that do
#    not clearly separate the patches from the original work must
#    be clearly labeled as unofficial distributions.
# 
# Disclaimer
# 
#   THIS SOFTWARE IS PROVIDED BY DIGITAL CREATIONS ``AS IS'' AND
#   ANY EXPRESSED OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
#   LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND
#   FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.  IN NO EVENT
#   SHALL DIGITAL CREATIONS OR ITS CONTRIBUTORS BE LIABLE FOR ANY
#   DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
#   CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
#   PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
#   DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#   ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
#   LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING
#   IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF
#   THE POSSIBILITY OF SUCH DAMAGE.
# 
# Attribution
# 
#   Individuals or organizations using this software as a web site
#   must provide attribution by placing the accompanying "button"
#   and a link to the accompanying "credits page" on the website's
#   main entry point.  In cases where this placement of
#   attribution is not feasible, a separate arrangment must be
#   concluded with Digital Creations.  Those using the software
#   for purposes other than web sites must provide a corresponding
#   attribution in locations that include a copyright using a
#   manner best suited to the application environment.
# 
# This software consists of contributions made by Digital
# Creations and many individuals on behalf of Digital Creations.
# Specific attributions are listed in the accompanying credits
# file.
# 
##############################################################################

"""WebDAV support - resource objects."""

__version__='$Revision: 1.4 $'[11:-2]

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

    def init_headers(self, r):
        # Init expected HTTP 1.1 / WebDAV headers which are not
        # currently set by the response object automagically.
        r.setHeader('Connection', 'close')
        r.setHeader('Date', rfc1123_date())
        r.setHeader('DAV', '1')

    dav__locks=()
    
    def dav__is_locked(self):
        # Return true if this object is locked via a
        # session or dav lock.
        if hasattr(self, 'locked_in_session') and self.locked_in_session():
            return 1
        return 0

    def dav__get_locks(self):
        # Return the current locks on the object.
        if hasattr(self, 'locked_in_session') and self.locked_in_session():
            lock=Lock('xxxx', 'xxxx')
            return self.dav__locks + (lock,)
        
    
    # WebDAV class 1 support

    def HEAD(self, REQUEST, RESPONSE):
        """Retrieve resource information without a response body."""
        self.init_headers(RESPONSE)
        raise 'Method Not Allowed', 'Method not supported for this resource.'

    def PUT(self, REQUEST, RESPONSE):
        """Replace the GET response entity of an existing resource.        
        Because this is often object-dependent, objects which handle
        PUT should override the default PUT implementation with an
        object-specific implementation. By default, PUT requests
        fail with a 405 (Method Not Allowed)."""
        self.init_headers(RESPONSE)
        raise 'Method Not Allowed', 'Method not supported for this resource.'
    
    def OPTIONS(self, REQUEST, RESPONSE):
        """Retrieve communication options."""
        self.init_headers(RESPONSE)
        RESPONSE.setHeader('Allow', string.join(self.__http_methods__, ', '))
        RESPONSE.setHeader('Content-Length', 0)
        RESPONSE.setStatus(200)
        return RESPONSE

    def TRACE(self, REQUEST, RESPONSE):
        """Return the HTTP message received back to the client as the
        entity-body of a 200 (OK) response. This will often usually
        be intercepted by the web server in use. If not, the TRACE
        request will fail with a 405 (Method Not Allowed), since it
        is not often possible to reproduce the HTTP request verbatim
        from within the Zope environment."""
        self.init_headers(RESPONSE)
        raise 'Method Not Allowed', 'Method not supported for this resource.'

    def DELETE(self, REQUEST, RESPONSE):
        """Delete a resource. For non-collection resources, DELETE may
        return either 200 or 204 (No Content) to indicate success."""
        self.init_headers(RESPONSE)
        url=urlfix(REQUEST['URL'], 'DELETE')
        name=filter(None, string.split(url, '/'))[-1]
        # TODO: add lock checking here
        self.aq_parent._delObject(name)
        RESPONSE.setStatus(204)
        return RESPONSE

    def PROPFIND(self, REQUEST, RESPONSE):
        """Retrieve properties defined on the resource."""
        self.init_headers(RESPONSE)
        try: cmd=xmlcmds.PropFind(REQUEST)
        except: raise 'Bad Request', 'Invalid xml request.'
        result=cmd.apply(self)
        RESPONSE.setStatus(207)
        RESPONSE.setHeader('Content-Type', 'text/xml; charset="utf-8"')
        RESPONSE.setBody(result)
        return RESPONSE

    def PROPPATCH(self, REQUEST, RESPONSE):
        """Set and/or remove properties defined on the resource."""
        self.init_headers(RESPONSE)
        if not hasattr(self, '__propsets__'):
            raise 'Method Not Allowed', (
                  'Method not supported for this resource.')
        # TODO: add lock checking here
        try: cmd=xmlcmds.PropPatch(REQUEST)
        except: raise 'Bad Request', 'Invalid xml request.'
        result=cmd.apply(self)
        RESPONSE.setStatus(207)
        RESPONSE.setHeader('Content-Type', 'text/xml; charset="utf-8"')
        RESPONSE.setBody(result)
        return RESPONSE

    def MKCOL(self, REQUEST, RESPONSE):
        """Create a new collection resource. If called on an existing 
        resource, MKCOL must fail with 405 (Method Not Allowed)."""
        self.init_headers(RESPONSE)
        raise 'Method Not Allowed', 'Method not supported for this resource.'

    def COPY(self, REQUEST, RESPONSE):
        """Create a duplicate of the source resource whose state
        and behavior match that of the source resource as closely
        as possible. Though we may later try to make a copy appear
        seamless across namespaces (e.g. from Zope to Apache), COPY 
        is currently only supported within the Zope namespace."""
        self.init_headers(RESPONSE)
        if not hasattr(aq_base(self), 'cb_isCopyable') or \
           not self.cb_isCopyable():
            raise 'Method Not Allowed', 'This object may not be copied.'
        depth=REQUEST.get_header('Depth', 'infinity')
        dest=REQUEST.get_header('Destination', '')
        if not dest: raise 'Bad Request', 'No destination given'
        flag=REQUEST.get_header('Overwrite', 'F')
        flag=string.upper(flag)
        body=REQUEST.get('BODY', '')

        path, name=os.path.split(dest)
        try: parent=REQUEST.resolve_url(path)
        except ValueError:
            raise 'Conflict', 'Attempt to copy to an unknown namespace.'
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
        try: self._notifyOfCopyTo(parent, op=0)
        except: raise 'Forbidden', sys.exc_value
        ob=self._getCopy(parent)
        ob._setId(name)
        parent._setObject(name, ob)
        ob=ob.__of__(parent)
        ob._postCopy(parent, op=0)

        RESPONSE.setStatus(existing and 204 or 201)
        if not existing: RESPONSE.setHeader('Location', dest)
        RESPONSE.setBody('')
        return RESPONSE
        

    def MOVE(self, REQUEST, RESPONSE):
        """Move a resource to a new location. Though we may later try to
        make a move appear seamless across namespaces (e.g. from Zope
        to Apache), MOVE is currently only supported within the Zope
        namespace."""
        self.init_headers(RESPONSE)
        if not hasattr(aq_base(self), 'cb_isMoveable') or \
           not self.cb_isMoveable():
            raise 'Method Not Allowed', 'This object may not be moved.'
        dest=REQUEST.get_header('Destination', '')
        if not dest: raise 'Bad Request', 'No destination given'
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
        parent._setObject(name, ob)
        ob=ob.__of__(parent)
        ob._postCopy(parent, op=1)
        RESPONSE.setStatus(existing and 204 or 201)
        if not existing: RESPONSE.setHeader('Location', dest)
        RESPONSE.setBody('')
        return RESPONSE


    # Class 2 support

    def LOCK(self, REQUEST, RESPONSE):
        """A write lock MUST prevent a principal without the lock from
        successfully executing a PUT, POST, PROPPATCH, LOCK, UNLOCK, MOVE,
        DELETE, or MKCOL on the locked resource.  All other current methods,
        GET in particular, function independently of the lock.
        """
        self.init_headers(RESPONSE)
        raise 'Method Not Allowed', 'Method not supported for this resource.'
    
    def UNLOCK(self):
        """Remove an existing lock on a resource."""
        self.init_headers(RESPONSE)
        raise 'Method Not Allowed', 'Method not supported for this resource.'



class Lock:
    """A WebDAV lock object"""
    def __init__(self, token, owner, scope='exclusive', type='write',
                 depth='infinity', timeout='Infinite'):
        self.token=token
        self.owner=owner        
        self.scope=scope
        self.type=type
        self.depth=depth
        self.timeout=timeout

    def dav__activelock(self):
        txt='<d:activelock>\n' \
            '<d:locktype><d:%(type)s/></d:locktype>\n' \
            '<d:lockscope><d:%(scope)s/></d:lockscope>\n' \
            '<d:depth>%(depth)s</d:depth>\n' \
            '<d:owner>%(owner)s</d:owner>\n' \
            '<d:timeout>%(timeout)s</d:timeout>\n' \
            '<d:locktoken>\n' \
            '<d:href>opaquelocktoken:%(token)s</d:href>\n' \
            '</d:locktoken>\n' \
            '</d:activelock>\n' % self.__dict__
