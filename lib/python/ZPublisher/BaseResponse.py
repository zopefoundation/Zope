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
'''CGI Response Output formatter

$Id: BaseResponse.py,v 1.8 2001/04/26 14:40:07 andreas Exp $'''
__version__='$Revision: 1.8 $'[11:-2]

import string, types, sys
from string import find, rfind, lower, upper, strip, split, join, translate
from types import StringType, InstanceType

class BaseResponse:
    """Base Response Class

    What should be here?
    """
    debug_mode=None
    _auth=None
    _error_format='text/plain'
    
    # Allow (reluctantly) access to unprotected attributes
    __allow_access_to_unprotected_subobjects__=1
        
    def __init__(self, stdout, stderr,
                 body='', headers=None, status=None, cookies=None):
        self.stdout=stdout
        self.stderr=stderr
        self.body=body
        if headers is None: headers={}
        self.headers=headers
        self.status=status
        if cookies is None: cookies={}
        self.cookies=cookies
    
    def setStatus(self, status, reason=None):
        self.status=status

    def setHeader(self, name, value):
        self.headers[name]=value

    __setitem__=setHeader

    def outputBody(self):
        """Output the response body"""
        self.stdout.write(str(self))

    def setBody(self, body):
        self.body=body

    def getStatus(self):
        'Returns the current HTTP status code as an integer. '
        return self.status

    def setCookie(self,name,value,**kw):
        '''\
        Set an HTTP cookie on the browser

        The response will include an HTTP header that sets a cookie on
        cookie-enabled browsers with a key "name" and value
        "value". This overwrites any previously set value for the
        cookie in the Response object.
        '''
        cookies=self.cookies
        if cookies.has_key(name):
            cookie=cookies[name]
        else: cookie=cookies[name]={}
        for k, v in kw.items():
            cookie[k]=v
        cookie['value']=value

    def appendBody(self, body):
        self.setBody(self.getBody() + body)

    def getHeader(self, name):
         '''\
         Get a header value
         
         Returns the value associated with a HTTP return header, or
         "None" if no such header has been set in the response
         yet. '''
         return self.headers.get(name, None)

    def __getitem__(self, name):
        'Get the value of an output header'
        return self.headers[name]

    def getBody(self):
        'Returns a string representing the currently set body. '
        return self.body

    def __str__(self):
        return str(self.body)

    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__, `self.body`)

    def flush(self): pass

    def write(self,data):
        """\
        Return data as a stream

        HTML data may be returned using a stream-oriented interface.
        This allows the browser to display partial results while
        computation of a response to proceed.

        The published object should first set any output headers or
        cookies on the response object.

        Note that published objects must not generate any errors
        after beginning stream-oriented output. 

        """
        self.body=self.body+data

    def exception(self, fatal=0, info=None):
        """Handle an exception.

        The fatal argument indicates whether the error is fatal.

        The info argument, if given should be a tuple with an
        error type, value, and traceback.
        """

    def notFoundError(self, v=''):
        """Generate an error indicating that an object was not found.
        """
        raise 'Not Found', v

    def debugError(self, v=''):
        """Raise an error with debigging info and in debugging mode"""
        raise 'Debug Error', v

    def badRequestError(self, v=''):
        """Raise an error indicating something wrong with the request"""
        raise 'Bad Request', v

    def forbiddenError(self, v=''):
        """Raise an error indicating that the request cannot be done"""
        raise 'Forbidden', v

    def unauthorized(self):
        """Raise an eror indicating that the user was not authizated

        Make sure to generate an appropriate challenge, as appropriate.
        """
        raise 'Unauthorized'
