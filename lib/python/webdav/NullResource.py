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

__version__='$Revision: 1.17 $'[11:-2]

import sys, os, string, mimetypes, Globals
import Acquisition, OFS.content_types
from common import absattr, aq_base, urlfix
from AccessControl.Permission import Permission
from Resource import Resource
from Globals import Persistent


class NullResource(Persistent, Acquisition.Implicit, Resource):
    """Null resources are used to handle HTTP method calls on
    objects which do not yet exist in the url namespace."""

    __null_resource__=1

    __ac_permissions__=(
        ('View',                             ('HEAD',)),
        ('Access contents information',      ('PROPFIND',)),
        ('Manage properties',                ('PROPPATCH',)),
        ('Add Documents, Images, and Files', ('PUT',)),
        ('Add Folders',                      ('MKCOL',)),
        ('Delete objects',                   ('DELETE',)),
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
        if method in ('PUT', 'MKCOL'):
            raise 'Conflict', 'Collection ancestors must already exist.'
        raise 'Not Found', 'The requested resource was not found.'

    def HEAD(self, REQUEST, RESPONSE):
        """Retrieve resource information without a response message body."""
        self.dav__init(REQUEST, RESPONSE)
        raise 'Not Found', 'The requested resource does not exist.'

    # Most methods return 404 (Not Found) for null resources.
    DELETE=OPTIONS=TRACE=PROPFIND=PROPPATCH=COPY=MOVE=HEAD

    def PUT(self, REQUEST, RESPONSE):
        """Create a new non-collection resource."""
        self.dav__init(REQUEST, RESPONSE)
        type=REQUEST.get_header('content-type', None)
        body=REQUEST.get('BODY', '')
        name=self.__name__
        if type is None:
            type, enc=mimetypes.guess_type(name)
        if type is None:
            if OFS.content_types.find_binary(body) >= 0:
                type='application/octet-stream'
            else: type=OFS.content_types.text_type(body)
        type=string.lower(type)
        from OFS.Image import Image, File
        if type in ('text/html', 'text/xml', 'text/plain'):
            self.__parent__.manage_addDTMLDocument(name, '', body)
        elif type[:6]=='image/':
            ob=Image(name, '', body, content_type=type)
            self.__parent__._setObject(name, ob)
        else:
            ob=File(name, '', body, content_type=type)
            self.__parent__._setObject(name, ob)
        RESPONSE.setStatus(201)
        RESPONSE.setBody('')
        return RESPONSE

    def MKCOL(self, REQUEST, RESPONSE):
        """Create a new collection resource."""
        self.dav__init(REQUEST, RESPONSE)
        if REQUEST.get('BODY', ''):
            raise 'Unsupported Media Type', 'Unknown request body.'
        parent=self.__parent__
        name=self.__name__
        if hasattr(aq_base(parent), name):
            raise 'Method Not Allowed', 'The name %s is in use.' % name
        if not hasattr(parent, '__dav_collection__'):
            raise 'Forbidden', 'Cannot create collection at this location.'
        parent.manage_addFolder(name)
        RESPONSE.setStatus(201)
        RESPONSE.setBody('')
        return RESPONSE

    def LOCK(self, REQUEST, RESPONSE):
        """Create a lock-null resource."""
        self.dav__init(REQUEST, RESPONSE)
        raise 'Method Not Allowed', 'Method not supported for this resource.'
    
    def UNLOCK(self):
        """Remove a lock-null resource."""
        self.dav__init(REQUEST, RESPONSE)
        raise 'Method Not Allowed', 'Method not supported for this resource.'


Globals.default__class_init__(NullResource)
