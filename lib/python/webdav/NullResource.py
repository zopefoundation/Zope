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

"""WebDAV support - null resource objects."""

__version__='$Revision: 1.1 $'[11:-2]

import sys, os, string, mimetypes
import Acquisition, OFS.content_types
from Resource import Resource, aq_base


class NullResource(Acquisition.Implicit, Resource):
    """Null resources are used to handle HTTP method calls on
    objects which do not yet exist in the url namespace."""
    _isNullResource=1
    
    def __init__(self, parent, id):
        self.id=id
        self.__parent__=parent
        self.__roles__=None # fix this!!

    def HEAD(self, REQUEST, RESPONSE):
        """Retrieve resource information without a response message body."""
        self.init_headers(RESPONSE)
        raise 'Not Found', 'The requested resource does not exist.'

    # Most methods return 404 (Not Found) for null resources.
    DELETE=OPTIONS=TRACE=PROPFIND=PROPPATCH=COPY=MOVE=HEAD

    def PUT(self, REQUEST, RESPONSE):
        """Create a new non-collection resource."""
        self.init_headers(RESPONSE)
        type=REQUEST.get_header('content-type', None)
        body=REQUEST.get('BODY', '')
        if type is None:
            type, enc=mimetypes.guess_type(self.id)
        if type is None:
            if OFS.content_types.find_binary(body) >= 0:
                content_type='application/octet-stream'
            else: type=OFS.content_types.text_type(body)
        type=string.lower(type)
        from OFS.Image import Image, File
        if type in ('text/html', 'text/xml', 'text/plain'):
            self.__parent__.manage_addDTMLDocument(self.id, '', body)
        elif type[:6]=='image/':
            ob=Image(self.id, '', body, content_type=type)
            self.__parent__._setObject(self.id, ob)
        else:
            ob=File(self.id, '', body, content_type=type)
            self.__parent__._setObject(self.id, ob)
        RESPONSE.setStatus(201)
        RESPONSE.setBody('')
        return RESPONSE

    def MKCOL(self, REQUEST, RESPONSE):
        """Create a new collection resource."""
        self.init_headers(RESPONSE)
        if REQUEST.get('BODY', ''):
            raise 'Unsupported Media Type', 'Unknown request body.'
        parent=self.__parent__
        if hasattr(aq_base(parent), self.id):
            raise 'Method Not Allowed', 'The name %s is in use.' % self.id
        if (not hasattr(parent.aq_base, 'isAnObjectManager')) or \
           (not parent.isAnObjectManager):
            raise 'Forbidden', 'Unable to create collection resource.'
        # This should probably do self.__class__(id, ...), except Folder
        # doesn't currently have a constructor.
        parent.manage_addFolder(self.id)
        RESPONSE.setStatus(201)
        RESPONSE.setBody('')
        return RESPONSE

    def LOCK(self, REQUEST, RESPONSE):
        """Create a lock-null resource."""
        self.init_headers(RESPONSE)
        raise 'Method Not Allowed', 'Method not supported for this resource.'
    
    def UNLOCK(self):
        """Remove a lock-null resource."""
        self.init_headers(RESPONSE)
        
        raise 'Method Not Allowed', 'Method not supported for this resource.'
