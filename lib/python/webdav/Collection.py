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

"""WebDAV support - collection objects."""

__version__='$Revision: 1.4 $'[11:-2]

import sys, os, string
from Resource import Resource
from common import urlfix


class Collection(Resource):
    """The Collection class provides basic WebDAV support for
    collection objects. It provides default implementations 
    for all supported WebDAV HTTP methods. The behaviors of some
    WebDAV HTTP methods for collections are slightly different
    than those for non-collection resources."""

    __dav_collection__=1

    def redirect_check(self, req, rsp):
        # By the spec, we are not supposed to accept /foo for a
        # collection, we have to redirect to /foo/.
        if req['PATH_INFO'][-1]=='/':
            return
        raise 'Moved Permanently', req['URL1']+'/'

    def HEAD(self, REQUEST, RESPONSE):
        """Retrieve resource information without a response body."""
        self.init_headers(RESPONSE)
        self.redirect_check(REQUEST, RESPONSE)
        RESPONSE.setStatus(200)
        return RESPONSE

    def PUT(self, REQUEST, RESPONSE):
        """The PUT method has no inherent meaning for collection
        resources, though collections are not specifically forbidden
        to handle PUT requests. The default response to a PUT request
        for collections is 405 (Method Not Allowed)."""
        self.init_headers(RESPONSE)
        self.redirect_check(REQUEST, RESPONSE)
        raise 'Method Not Allowed', 'Method not supported for this resource.'

    def DELETE(self, REQUEST, RESPONSE):
        """Delete a collection resource. For collection resources, DELETE
        may return either 200 (OK) or 204 (No Content) to indicate total
        success, or may return 207 (Multistatus) to indicate partial
        success. Note that in Zope a DELETE never returns 207."""
        self.init_headers(RESPONSE)
        self.redirect_check(REQUEST, RESPONSE)
#        self.dav__validate('manage_delObjects', REQUEST)
        url=urlfix(REQUEST['URL'], 'DELETE')
        name=filter(None, string.split(url, '/'))[-1]
        # TODO: add lock checking here
        self.aq_parent._delObject(name)
        RESPONSE.setStatus(204)
        return RESPONSE

