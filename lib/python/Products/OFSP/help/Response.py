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


class Response:

    """

    The Response object represents the response to a Zope request.

    """

    def setStatus(status, reason=None):
        '''
        
        Sets the HTTP status code of the response; the argument may
        either be an integer or one of the following strings:

            OK,
            Created,
            Accepted,
            NoContent,
            MovedPermanently,
            MovedTemporarily,
            NotModified,
            BadRequest,
            Unauthorized,
            Forbidden,
            NotFound,
            InternalError,
            NotImplemented,
            BadGateway,
            ServiceUnavailable
        
        that will be converted to the correct integer value.

        Permission -- Always available

        '''

    def setHeader(name, value):
        '''
        
        Sets an HTTP return header "name" with value "value", clearing
        the previous value set for the header, if one exists. If the
        literal flag is true, the case of the header name is
        preserved, otherwise word-capitalization will be performed on
        the header name on output.

        Permission -- Always available

        '''

    def addHeader(name, value):
        '''
        
        Set a new HTTP return header with the given value, while
        retaining any previously set headers with the same name.

        Permission -- Always available
        
        '''

    def setBase(base):
        """

        Set the base URL for the returned document.

        Permission -- Always available
        
        """

    def appendCookie(name, value):
        '''
        
        Returns an HTTP header that sets a cookie on cookie-enabled
        browsers with a key "name" and value "value". If a value for the
        cookie has previously been set in the response object, the new
        value is appended to the old one separated by a colon.

        Permission -- Always available
        
        '''


    def expireCookie(name, **kw):
        '''
        
        Cause an HTTP cookie to be removed from the browser
        
        The response will include an HTTP header that will remove the cookie
        corresponding to "name" on the client, if one exists. This is
        accomplished by sending a new cookie with an expiration date
        that has already passed. Note that some clients require a path
        to be specified - this path must exactly match the path given
        when creating the cookie. The path can be specified as a keyword
        argument.

        Permission -- Always available
        
        '''

    def setCookie(name,value,**kw):
        '''
        
        Set an HTTP cookie on the browser

        The response will include an HTTP header that sets a cookie on
        cookie-enabled browsers with a key "name" and value
        "value". This overwrites any previously set value for the
        cookie in the Response object.

        Permission -- Always available
        
        '''

    def appendHeader(name, value, delimiter=","):
        '''
        
        Append a value to a cookie
        
        Sets an HTTP return header "name" with value "value",
        appending it following a comma if there was a previous value
        set for the header.

        Permission -- Always available
        
        '''

    def redirect(location, lock=0):
        """

        Cause a redirection without raising an error. If the "lock"
        keyword argument is passed with a true value, then the HTTP
        redirect response code will not be changed even if an error
        occurs later in request processing (after redirect() has
        been called).

        Permission -- Always available
        
        """

    def write(data):
        """
        Return data as a stream

        HTML data may be returned using a stream-oriented interface.
        This allows the browser to display partial results while
        computation of a response to proceed.

        The published object should first set any output headers or
        cookies on the response object.

        Note that published objects must not generate any errors
        after beginning stream-oriented output. 

        Permission -- Always available

        """
        
