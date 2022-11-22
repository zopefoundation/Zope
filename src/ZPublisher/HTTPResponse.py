##############################################################################
#
# Copyright (c) 2001-2009 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
""" CGI Response Output formatter
"""
import html
import os
import re
import struct
import sys
import time
import zlib
from email.header import Header
from email.message import _parseparam
from email.utils import encode_rfc2231
from io import BytesIO
from io import IOBase
from urllib.parse import quote
from urllib.parse import urlparse
from urllib.parse import urlunparse

from zExceptions import BadRequest
from zExceptions import HTTPRedirection
from zExceptions import InternalError
from zExceptions import NotFound
from zExceptions import Redirect
from zExceptions import Unauthorized
from zExceptions import status_reasons
from zExceptions.ExceptionFormatter import format_exception
from zope.event import notify
from ZPublisher import pubevents
from ZPublisher.BaseResponse import BaseResponse
from ZPublisher.Iterators import IStreamIterator
from ZPublisher.Iterators import IUnboundStreamIterator

from .cookie import convertCookieParameter
from .cookie import getCookieParamPolicy
from .cookie import getCookieValuePolicy


# This may get overwritten during configuration
default_encoding = 'utf-8'

# Enable APPEND_TRACEBACKS to make Zope append tracebacks like it used to,
# but a better solution is to make standard_error_message display error_tb.
APPEND_TRACEBACKS = 0

status_codes = {}
# Add mappings for builtin exceptions and
# provide text -> error code lookups.
for key, val in status_reasons.items():
    status_codes[''.join(val.split(' ')).lower()] = key
    status_codes[val.lower()] = key
    status_codes[key] = key
    status_codes[str(key)] = key
en = [n for n in dir(__builtins__) if n[-5:] == 'Error']
for name in en:
    status_codes[name.lower()] = 500
status_codes['nameerror'] = 503
status_codes['keyerror'] = 503
status_codes['redirect'] = 302
status_codes['resourcelockederror'] = 423


start_of_header_search = re.compile('(<head[^>]*>)', re.IGNORECASE).search
base_re_search = re.compile('(<base.*?>)', re.I).search
bogus_str_search = re.compile(b" 0x[a-fA-F0-9]+>$").search
charset_re_str = (r'(?:application|text)/[-+0-9a-z]+\s*;\s*'
                  r'charset=([-_0-9a-z]+)(?:(?:\s*;)|\Z)')
charset_re_match = re.compile(charset_re_str, re.IGNORECASE).match
absuri_match = re.compile(r'\w+://[\w\.]+').match
tag_search = re.compile('[a-zA-Z]>').search

_gzip_header = (b"\037\213"  # magic
                b"\010"  # compression method
                b"\000"  # flags
                b"\000\000\000\000"  # time
                b"\002"
                b"\377")

# these mime major types should not be gzip content encoded
uncompressableMimeMajorTypes = ('image',)

# The environment variable DONT_GZIP_MAJOR_MIME_TYPES can be set to a list
# of comma separated mime major types which should also not be compressed

otherTypes = os.environ.get('DONT_GZIP_MAJOR_MIME_TYPES', '').lower()
if otherTypes:
    uncompressableMimeMajorTypes += tuple(otherTypes.split(','))

_CRLF = re.compile(r'[\r\n]')


def _scrubHeader(name, value):
    if isinstance(value, bytes):
        # handle ``bytes`` values correctly
        # we assume that the provider knows that HTTP 1.1 stipulates ISO-8859-1
        value = value.decode('ISO-8859-1')
    elif not isinstance(value, str):
        value = str(value)
    return ''.join(_CRLF.split(str(name))), ''.join(_CRLF.split(value))


