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
"""XML-RPC support module

Written by Eric Kidd at UserLand software, with much help from Jim Fulton
at DC. This code hooks Zope up to Fredrik Lundh's Python XML-RPC library.

See http://www.xmlrpc.com/ and http://linux.userland.com/ for more
information about XML-RPC and Zope.
"""

import sys
from string import replace
from HTTPResponse import HTTPResponse
import xmlrpclib

def parse_input(data):
    """Parse input data and return a method path and argument tuple

    The data is a string.
    """
    # 
    # For example, with the input:
    #     
    #   <?xml version="1.0"?>
    #   <methodCall>
    #      <methodName>examples.getStateName</methodName>
    #      <params>
    #         <param>
    #            <value><i4>41</i4></value>
    #            </param>
    #         </params>
    #      </methodCall>
    # 
    # the function should return:
    # 
    #     ('examples.getStateName', (41,))
    params, method = xmlrpclib.loads(data)
    # Translate '.' to '/' in meth to represent object traversal.
    method = replace(method, '.', '/')
    return method, params

# See below
#
# def response(anHTTPResponse):
#     """Return a valid ZPublisher response object
# 
#     Use data already gathered by the existing response.
#     The new response will replace the existing response.
#     """
#     # As a first cut, lets just clone the response and
#     # put all of the logic in our refined response class below.
#     r=Response()
#     r.__dict__.update(anHTTPResponse.__dict__)
#     return r
    
    

########################################################################
# Possible implementation helpers:

class Response:
    """Customized Response that handles XML-RPC-specific details.

    We override setBody to marhsall Python objects into XML-RPC. We
    also override exception to convert errors to XML-RPC faults.

    If these methods stop getting called, make sure that ZPublisher is
    using the xmlrpc.Response object created above and not the original
    HTTPResponse object from which it was cloned.

    It's probably possible to improve the 'exception' method quite a bit.
    The current implementation, however, should suffice for now.
    """

    # Because we can't predict what kind of thing we're customizing,
    # we have to use delegation, rather than inheritence to do the
    # customization.

    def __init__(self, real): self.__dict__['_real']=real

    def __getattr__(self, name): return getattr(self._real, name)
    def __setattr__(self, name, v): return setattr(self._real, name, v)
    def __delattr__(self, name): return delattr(self._real, name)
    
    def setBody(self, body, title='', is_error=0, bogus_str_search=None):
        if isinstance(body, xmlrpclib.Fault):
            # Convert Fault object to XML-RPC response.
            body=xmlrpclib.dumps(body, methodresponse=1)
        else:
            # Marshall our body as an XML-RPC response. Strings will be sent
            # strings, integers as integers, etc. We do *not* convert
            # everything to a string first.
            if body is None:
                body=xmlrpclib.False # Argh, XML-RPC doesn't handle null
            try:
                body = xmlrpclib.dumps((body,), methodresponse=1)
            except:
                self.exception()
                return
        # Set our body to the XML-RPC message, and fix our MIME type.
        self._real.setBody(body)
        self._real.setHeader('content-type', 'text/xml')
        return self

    def exception(self, fatal=0, info=None,
                  absuri_match=None, tag_search=None):
        # Fetch our exception info. t is type, v is value and tb is the
        # traceback object.
        if type(info) is type(()) and len(info)==3: t,v,tb = info
        else: t,v,tb = sys.exc_info()

        # Abort running transaction, if any:
        try: get_transaction().abort()
        except: pass

        # Create an appropriate Fault object. Unfortunately, we throw away
        # most of the debugging information. More useful error reporting is
        # left as an exercise for the reader.
        Fault=xmlrpclib.Fault
        f=None
        try:
            if isinstance(v, Fault):
                f=v
            elif isinstance(v, Exception):
                f=Fault(-1, "Unexpected Zope exception: " + str(v))
            else:
                f=Fault(-2, "Unexpected Zope error value: " + str(v))
        except:
            f=Fault(-3, "Unknown Zope fault type")

        # Do the damage.
        self.setBody(f)
        self._real.setStatus(200)

        return tb

response=Response
