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

"""WebDAV support - collection objects."""

__version__='$Revision: 1.20 $'[11:-2]

import sys, os, string, Globals, davcmds, Lockable,re
from common import urlfix, rfc1123_date
from Resource import Resource
from AccessControl import getSecurityManager
from urllib import unquote
from WriteLockInterface import WriteLockInterface


class Collection(Resource):
    """The Collection class provides basic WebDAV support for
    collection objects. It provides default implementations 
    for all supported WebDAV HTTP methods. The behaviors of some
    WebDAV HTTP methods for collections are slightly different
    than those for non-collection resources."""

    __dav_collection__=1

    def dav__init(self, request, response):
        # We are allowed to accept a url w/o a trailing slash
        # for a collection, but are supposed to provide a
        # hint to the client that it should be using one.
        # [WebDAV, 5.2]
        pathinfo=request.get('PATH_INFO','')
        if pathinfo and pathinfo[-1] != '/':
            location='%s/' % request['URL1']
            response.setHeader('Content-Location', location)
        response.setHeader('Connection', 'close', 1)
        response.setHeader('Date', rfc1123_date(), 1)
        response.setHeader('MS-Author-Via', 'DAV')

    def HEAD(self, REQUEST, RESPONSE):
        """Retrieve resource information without a response body."""
        self.dav__init(REQUEST, RESPONSE)
        # Note that we are willing to acquire the default document
        # here because what we really care about is whether doing
        # a GET on this collection / would yield a 200 response.
        if hasattr(self, 'index_html'):
            if hasattr(self.index_html, 'HEAD'):
                return self.index_html.HEAD(REQUEST, RESPONSE)
            raise 'Method Not Allowed', (
                  'Method not supported for this resource.'
                  )
        raise 'Not Found', 'The requested resource does not exist.'

    def PUT(self, REQUEST, RESPONSE):
        """The PUT method has no inherent meaning for collection
        resources, though collections are not specifically forbidden
        to handle PUT requests. The default response to a PUT request
        for collections is 405 (Method Not Allowed)."""
        self.dav__init(REQUEST, RESPONSE)
        raise 'Method Not Allowed', 'Method not supported for collections.'

    def DELETE(self, REQUEST, RESPONSE):
        """Delete a collection resource. For collection resources, DELETE
        may return either 200 (OK) or 204 (No Content) to indicate total
        success, or may return 207 (Multistatus) to indicate partial
        success. Note that in Zope a DELETE currently never returns 207."""


        self.dav__init(REQUEST, RESPONSE)
        ifhdr = REQUEST.get_header('If', '')
        url = urlfix(REQUEST['URL'], 'DELETE')
        name = unquote(filter(None, string.split(url, '/'))[-1])
        parent = self.aq_parent
        user = getSecurityManager().getUser()
        token = None

#        if re.match("/Control_Panel",REQUEST['PATH_INFO']):
#            RESPONSE.setStatus(403)
#            RESPONSE.setHeader('Content-Type', 'text/xml; charset="utf-8"')
#            return RESPONSE

        # Level 1 of lock checking (is the collection or its parent locked?)
        if Lockable.wl_isLocked(self):
            if ifhdr:
                self.dav__simpleifhandler(REQUEST, RESPONSE, 'DELETE', col=1)
            else:
                raise 'Locked'
        elif Lockable.wl_isLocked(parent):
            if ifhdr:
                parent.dav__simpleifhandler(REQUEST, RESPONSE, 'DELETE', col=1)
            else:
                raise 'Precondition Failed'
        # Second level of lock\conflict checking (are any descendants locked,
        # or is the user not permitted to delete?).  This results in a
        # multistatus response
        if ifhdr:
            tokens = self.wl_lockTokens()
            for tok in tokens:
                # We already know that the simple if handler succeeded,
                # we just want to get the right token out of the header now
                if string.find(ifhdr, tok) > -1:
                    token = tok
        cmd = davcmds.DeleteCollection()
        result = cmd.apply(self, token, user, REQUEST['URL'])

        if result:
            # There were conflicts, so we need to report them
            RESPONSE.setStatus(207)
            RESPONSE.setHeader('Content-Type', 'text/xml; charset="utf-8"')
            RESPONSE.setBody(result)
        else:
            # There were no conflicts, so we can go ahead and delete
            # ajung: additional check if we really could delete the collection
            # (Collector #2196) 
            if parent.manage_delObjects([name],REQUEST=None)  is None:
                RESPONSE.setStatus(204)
            else:
                RESPONSE.setStatus(403)
            
        return RESPONSE


Globals.default__class_init__(Collection)