_NOW = None  # overwrite for testing
MONTHNAME = [None, 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
             'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
WEEKDAYNAME = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']


def _now():
    if _NOW is not None:
        return _NOW
    return time.time()


def build_http_date(when):
    year, month, day, hh, mm, ss, wd, y, z = time.gmtime(when)
    return "%s, %02d %3s %4d %02d:%02d:%02d GMT" % (
        WEEKDAYNAME[wd], day, MONTHNAME[month], year, hh, mm, ss)


def make_content_disposition(disposition, file_name):
    """Create HTTP header for downloading a file with a UTF-8 filename.

    See this and related answers: https://stackoverflow.com/a/8996249/2173868.
    """
    header = f'{disposition}'
    try:
        file_name.encode('us-ascii')
    except UnicodeEncodeError:
        # the file cannot be encoded using the `us-ascii` encoding
        # which is advocated by RFC 7230 - 7237
        #
        # a special header has to be crafted
        # also see https://tools.ietf.org/html/rfc6266#appendix-D
        encoded_file_name = file_name.encode('us-ascii', errors='ignore')
        header += f'; filename="{encoded_file_name}"'
        quoted_file_name = quote(file_name)
        header += f'; filename*=UTF-8\'\'{quoted_file_name}'
        return header
    else:
        header += f'; filename="{file_name}"'
        return header


class HTTPBaseResponse(BaseResponse):
    """ An object representation of an HTTP response.

    The Response type encapsulates all possible responses to HTTP
    requests.  Responses are normally created by the object publisher.
    A published object may receive the response object as an argument
    named 'RESPONSE'.  A published object may also create it's own
    response object.  Normally, published objects use response objects
    to:

    - Provide specific control over output headers,

    - Set cookies, or

    - Provide stream-oriented output.

    If stream oriented output is used, then the response object
    passed into the object must be used.
    """

    body = b''
    base = ''
    charset = default_encoding
    realm = 'Zope'
    _error_format = 'text/html'
    _locked_status = 0
    _locked_body = 0

    # Indicate if setBody should content-compress output.
    # 0 - no compression
    # 1 - compress if accept-encoding ok
    # 2 - ignore accept-encoding (i.e. force)
    use_HTTP_content_compression = 0

    def __init__(self,
                 body=b'',
                 status=200,
                 headers=None,
                 stdout=None,
                 stderr=None):
        """ Create a new response using the given values.
        """
        self.accumulated_headers = []
        self.cookies = {}
        self.headers = {}

        if headers is not None:
            for key, value in headers.items():
                self.setHeader(key, value)

        self.setStatus(status)

        if stdout is None:
            stdout = BytesIO()
        self.stdout = stdout

        if stderr is None:
            stderr = BytesIO()
        self.stderr = stderr

        if body:
            self.setBody(body)

    @property
    def text(self):
        return self.body.decode(self.charset)

    @text.setter
    def text(self, value):
        self.body = value.encode(self.charset)

    def redirect(self, location, status=302, lock=0):
        """Cause a redirection without raising an error"""
        if isinstance(location, HTTPRedirection):
            status = location.getStatus()
            location = location.headers['Location']

        if isinstance(location, bytes):
            location = location.decode(self.charset)

        # To be entirely correct, we must make sure that all non-ASCII
        # characters are quoted correctly.
        parsed = list(urlparse(location))
        rfc2396_unreserved = "-_.!~*'()"  # RFC 2396 section 2.3
        for idx, idx_safe in (
                # authority
                (1, ";:@?/&=+$,"),  # RFC 2396 section 3.2, 3.2.1, 3.2.3
                # path
                (2, "/;:@&=+$,"),  # RFC 2396 section 3.3
                # params - actually part of path; empty in Python 3
                (3, "/;:@&=+$,"),  # RFC 2396 section 3.3
                # query
                (4, ";/?:@&=+,$"),  # RFC 2396 section 3.4
                # fragment
                (5, ";/?:@&=+$,"),  # RFC 2396 section 4
        ):
            # Make a hacky guess whether the component is already
            # URL-encoded by checking for %. If it is, we don't touch it.
            if '%' not in parsed[idx]:
                parsed[idx] = quote(parsed[idx],
                                    safe=rfc2396_unreserved + idx_safe)
        location = urlunparse(parsed)

        self.setStatus(status, lock=lock)
        self.setHeader('Location', location)
        return location

    def retry(self):
        """ Return a cloned response object to be used in a retry attempt.
        """
        # This implementation is a bit lame, because it assumes that
        # only stdout stderr were passed to the constructor. OTOH, I
        # think that that's all that is ever passed.
        return self.__class__(stdout=self.stdout, stderr=self.stderr)

    def setStatus(self, status, reason=None, lock=None):
        """ Set the HTTP status code of the response

        o The argument may either be an integer or a string from the
          'status_reasons' dict values:  status messages will be converted
          to the correct integer value.
        """
        if self._locked_status:
            # Don't change the response status.
            # It has already been determined.
            return

        if isinstance(status, type) and issubclass(status, Exception):
            status = status.__name__

        if isinstance(status, str):
            status = status.lower()

        if status in status_codes:
            status = status_codes[status]
        else:
            status = 500

        self.status = status

        if reason is None:
            if status in status_reasons:
                reason = status_reasons[status]
            else:
                reason = 'Unknown'

        self.errmsg = reason
        # lock the status if we're told to
        if lock:
            self._locked_status = 1

    def setCookie(self, name, value, quoted=True, **kw):
        """ Set an HTTP cookie.

        The response will include an HTTP header that sets a cookie on
        cookie-enabled browsers with a key "name" and value
        "value".

        This value overwrites any previously set value for the
        cookie in the Response object.

        `name` has to be text in Python 3.

        `value` may be text or bytes. The default encoding of respective python
        version is used.
        """
        cookie = {}
        for k, v in kw.items():
            k, v = convertCookieParameter(k, v)
            cookie[k] = v
        cookie['value'] = value
        # RFC6265 makes quoting obsolete
        # cookie['quoted'] = quoted
        getCookieParamPolicy().check_consistency(name, cookie)

        # update ``self.cookies`` only if there have been no exceptions
        cookies = self.cookies
        if name in cookies:
            cookies[name].update(cookie)
        else:
            cookies[name] = cookie

    def appendCookie(self, name, value):
        """ Set an HTTP cookie.

        Returns an HTTP header that sets a cookie on cookie-enabled
        browsers with a key "name" and value "value". If a value for the
        cookie has previously been set in the response object, the new
        value is appended to the old one separated by a colon.

        `name` has to be text in Python 3.

        `value` may be text or bytes. The default encoding of respective python
        version is used.
        """
        cookies = self.cookies
        if name in cookies:
            cookie = cookies[name]
        else:
            cookie = cookies[name] = {}
        if 'value' in cookie:
            cookie['value'] = f'{cookie["value"]}:{value}'
        else:
            cookie['value'] = value

    def expireCookie(self, name, **kw):
        """ Clear an HTTP cookie.

        The response will include an HTTP header that will remove the cookie
        corresponding to "name" on the client, if one exists. This is
        accomplished by sending a new cookie with an expiration date
        that has already passed. Note that some clients require a path
        to be specified - this path must exactly match the path given
        when creating the cookie. The path can be specified as a keyword
        argument.

        `name` has to be text in Python 3.
        """
        d = kw.copy()
        if 'value' in d:
            d.pop('value')
        d['max_age'] = 0
        d['expires'] = 'Wed, 31 Dec 1997 23:59:59 GMT'

        self.setCookie(name, value='deleted', **d)

    def getHeader(self, name, literal=0):
        """ Get a previously set header value.

        Return the value associated with a HTTP return header, or
        None if no such header has been set in the response
        yet.

        If the 'literal' flag is true, preserve the case of the header name;
        otherwise lower-case the header name before looking up the value.
        """
        key = literal and name or name.lower()
        return self.headers.get(key, None)

    def setHeader(self, name, value, literal=0, scrubbed=False):
        """ Set an HTTP return header on the response.

        Replay any existing value set for the header.

        If the 'literal' flag is true, preserve the case of the header name;
        otherwise the header name will be lowercased.

        'scrubbed' is for internal use, to indicate that another API has
        already removed any CRLF from the name and value.
        """
        if not scrubbed:
            name, value = _scrubHeader(name, value)
        key = name.lower()

        if key == 'content-type':
            if 'charset' in value:
                # Update self.charset with the charset from the header
                match = charset_re_match(value)
                if match:
                    self.charset = match.group(1)
            else:
                # Update the header value with self.charset
                if value.startswith('text/'):
                    value = value + '; charset=' + self.charset

        name = literal and name or key
        self.headers[name] = value

    def appendHeader(self, name, value, delimiter=", "):
        """ Append a value to an HTTP return header.

        Set an HTTP return header "name" with value "value",
        appending it following a comma if there was a previous value
        set for the header.

        'name' is always lowercased before use.
        """
        name, value = _scrubHeader(name, value)
        name = name.lower()

        headers = self.headers
        if name in headers:
            h = headers[name]
            h = f"{h}{delimiter}{value}"
        else:
            h = value
        self.setHeader(name, h, scrubbed=True)

    def addHeader(self, name, value):
        """ Set a new HTTP return header with the given value,

        Retain any previously set headers with the same name.

        Note that this API appends to the 'accumulated_headers' attribute;
        it does not update the 'headers' mapping.
        """
        name, value = _scrubHeader(name, value)
        self.accumulated_headers.append((name, value))

    __setitem__ = setHeader

    def setBase(self, base):
        """Set the base URL for the returned document.

        If base is None, set to the empty string.

        If base is not None, ensure that it has a trailing slash.
        """
        if base is None:
            base = ''
        elif not base.endswith('/'):
            base = base + '/'

        self.base = str(base)

    def insertBase(self):
        # Only insert a base tag if content appears to be HTML.
        content_type = self.headers.get('content-type', '').split(';')[0]
        if content_type and (content_type != 'text/html'):
            return

        if self.base and self.body:
            text = self.text
            match = start_of_header_search(text)
            if match is not None:
                index = match.start(0) + len(match.group(0))
                ibase = base_re_search(text)
                if ibase is None:
                    text = (text[:index] + '\n<base href="'
                            + html.escape(self.base, True) + '" />\n'
                            + text[index:])
                    self.text = text
                    self.setHeader('content-length', len(self.body))

    def isHTML(self, text):
        if isinstance(text, bytes):
            try:
                text = text.decode(self.charset)
            except UnicodeDecodeError:
                return False
        text = text.lstrip()
        # Note that the string can be big, so text.lower().startswith()
        # is more expensive than s[:n].lower().
        if text[:6].lower() == '<html>' or \
           text[:14].lower() == '<!doctype html':
            return True
        if text.find('</') > 0:
            return True
        return False

    def setBody(self, body, title='', is_error=False, lock=None):
        """ Set the body of the response

        Sets the return body equal to the (string) argument "body". Also
        updates the "content-length" return header.

        If the body is already locked via a previous call, do nothing and
        return None.

        You can also specify a title, in which case the title and body
        will be wrapped up in html, head, title, and body tags.

        If body has an 'asHTML' method, replace it by the result of that
        method.

        If body is now bytes, bytearray or memoryview, convert it to bytes.
        Else, either try to convert it to bytes or use an intermediate string
        representation which is then converted to bytes, depending on the
        content type.

        If is_error is true, format the HTML as a Zope error message instead
        of a generic HTML page.

        Return 'self' (XXX as a true value?).
        """
        # allow locking of the body in the same way as the status
        if self._locked_body:
            return
        elif lock:
            self._locked_body = 1

        if not body:
            return self

        content_type = self.headers.get('content-type')

        if hasattr(body, 'asHTML'):
            body = body.asHTML()
            if content_type is None:
                content_type = 'text/html'

        if isinstance(body, (bytes, bytearray, memoryview)):
            body = bytes(body)
        elif content_type is not None and not content_type.startswith('text/'):
            try:
                body = bytes(body)
            except (TypeError, UnicodeError):
                pass
        if not isinstance(body, bytes):
            body = self._encode_unicode(str(body))

        # At this point body is always binary
        b_len = len(body)
        if b_len < 200 and \
           body[:1] == b'<' and \
           body.find(b'>') == b_len - 1 and \
           bogus_str_search(body) is not None:
            self.notFoundError(body[1:-1].decode(self.charset))
        else:
            if title:
                title = str(title)
                content_type = 'text/html'
                if not is_error:
                    self.body = body = self._html(
                        title, body.decode(self.charset)).encode(self.charset)
                else:
                    self.body = body = self._error_html(
                        title, body.decode(self.charset)).encode(self.charset)
            else:
                self.body = body

        if content_type is None:
            content_type = f'text/plain; charset={self.charset}'
            self.setHeader('content-type', content_type)
        else:
            if content_type.startswith('text/') and \
               'charset=' not in content_type:
                content_type = f'{content_type}; charset={self.charset}'
                self.setHeader('content-type', content_type)

        self.setHeader('content-length', len(self.body))

        self.insertBase()

        if self.use_HTTP_content_compression and \
           self.headers.get('content-encoding', 'gzip') == 'gzip':
            # use HTTP content encoding to compress body contents unless
            # this response already has another type of content encoding
            if content_type.split('/')[0] not in uncompressableMimeMajorTypes:
                # only compress if not listed as uncompressable
                body = self.body
                startlen = len(body)
                co = zlib.compressobj(6, zlib.DEFLATED, -zlib.MAX_WBITS,
                                      zlib.DEF_MEM_LEVEL, 0)
                chunks = [_gzip_header, co.compress(body),
                          co.flush(),
                          struct.pack("<LL",
                                      zlib.crc32(body) & 0xffffffff,
                                      startlen)]
                z = b''.join(chunks)
                newlen = len(z)
                if newlen < startlen:
                    self.body = z
                    self.setHeader('content-length', newlen)
                    self.setHeader('content-encoding', 'gzip')
                    if self.use_HTTP_content_compression == 1:
                        # use_HTTP_content_compression == 1 if force was
                        # NOT used in enableHTTPCompression().
                        # If we forced it, then Accept-Encoding
                        # was ignored anyway, so cache should not
                        # vary on it. Otherwise if not forced, cache should
                        # respect Accept-Encoding client header
                        vary = self.getHeader('Vary')
                        if vary is None or 'Accept-Encoding' not in vary:
                            self.appendHeader('Vary', 'Accept-Encoding')
        return self

    def enableHTTPCompression(self, REQUEST={}, force=0, disable=0, query=0):
        """Enable HTTP Content Encoding with gzip compression if possible

           REQUEST -- used to check if client can accept compression
           force   -- set true to ignore REQUEST headers
           disable -- set true to disable compression
           query   -- just return if compression has been previously requested

           returns -- 1 if compression will be attempted, 2 if compression
                      is forced, 0 if no compression

           The HTTP specification allows for transfer encoding and content
           encoding. Unfortunately many web browsers still do not support
           transfer encoding, but they all seem to support content encoding.

           This function is designed to be called on each request to specify
           on a request-by-request basis that the response content should
           be compressed.

           The REQUEST headers are used to determine if the client accepts
           gzip content encoding. The force parameter can force the use
           of gzip encoding regardless of REQUEST, and the disable parameter
           can be used to "turn off" previously enabled encoding (but note
           that any existing content-encoding header will not be changed).
           The query parameter can be used to determine the if compression
           has been previously requested.

           In setBody, the major mime type is used to determine if content
           encoding should actually be performed.

           By default, image types are not compressed.
           Additional major mime types can be specified by setting the
           environment variable DONT_GZIP_MAJOR_MIME_TYPES to a comma-seperated
           list of major mime types that should also not be gzip compressed.
        """
        if query:
            return self.use_HTTP_content_compression

        elif disable:
            # in the future, a gzip cache manager will need to ensure that
            # compression is off
            self.use_HTTP_content_compression = 0

        elif force or 'gzip' in REQUEST.get('HTTP_ACCEPT_ENCODING', ''):
            if force:
                self.use_HTTP_content_compression = 2
            else:
                self.use_HTTP_content_compression = 1

        return self.use_HTTP_content_compression

    def _encode_unicode(self, text):
        # Fixes the encoding in the XML preamble according
        # to the charset specified in the content-type header.
        if text.startswith('<?xml'):
            pos_right = text.find('?>')  # right end of the XML preamble
            text = ('<?xml version="1.0" encoding="' + self.charset
                    + '" ?>' + text[pos_right + 2:])

        # Encode the text data using the response charset
        text = text.encode(self.charset, 'replace')
        return text

    def _cookie_list(self):
        cookie_list = []
        dump = getCookieValuePolicy().dump
        parameters = getCookieParamPolicy().parameters
        for name, attrs in self.cookies.items():
            params = []
            for pn, pv in parameters(name, attrs):
                if pv is None:
                    continue
                params.append(pn if pv is True else f"{pn}={pv}")
            cookie = "{}={}".format(name, dump(name, attrs["value"]))
            if params:
                cookie += "; " + "; ".join(params)
            # Should really check size of cookies here!
            cookie_list.append(('Set-Cookie', cookie))
        return cookie_list

    def listHeaders(self):
        """ Return a list of (key, value) pairs for our headers.

        o Do appropriate case normalization.

        o Encode header values via `header_encoding_registry`
        """

        result = [
            ('X-Powered-By', 'Zope (www.zope.dev), Python (www.python.org)')
        ]

        encode = header_encoding_registry.encode
        for key, value in self.headers.items():
            if key.lower() == key:
                # only change non-literal header names
                key = '-'.join([x.capitalize() for x in key.split('-')])
            result.append((key, encode(key, value)))

        result.extend(self._cookie_list())
        for key, value in self.accumulated_headers:
            result.append((key, encode(key, value)))
        return result

    def _unauthorized(self):
        realm = self.realm
        if realm:
            self.setHeader(
                'WWW-Authenticate',
                'basic realm="%s", charset="UTF-8"' % realm,
                1)

    @staticmethod
    def _html(title, body):
        return ("<html>\n"
                "<head>\n<title>%s</title>\n</head>\n"
                "<body>\n%s\n</body>\n"
                "</html>\n" % (title, body))


class HTTPResponse(HTTPBaseResponse):

    _wrote = None

    def __bytes__(self):
        if self._wrote:
            return b''  # Streaming output was used.

        status, headers = self.finalize()
        body = self.body

        chunks = []

        # status header must come first.
        chunks.append(b"Status: " + status.encode('ascii'))

        for key, value in headers:
            chunks.append(key.encode('ascii') + b': ' + value.encode('ascii'))
        # RFC 2616 mandates empty line between headers and payload
        chunks.append(b'')
        chunks.append(body)
        return b'\r\n'.join(chunks)

    # deprecated
    def quoteHTML(self, text):
        return html.escape(text, 1)

    def _traceback(self, t, v, tb, as_html=1):
        tb = format_exception(t, v, tb, as_html=as_html)
        return '\n'.join(tb)

    def _error_html(self, title, body):
        return ("""<!DOCTYPE html><html>
  <head><title>Site Error</title><meta charset="utf-8" /></head>
  <body bgcolor="#FFFFFF">
  <h2>Site Error</h2>
  <p>An error was encountered while publishing this resource.
  </p>
  <p><strong>""" + title + """</strong></p>

  """ + body + """
  <hr noshade="noshade"/>

  <p>Troubleshooting Suggestions</p>

  <ul>
  <li>The URL may be incorrect.</li>
  <li>The parameters passed to this resource may be incorrect.</li>
  <li>A resource that this resource relies on may be
      encountering an error.</li>
  </ul>

  <p>If the error persists please contact the site maintainer.
  Thank you for your patience.
  </p></body></html>""")

    def notFoundError(self, entry='Unknown'):
        self.setStatus(404)
        raise NotFound(self._error_html(
            "Resource not found",
            ("Sorry, the requested resource does not exist."
             "<p>Check the URL and try again.</p>"
             "<p><b>Resource:</b> " + html.escape(entry) + "</p>")))

    # If a resource is forbidden, why reveal that it exists?
    forbiddenError = notFoundError

    def debugError(self, entry):
        raise NotFound(self._error_html(
            "Debugging Notice",
            (
                "Zope has encountered a problem publishing your object. "
                "<p>%s</p>" % repr(entry)
            )
        ))

    def badRequestError(self, name):
        self.setStatus(400)
        if re.match('^[A-Z_0-9]+$', name):
            raise InternalError(self._error_html(
                "Internal Error",
                "Sorry, an internal error occurred in this resource."))

        raise BadRequest(self._error_html(
            "Invalid request",
            ("The parameter, <em>" + name + "</em>, "
             "was omitted from the request.<p>"
             "Make sure to specify all required parameters, "
             "and try the request again.</p>")))

    def unauthorized(self):
        m = "You are not authorized to access this resource."
        if self.debug_mode:
            if self._auth:
                m = m + '\nUsername and password are not correct.'
            else:
                m = m + '\nNo Authorization header found.'
        raise Unauthorized(m)

    def exception(self, fatal=0, info=None, abort=1):
        if isinstance(info, tuple) and len(info) == 3:
            t, v, tb = info
        else:
            t, v, tb = sys.exc_info()

        if issubclass(t, Unauthorized):
            self._unauthorized()

        self.setStatus(t)
        if 300 <= self.status < 400:
            if isinstance(v, str) and absuri_match(v) is not None:
                if self.status == 300:
                    self.setStatus(302)
                self.setHeader('location', v)
                tb = None  # just one path covered
                return self
            elif isinstance(v, Redirect):
                if self.status == 300:
                    self.setStatus(302)
                self.setHeader('location', v.args[0])
                self.setBody(b'')
                tb = None
                return self
            else:
                try:
                    l, b = v
                    if isinstance(l, str) and absuri_match(l) is not None:
                        if self.status == 300:
                            self.setStatus(302)
                        self.setHeader('location', l)
                        self.setBody(b)
                        tb = None  # one more patch covered
                        return self
                except Exception:
                    pass  # tb is not cleared in this case

        b = v
        if isinstance(b, Exception):
            try:
                try:
                    b = str(b)
                except UnicodeDecodeError:
                    b = self._encode_unicode(str(b)).decode(self.charset)
            except Exception:
                b = '<unprintable %s object>' % type(b).__name__

        if fatal and t is SystemExit and v.code == 0:
            self.setHeader('content-type', 'text/html')
            body = self.setBody(
                'Zope has exited normally.<p>'
                + self._traceback(t, v, tb) + '</p>',
                title=t,
                is_error=True)
        else:
            try:
                match = tag_search(b)
            except TypeError:
                match = None

            if match is None:
                self.setHeader('content-type', 'text/html')
                body = self.setBody(
                    'Sorry, a site error occurred.<p>'
                    + self._traceback(t, v, tb) + '</p>',
                    title=t,
                    is_error=True)
            elif self.isHTML(b):
                # error is an HTML document, not just a snippet of html
                if APPEND_TRACEBACKS:
                    body = self.setBody(b + self._traceback(
                        t, '(see above)', tb), is_error=True)
                else:
                    body = self.setBody(b, is_error=True)
            else:
                body = self.setBody(
                    b + self._traceback(t, '(see above)', tb, 0),
                    title=t,
                    is_error=True)
        del tb
        return body

    def finalize(self):
        """ Set headers required by various parts of protocol.
        """
        body = self.body
        if 'content-length' not in self.headers and \
           'transfer-encoding' not in self.headers:
            self.setHeader('content-length', len(body))
        return "%d %s" % (self.status, self.errmsg), self.listHeaders()

    def write(self, data):
        """
        Return data as a stream

        HTML data may be returned using a stream-oriented interface.
        This allows the browser to display partial results while
        computation of a response to proceed.

        The published object should first set any output headers or
        cookies on the response object.

        Note that published objects must not generate any errors
        after beginning stream-oriented output.
        """
        if not self._wrote:
            notify(pubevents.PubBeforeStreaming(self))

            self.outputBody()
            self._wrote = 1
            self.stdout.flush()

        self.stdout.write(data)


class WSGIResponse(HTTPBaseResponse):
    """A response object for WSGI
    """
    _streaming = 0
    _http_version = None
    _server_version = None

    # Append any "cleanup" functions to this list.
    after_list = ()

    def notFoundError(self, entry='Unknown'):
        self.setStatus(404)
        exc = NotFound(entry)
        exc.title = 'Resource not found'
        exc.detail = (
            'Sorry, the requested resource does not exist.'
            '<p>Check the URL and try again.</p>'
            '<p><b>Resource:</b> %s</p>' % html.escape(entry, True))
        raise exc

    # If a resource is forbidden, why reveal that it exists?
    forbiddenError = notFoundError

    def debugError(self, entry):
        self.setStatus(404)
        exc = NotFound(entry)
        exc.title = 'Debugging Notice'
        exc.detail = (
            "Zope has encountered a problem publishing your object. "
            "<p>%s</p>" % repr(entry)
        )
        raise exc

    def badRequestError(self, name):
        if re.match('^[A-Z_0-9]+$', name):
            self.setStatus(500)
            exc = InternalError(name)
            exc.title = 'Internal Error'
            exc.detail = 'Sorry, an internal error occurred in this resource.'
            raise exc

        self.setStatus(400)
        exc = BadRequest(name)
        exc.title = 'Invalid request'
        exc.detail = (
            'The parameter, <em>%s</em>, '
            'was omitted from the request.<p>'
            'Make sure to specify all required parameters, '
            'and try the request again.</p>' % name)
        raise exc

    def unauthorized(self):
        message = 'You are not authorized to access this resource.'
        exc = Unauthorized(message)
        exc.title = message
        if self.debug_mode:
            if self._auth:
                exc.detail = 'Username and password are not correct.'
            else:
                exc.detail = 'No Authorization header found.'
        raise exc

    def exception(self, fatal=0, info=None, abort=1):
        if isinstance(info, tuple) and len(info) == 3:
            t, v, tb = info
        else:
            t, v, tb = sys.exc_info()

        if issubclass(t, Unauthorized):
            self._unauthorized()

        raise v.with_traceback(tb)

    def finalize(self):
        # Set 204 (no content) status if 200 and response is empty
        # and not streaming.
        if 'content-type' not in self.headers and \
           'content-length' not in self.headers and \
           not self._streaming and \
           self.status == 200:
            self.setStatus('nocontent')

        # Add content length if not streaming.
        content_length = self.headers.get('content-length')
        if content_length is None and not self._streaming:
            self.setHeader('content-length', len(self.body))

        return f'{self.status} {self.errmsg}', self.listHeaders()

    def listHeaders(self):
        result = []
        if self._server_version:
            result.append(('Server', self._server_version))

        result.append(('Date', build_http_date(_now())))
        result.extend(super().listHeaders())
        return result

    def write(self, data):
        """Add data to our output stream.

        HTML data may be returned using a stream-oriented interface.
        This allows the browser to display partial results while
        computation of a response proceeds.
        """
        if not self._streaming:
            notify(pubevents.PubBeforeStreaming(self))
            self._streaming = 1
            self.stdout.flush()

        self.stdout.write(data)

    def setBody(self, body, title='', is_error=False, lock=None):
        # allow locking of the body in the same way as the status
        if self._locked_body:
            return

        if isinstance(body, IOBase):
            body.seek(0, 2)
            length = body.tell()
            body.seek(0)
            self.setHeader('Content-Length', '%d' % length)
            self.body = body
        elif IStreamIterator.providedBy(body):
            self.body = body
            super().setBody(b'', title, is_error)
        elif IUnboundStreamIterator.providedBy(body):
            self.body = body
            self._streaming = 1
            super().setBody(b'', title, is_error)
        else:
            super().setBody(body, title, is_error)

        # Have to apply the lock at the end in case the super class setBody
        # is called, which will observe the lock and do nothing
        if lock:
            self._locked_body = 1

    def __bytes__(self):
        raise NotImplementedError

    def __str__(self):
        raise NotImplementedError


# HTTP header encoding
class HeaderEncodingRegistry(dict):
    """Encode HTTP headers.

    HTTP/1.1 uses `ISO-8859-1` as charset for its headers
    (the modern spec (RFC 7230-7235) has deprecated non ASCII characters
    but for the sake of older browsers we still use `ISO-8859-1`).
    Header values need encoding if they contain characters
    not expressible in this charset.

    HTTP/1.1 is based on MIME
    ("Multimedia Internet Mail Extensions" RFC 2045-2049).
    MIME knows about 2 header encodings:
     - one for parameter values (RFC 2231)
     - and one word words as part of text, phrase or comment (RFC 2047)
    For use with HTTP/1.1 MIME's parameter value encoding (RFC 2231)
    was specialized and simplified via RFC 5987 and RFC 8187.

    For efficiency reasons and because HTTP is an extensible
    protocol (an application can use headers not specified
    by HTTP), we use an encoding registry to guide the header encoding.
    An application can register an encoding for specific keys and/or
    a default encoding to be used for keys without specific registration.
    If there is neither a specific encoding nor a default encoding,
    a header value remains unencoded.
    Header values are encoded only if they contain non `ISO-8859-1` characters.
    """

    def register(self, header, encoder, **kw):
        """register *encoder* as encoder for header *header*.

        If *encoder* is `None`, this indicates that *header* should not
        get encoded.

        If *header* is `None`, this indicates that *encoder* is defined
        as the default encoder.

        When encoding is necessary, *encoder* is called with
        the header value and the keywords specified by *kw*.
        """
        if header is not None:
            header = header.lower()
        self[header] = encoder, kw

    def unregister(self, header):
        """remove any registration for *header*.

        *header* can be either a header name or `None`.
        In the latter case, a default registration is removed.
        """
        if header is not None:
            header = header.lower()
        if header in self:
            del self[header]

    def encode(self, header, value):
        """encode *value* as specified for *header*.

        encoding takes only place if *value* contains non ISO-8859-1 chars.
        """
        if not isinstance(value, str):
            return value
        header = header.lower()
        reg = self.get(header) or self.get(None)
        if reg is None or reg[0] is None or non_latin_1(value) is None:
            return value
        return reg[0](value, **reg[1])


non_latin_1 = re.compile(r"[^\x00-\xff]").search


def encode_words(value):
    """RFC 2047 word encoding.

    Note: treats *value* as unstructured data
    and therefore must not be applied for headers with
    a structured value (unless the structure is garanteed
    to only contain ISO-8859-1 chars).
    """
    return Header(value, 'utf-8', 1000000).encode()


def encode_params(value):
    """RFC 5987(8187) (specialized from RFC 2231) parameter encoding.

    This encodes parameters as specified by RFC 5987 using
    fixed `UTF-8` encoding (as required by RFC 8187).
    However, all parameters with non latin-1 values are
    automatically transformed and a `*` suffixed parameter is added
    (RFC 8187 allows this only for parameters explicitly specified
    to have this behavior).

    Many HTTP headers use `,` separated lists. For simplicity,
    such headers are not supported (we would need to recognize
    `,` inside quoted strings as special).
    """
    params = []
    for p in _parseparam(";" + value):
        p = p.strip()
        if not p:
            continue
        params.append([s.strip() for s in p.split("=", 1)])
    known_params = {p[0] for p in params}
    for p in params[:]:
        if len(p) == 2 and non_latin_1(p[1]):  # need encoding
            pn = p[0]
            pnc = pn + "*"
            pv = p[1]
            if pnc not in known_params:
                if pv.startswith('"'):
                    pv = pv[1:-1]  # remove quotes
                params.append((pnc, encode_rfc2231(pv, "utf-8", None)))
            # backward compatibility for clients not understanding RFC 5987
            p[1] = p[1].encode("iso-8859-1", "replace").decode("iso-8859-1")
    return "; ".join("=".join(p) for p in params)


header_encoding_registry = HeaderEncodingRegistry()
header_encoding_registry.register("content-type", encode_params)
header_encoding_registry.register("content-disposition", encode_params)
