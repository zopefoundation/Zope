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
"""
Response class for the FTP Server.
"""

from ZServer.HTTPResponse import ZServerHTTPResponse
from PubCore.ZEvent import Wakeup
from cStringIO import StringIO
import marshal


class FTPResponse(ZServerHTTPResponse):
    """
    Response to an FTP command
    """

    def __str__(self):
        ZServerHTTPResponse.__str__(self)
        return

    def outputBody(self):
        pass

    def setCookie(self, name, value, **kw):
        self.cookies[name]=value

    def appendCookie(self, name, value):
        self.cookies[name]=self.cookies[name] + value

    def expireCookie(self, name, **kw):
        if self.cookies.has_key(name):            
            del self.cookies[name]

    def _cookie_list(self):
        return []

    def _marshalledBody(self):
        return marshal.loads(self.body)

 
class CallbackPipe:
    """
    Sends response object to a callback. Doesn't write anything.
    The callback takes place in Medusa's thread, not the request thread.
    """
    def __init__(self, callback, args):
        self._callback=callback
        self._args=args
        self._producers=[]
        
    def close(self):
        pass
        
    def write(self, text, l=None):
        if text:
            self._producers.append(text)
    
    def finish(self, response):
        self._response=response
        Wakeup(self.apply) # move callback to medusas thread
        
    def apply(self):
        result=apply(self._callback, self._args+(self._response,))
       
        # break cycles
        self._callback=None
        self._response=None
        self._args=None
        
        return result    

def make_response(channel, callback, *args):
    # XXX should this be the FTPResponse constructor instead?
    r=FTPResponse(stdout=CallbackPipe(callback, args), stderr=StringIO())
    r.setHeader('content-type','text/plain')
    r.cookies=channel.cookies
    return r
