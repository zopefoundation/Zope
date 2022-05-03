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
"""CGI Response Output formatter"""

from zExceptions import BadRequest
from zExceptions import Forbidden
from zExceptions import NotFound
from zExceptions import Unauthorized


class BaseResponse:
    """Base Response Class
    """
    body = b''
    debug_mode = None
    _auth = None
    _error_format = 'text/plain'

    # Allow (reluctantly) access to unprotected attributes
    __allow_access_to_unprotected_subobjects__ = 1

    def __init__(self, stdout, stderr,
                 body=b'', headers=None, status=None, cookies=None):
        self.stdout = stdout
        self.stderr = stderr
        self.body = body
        if headers is None:
            headers = {}
        self.headers = headers
        self.status = status
        if cookies is None:
            cookies = {}
        self.cookies = cookies

    def setStatus(self, status, reason=None):
        self.status = status

    def setHeader(self, name, value):
        self.headers[name] = value

    __setitem__ = setHeader

    def outputBody(self):
        """Output the response body."""
        self.stdout.write(bytes(self))

    def setBody(self, body):
        if isinstance(body, str):
            raise ValueError('Body must be binary.')
        self.body = body

    def getStatus(self):
        """Returns the current HTTP status code as an integer."""
        return self.status

    def setCookie(self, name, value, **kw):
        """Set an HTTP cookie on the browser.

        The response will include an HTTP header that sets a cookie on
        cookie-enabled browsers with a key "name" and value
        "value". This overwrites any previously set value for the
        cookie in the Response object.
        """
        cookies = self.cookies
        if name in cookies:
            cookie = cookies[name]
        else:
            cookie = cookies[name] = {}
        for k, v in kw.items():
            cookie[k] = v
        cookie['value'] = value

    def appendBody(self, body):
        self.setBody(self.getBody() + body)

    def getHeader(self, name):
        """Get a header value.

        Returns the value associated with a HTTP return header, or
        "None" if no such header has been set in the response
        yet.
        """
        return self.headers.get(name, None)

    def __getitem__(self, name):
        """Get the value of an output header."""
        return self.headers[name]

    def getBody(self):
        """Returns bytes representing the currently set body."""
        return self.body

    def __bytes__(self):
        return bytes(self.body)

    def __repr__(self):
        return f'{self.__class__.__name__}({self.body!r})'

    def flush(self):
        pass

    def write(self, data):
        """Return data as a stream.

        HTML data may be returned using a stream-oriented interface.
        This allows the browser to display partial results while
        computation of a response to proceed.

        The published object should first set any output headers or
        cookies on the response object.

        Note that published objects must not generate any errors
        after beginning stream-oriented output.
        """
        if isinstance(data, str):
            raise ValueError('Data must be binary.')
        self.body = self.body + data

    def exception(self, fatal=0, info=None):
        """Handle an exception.

        The fatal argument indicates whether the error is fatal.

        The info argument, if given should be a tuple with an
        error type, value, and traceback.
        """

    def notFoundError(self, v=''):
        """Generate an error indicating that an object was not found."""
        raise NotFound(v)

    def debugError(self, v=''):
        """Raise an error with debugging info and in debugging mode."""
        raise NotFound("Debugging notice: %s" % v)

    def badRequestError(self, v=''):
        """Raise an error indicating something wrong with the request."""
        raise BadRequest(v)

    def forbiddenError(self, v=''):
        """Raise an error indicating that the request cannot be done."""
        raise Forbidden(v)

    def unauthorized(self):
        """Raise an error indicating that the user was not authorized.

        Make sure to generate an appropriate challenge, as appropriate.
        """
        raise Unauthorized()
