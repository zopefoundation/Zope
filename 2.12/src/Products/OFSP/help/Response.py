##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
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

    def setCookie(name, value, quoted=True, **kw):
        '''

        Set an HTTP cookie on the browser

        The response will include an HTTP header that sets a cookie on
        cookie-enabled browsers with a key "name" and value
        "value". This overwrites any previously set value for the
        cookie in the Response object.

        By default, the cookie value will be enclosed in double quotes.
        To suppress the double quotes you can pass the "quoted" argument
        with a False value such as False or 0.

        Permission -- Always available

        '''

    def appendHeader(name, value, delimiter=","):
        '''

        Append a value to a header.

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
