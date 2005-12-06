#############################################################################
#
# Copyright (c) 2002 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
'''CGI Response Output formatter

$Id$'''
__version__ = '$Revision: 1.81 $'[11:-2]

import types, os, sys, re
import zlib, struct
from string import translate, maketrans
from BaseResponse import BaseResponse
from zExceptions import Unauthorized, Redirect
from zExceptions.ExceptionFormatter import format_exception
from ZPublisher import BadRequest, InternalError, NotFound
from cgi import escape

nl2sp = maketrans('\n',' ')

# This may get overwritten during configuration
default_encoding = 'iso-8859-15'

# Enable APPEND_TRACEBACKS to make Zope append tracebacks like it used to,
# but a better solution is to make standard_error_message display error_tb.
APPEND_TRACEBACKS = 0


status_reasons = {
100: 'Continue',
101: 'Switching Protocols',
102: 'Processing',
200: 'OK',
201: 'Created',
202: 'Accepted',
203: 'Non-Authoritative Information',
204: 'No Content',
205: 'Reset Content',
206: 'Partial Content',
207: 'Multi-Status',
300: 'Multiple Choices',
301: 'Moved Permanently',
302: 'Moved Temporarily',
303: 'See Other',
304: 'Not Modified',
305: 'Use Proxy',
307: 'Temporary Redirect',
400: 'Bad Request',
401: 'Unauthorized',
402: 'Payment Required',
403: 'Forbidden',
404: 'Not Found',
405: 'Method Not Allowed',
406: 'Not Acceptable',
407: 'Proxy Authentication Required',
408: 'Request Time-out',
409: 'Conflict',
410: 'Gone',
411: 'Length Required',
412: 'Precondition Failed',
413: 'Request Entity Too Large',
414: 'Request-URI Too Large',
415: 'Unsupported Media Type',
416: 'Requested range not satisfiable',
417: 'Expectation Failed',
422: 'Unprocessable Entity',
423: 'Locked',
424: 'Failed Dependency',
500: 'Internal Server Error',
501: 'Not Implemented',
502: 'Bad Gateway',
503: 'Service Unavailable',
504: 'Gateway Time-out',
505: 'HTTP Version not supported',
507: 'Insufficient Storage',
}

status_codes = {}
# Add mappings for builtin exceptions and
# provide text -> error code lookups.
for key, val in status_reasons.items():
    status_codes[''.join(val.split(' ')).lower()] = key
    status_codes[val.lower()] = key
    status_codes[key] = key
    status_codes[str(key)] = key
en = filter(lambda n: n[-5:] == 'Error', dir(__builtins__))
for name in en:
    status_codes[name.lower()] = 500
status_codes['nameerror'] = 503
status_codes['keyerror'] = 503
status_codes['redirect'] = 300


start_of_header_search = re.compile('(<head[^>]*>)', re.IGNORECASE).search

accumulate_header = {'set-cookie': 1}.has_key


_gzip_header = ("\037\213" # magic
                "\010" # compression method
                "\000" # flags
                "\000\000\000\000" # time
                "\002"
                "\377")

uncompressableMimeMajorTypes = ('image',)   # these mime major types should
                                            # not be gzip content encoded

# The environment variable DONT_GZIP_MAJOR_MIME_TYPES can be set to a list
# of comma seperated mime major types which should also not be compressed

otherTypes = os.environ.get('DONT_GZIP_MAJOR_MIME_TYPES','').lower()
if otherTypes:
    uncompressableMimeMajorTypes += tuple(otherTypes.split(','))


class HTTPResponse(BaseResponse):
    """\
    An object representation of an HTTP response.

    The Response type encapsulates all possible responses to HTTP
    requests.  Responses are normally created by the object publisher.
    A published object may recieve the response abject as an argument
    named 'RESPONSE'.  A published object may also create it's own
    response object.  Normally, published objects use response objects
    to:

    - Provide specific control over output headers,

    - Set cookies, or

    - Provide stream-oriented output.

    If stream oriented output is used, then the response object
    passed into the object must be used.
    """ #'

    accumulated_headers = ''
    body = ''
    realm = 'Zope'
    _error_format = 'text/html'
    _locked_status = 0
    _locked_body = 0

    # Indicate if setBody should content-compress output.
    # 0 - no compression
    # 1 - compress if accept-encoding ok
    # 2 - ignore accept-encoding (i.e. force)
    use_HTTP_content_compression = 0

    def __init__(self,body='',status=200,headers=None,
                 stdout=sys.stdout, stderr=sys.stderr,):
        '''\
        Creates a new response. In effect, the constructor calls
        "self.setBody(body); self.setStatus(status); for name in
        headers.keys(): self.setHeader(name, headers[name])"
        '''
        if headers is None:
            headers = {}
        self.headers = headers

        if status == 200:
            self.status = 200
            self.errmsg = 'OK'
            headers['status'] = "200 OK"
        else:
            self.setStatus(status)
        self.base = ''
        if body:
            self.setBody(body)
        self.cookies = {}
        self.stdout = stdout
        self.stderr = stderr

    def retry(self):
        """Return a response object to be used in a retry attempt
        """

        # This implementation is a bit lame, because it assumes that
        # only stdout stderr were passed to the constructor. OTOH, I
        # think that that's all that is ever passed.

        return self.__class__(stdout=self.stdout, stderr=self.stderr)

    _shutdown_flag = None
    def _requestShutdown(self, exitCode=0):
        """Request that the server shut down with exitCode after fulfilling
           the current request."""
        import ZServer
        ZServer.exit_code = exitCode
        self._shutdown_flag = 1

    def _shutdownRequested(self):
        """Returns true if this request requested a server shutdown."""
        return self._shutdown_flag is not None

    def setStatus(self, status, reason=None, lock=None):
        '''\
        Sets the HTTP status code of the response; the argument may
        either be an integer or a string from { OK, Created, Accepted,
        NoContent, MovedPermanently, MovedTemporarily,
        NotModified, BadRequest, Unauthorized, Forbidden,
        NotFound, InternalError, NotImplemented, BadGateway,
        ServiceUnavailable } that will be converted to the correct
        integer value. '''
        if self._locked_status:
            # Don't change the response status.
            # It has already been determined.
            return

        if (isinstance(status, types.ClassType)
         and issubclass(status, Exception)):
            status = status.__name__

        if isinstance(status, str):
            status = status.lower()

        if status_codes.has_key(status):
            status = status_codes[status]
        else:
            status = 500

        self.status = status

        if reason is None:
            if status_reasons.has_key(status):
                reason = status_reasons[status]
            else:
                reason = 'Unknown'
        self.setHeader('Status', "%d %s" % (status,str(reason)))
        self.errmsg = reason
        # lock the status if we're told to
        if lock:
             self._locked_status = 1

    def setHeader(self, name, value, literal=0):
        '''\
        Sets an HTTP return header "name" with value "value", clearing
        the previous value set for the header, if one exists. If the
        literal flag is true, the case of the header name is preserved,
        otherwise word-capitalization will be performed on the header
        name on output.'''
        name = str(name)
        value = str(value)
        key = name.lower()
        if accumulate_header(key):
            self.accumulated_headers = (
                "%s%s: %s\n" % (self.accumulated_headers, name, value))
            return
        name = literal and name or key
        self.headers[name] = value

    def addHeader(self, name, value):
        '''\
        Set a new HTTP return header with the given value, while retaining
        any previously set headers with the same name.'''
        name = str(name)
        value = str(value)
        self.accumulated_headers = (
            "%s%s: %s\n" % (self.accumulated_headers, name, value))

    __setitem__ = setHeader

    def setBody(self, body, title='', is_error=0,
                bogus_str_search=re.compile(" [a-fA-F0-9]+>$").search,
                latin1_alias_match=re.compile(
                r'text/html(\s*;\s*charset=((latin)|(latin[-_]?1)|'
                r'(cp1252)|(cp819)|(csISOLatin1)|(IBM819)|(iso-ir-100)|'
                r'(iso[-_]8859[-_]1(:1987)?)))?$',re.I).match,
                lock=None
                ):
        '''\
        Set the body of the response

        Sets the return body equal to the (string) argument "body". Also
        updates the "content-length" return header.

        You can also specify a title, in which case the title and body
        will be wrapped up in html, head, title, and body tags.

        If the body is a 2-element tuple, then it will be treated
        as (title,body)

        If is_error is true then the HTML will be formatted as a Zope error
        message instead of a generic HTML page.
        '''
        # allow locking of the body in the same way as the status
        if self._locked_body:
            return
        elif lock:
            self._locked_body = 1
            
        if not body:
            return self

        if isinstance(body, tuple) and len(body) == 2:
            title, body = body

        if not isinstance(body, str):
            if hasattr(body,'asHTML'):
                body = body.asHTML()

        if isinstance(body, unicode):
            body = self._encode_unicode(body)
        elif isinstance(body, str):
            pass
        else:
            try:
                body = str(body)
            except UnicodeError:
                body = self._encode_unicode(unicode(body))

        l = len(body)
        if ((l < 200) and body[:1] == '<' and body.find('>') == l-1 and
            bogus_str_search(body) is not None):
            self.notFoundError(body[1:-1])
        else:
            if(title):
                title = str(title)
                if not is_error:
                    self.body = self._html(title, body)
                else:
                    self.body = self._error_html(title, body)
            else:
                self.body = body


        if not self.headers.has_key('content-type'):
            isHTML = self.isHTML(self.body)
            if isHTML:
                c = 'text/html'
            else:
                c = 'text/plain'
            self.setHeader('content-type', c)

        # Some browsers interpret certain characters in Latin 1 as html
        # special characters. These cannot be removed by html_quote,
        # because this is not the case for all encodings.
        content_type = self.headers['content-type']
        if content_type == 'text/html' or latin1_alias_match(
            content_type) is not None:
            body = '&lt;'.join(body.split('\213'))
            body = '&gt;'.join(body.split('\233'))

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
                co = zlib.compressobj(6,zlib.DEFLATED,-zlib.MAX_WBITS,
                                      zlib.DEF_MEM_LEVEL,0)
                chunks = [_gzip_header, co.compress(body),
                          co.flush(),
                          struct.pack("<ll",zlib.crc32(body),startlen)]
                z = "".join(chunks)
                newlen = len(z)
                if newlen < startlen:
                    self.body = z
                    self.setHeader('content-length', newlen)
                    self.setHeader('content-encoding','gzip')
                    if self.use_HTTP_content_compression == 1:
                        # use_HTTP_content_compression == 1 if force was
                        # NOT used in enableHTTPCompression().
                        # If we forced it, then Accept-Encoding
                        # was ignored anyway, so cache should not
                        # vary on it. Otherwise if not forced, cache should
                        # respect Accept-Encoding client header
                        self.appendHeader('Vary','Accept-Encoding')
        return self

    def enableHTTPCompression(self,REQUEST={},force=0,disable=0,query=0):
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
           be compressed. This is quite useful for xml-rpc transactions, where
           compression rates of 90% or more can be achieved for text data.

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

        elif (force or
              (REQUEST.get('HTTP_ACCEPT_ENCODING','').find('gzip') != -1)):
            if force:
                self.use_HTTP_content_compression = 2
            else:
                self.use_HTTP_content_compression = 1

        return self.use_HTTP_content_compression

    def _encode_unicode(self,body,
                        charset_re=re.compile(r'(?:application|text)/[-+0-9a-z]+\s*;\s*' +
                                              r'charset=([-_0-9a-z]+' +
                                              r')(?:(?:\s*;)|\Z)',
                                              re.IGNORECASE)):
        # Encode the Unicode data as requested
        if self.headers.has_key('content-type'):
            match = charset_re.match(self.headers['content-type'])
            if match:
                encoding = match.group(1)
                return body.encode(encoding)
        # Use the default character encoding
        return body.encode(default_encoding,'replace')

    def setBase(self,base):
        """Set the base URL for the returned document.
        If base is None, or the document already has a base, do nothing."""
        if base is None:
            base = ''
        elif not base.endswith('/'):
            base = base+'/'
        self.base = str(base)

    def insertBase(self,
                   base_re_search=re.compile('(<base.*?>)',re.I).search
                   ):

        # Only insert a base tag if content appears to be html.
        content_type = self.headers.get('content-type', '').split(';')[0]
        if content_type and (content_type != 'text/html'):
            return

        if self.base:
            body = self.body
            if body:
                match = start_of_header_search(body)
                if match is not None:
                    index = match.start(0) + len(match.group(0))
                    ibase = base_re_search(body)
                    if ibase is None:
                        self.body = ('%s\n<base href="%s" />\n%s' %
                                   (body[:index], escape(self.base, 1),
                                    body[index:]))
                        self.setHeader('content-length', len(self.body))

    def appendCookie(self, name, value):
        '''\
        Returns an HTTP header that sets a cookie on cookie-enabled
        browsers with a key "name" and value "value". If a value for the
        cookie has previously been set in the response object, the new
        value is appended to the old one separated by a colon. '''

        name = str(name)
        value = str(value)

        cookies = self.cookies
        if cookies.has_key(name):
            cookie = cookies[name]
        else:
            cookie = cookies[name] = {}
        if cookie.has_key('value'):
            cookie['value'] = '%s:%s' % (cookie['value'], value)
        else:
            cookie['value'] = value

    def expireCookie(self, name, **kw):
        '''\
        Cause an HTTP cookie to be removed from the browser

        The response will include an HTTP header that will remove the cookie
        corresponding to "name" on the client, if one exists. This is
        accomplished by sending a new cookie with an expiration date
        that has already passed. Note that some clients require a path
        to be specified - this path must exactly match the path given
        when creating the cookie. The path can be specified as a keyword
        argument.
        '''
        name = str(name)

        d = kw.copy()
        d['max_age'] = 0
        d['expires'] = 'Wed, 31-Dec-97 23:59:59 GMT'
        apply(HTTPResponse.setCookie, (self, name, 'deleted'), d)

    def setCookie(self,name,value,**kw):
        '''\
        Set an HTTP cookie on the browser

        The response will include an HTTP header that sets a cookie on
        cookie-enabled browsers with a key "name" and value
        "value". This overwrites any previously set value for the
        cookie in the Response object.
        '''
        name = str(name)
        value = str(value)

        cookies = self.cookies
        if cookies.has_key(name):
            cookie = cookies[name]
        else:
            cookie = cookies[name] = {}
        for k, v in kw.items():
            cookie[k] = v
        cookie['value'] = value

    def appendHeader(self, name, value, delimiter=","):
        '''\
        Append a value to a header.

        Sets an HTTP return header "name" with value "value",
        appending it following a comma if there was a previous value
        set for the header. '''
        name = str(name).lower()
        value = str(value)

        headers = self.headers
        if headers.has_key(name):
            h = headers[name]
            h = "%s%s\n\t%s" % (h,delimiter,value)
        else:
            h = value
        self.setHeader(name,h)

    def isHTML(self, s):
        s = s.lstrip()
        # Note that the string can be big, so s.lower().startswith() is more
        # expensive than s[:n].lower().
        if (s[:6].lower() == '<html>' or s[:14].lower() == '<!doctype html'):
            return 1
        if s.find('</') > 0:
            return 1
        return 0

    # deprecated
    def quoteHTML(self, text):
        return escape(text, 1)

    def _traceback(self, t, v, tb, as_html=1):
        tb = format_exception(t, v, tb, as_html=as_html)
        return '\n'.join(tb)

    def redirect(self, location, status=302, lock=0):
        """Cause a redirection without raising an error"""
        self.setStatus(status)
        self.setHeader('Location', location)

        location = str(location)

        if lock:
            # Don't let anything change the status code.
            # The "lock" argument needs to be set when redirecting
            # from a standard_error_message page.
            self._locked_status = 1
        return location


    def _html(self,title,body):
        return ("<html>\n"
                "<head>\n<title>%s</title>\n</head>\n"
                "<body>\n%s\n</body>\n"
                "</html>\n" % (title,body))

    def _error_html(self,title,body):
        # XXX could this try to use standard_error_message somehow?
        return ("""\
<table border="0" width="100%">
<tr valign="top">

<td width="10%" align="center">
&nbsp;
</td>

<td width="90%">
  <h2>Site Error</h2>
  <p>An error was encountered while publishing this resource.
  </p>""" + \
  """
  <p><strong>%s</strong></p>

  %s""" %(title,body) + \
  """
  <hr noshade="noshade"/>

  <p>Troubleshooting Suggestions</p>

  <ul>
  <li>The URL may be incorrect.</li>
  <li>The parameters passed to this resource may be incorrect.</li>
  <li>A resource that this resource relies on may be
      encountering an error.</li>
  </ul>

  <p>For more detailed information about the error, please
  refer to error log.
  </p>

  <p>If the error persists please contact the site maintainer.
  Thank you for your patience.
  </p>
</td></tr>
</table>""")


    def notFoundError(self,entry='Unknown'):
        self.setStatus(404)
        raise NotFound, self._error_html(
            "Resource not found",
            "Sorry, the requested resource does not exist." +
            "<p>Check the URL and try again.</p>" +
            "<p><b>Resource:</b> %s</p>" % escape(entry))

    forbiddenError = notFoundError  # If a resource is forbidden,
                                    # why reveal that it exists?

    def debugError(self,entry):
        raise NotFound, self._error_html(
            "Debugging Notice",
            "Zope has encountered a problem publishing your object.<p>"
            "\n%s" % entry)

    def badRequestError(self,name):
        self.setStatus(400)
        if re.match('^[A-Z_0-9]+$',name):
            raise InternalError, self._error_html(
                "Internal Error",
                "Sorry, an internal error occurred in this resource.")

        raise BadRequest, self._error_html(
            "Invalid request",
            "The parameter, <em>%s</em>, " % name +
            "was omitted from the request.<p>" +
            "Make sure to specify all required parameters, " +
            "and try the request again."
            )

    def _unauthorized(self):
        realm = self.realm
        if realm:
            self.setHeader('WWW-Authenticate', 'basic realm="%s"' % realm, 1)

    def unauthorized(self):
        self._unauthorized()
        m = "<strong>You are not authorized to access this resource.</strong>"
        if self.debug_mode:
            if self._auth:
                m = m + '<p>\nUsername and password are not correct.'
            else:
                m = m + '<p>\nNo Authorization header found.'
        raise Unauthorized, m

    def exception(self, fatal=0, info=None,
                  absuri_match=re.compile(r'\w+://[\w\.]+').match,
                  tag_search=re.compile('[a-zA-Z]>').search,
                  abort=1
                  ):
        if type(info) is type(()) and len(info) == 3:
            t, v, tb = info
        else:
            t, v, tb = sys.exc_info()

        if t == 'Unauthorized' or t == Unauthorized or (
            isinstance(t, types.ClassType) and issubclass(t, Unauthorized)):
            t = 'Unauthorized'
            self._unauthorized()

        stb = tb # note alias between tb and stb

        try:
            # Try to capture exception info for bci calls
            et = translate(str(t), nl2sp)
            self.setHeader('bobo-exception-type', et)

            # As of Zope 2.6.2 / 2.7, we no longer try to pass along a
            # meaningful exception value. Now that there are good logging
            # facilities on the server side (and given that xml-rpc has
            # largely removed the need for this code at all), we just
            # refer the caller to the server error log.
            ev = 'See the server error log for details'
            self.setHeader('bobo-exception-value', ev)

            # Get the tb tail, which is the interesting part:
            while tb.tb_next is not None:
                tb = tb.tb_next
            el = str(tb.tb_lineno)
            ef = str(tb.tb_frame.f_code.co_filename)

            # Do not give out filesystem information.
            ef = ef.split(os.sep)[-1]

            self.setHeader('bobo-exception-file', ef)
            self.setHeader('bobo-exception-line', el)

        except:
            # Dont try so hard that we cause other problems ;)
            pass

        tb = stb # original traceback
        del stb
        self.setStatus(t)
        if self.status >= 300 and self.status < 400:
            if isinstance(v, str) and absuri_match(v) is not None:
                if self.status == 300:
                    self.setStatus(302)
                self.setHeader('location', v)
                tb = None # just one path covered
                return self
            elif isinstance(v, Redirect): # death to string exceptions!
                if self.status == 300:
                    self.setStatus(302)
                self.setHeader('location', v.args[0])
                self.setBody('')
                tb = None
                return self
            else:
                try:
                    l, b = v
                    if (isinstance(l, str)
                        and absuri_match(l) is not None):
                        if self.status == 300:
                            self.setStatus(302)
                        self.setHeader('location', l)
                        self.setBody(b)
                        tb = None # one more patch covered
                        return self
                except:
                    pass # tb is not cleared in this case

        b = v
        if isinstance(b, Exception):
            try:
                b = str(b)
            except:
                b = '<unprintable %s object>' % type(b).__name__

        if fatal and t is SystemExit and v.code == 0:
            body = self.setBody(
                (str(t),
                 'Zope has exited normally.<p>' + self._traceback(t, v, tb)),
                is_error=1)
        else:
            try:
                match = tag_search(b)
            except TypeError:
                match = None
            if match is None:
                body = self.setBody(
                    (str(t),
                     'Sorry, a site error occurred.<p>'
                     + self._traceback(t, v, tb)),
                    is_error=1)
            elif self.isHTML(b):
                # error is an HTML document, not just a snippet of html
                if APPEND_TRACEBACKS:
                    body = self.setBody(b + self._traceback(
                        t, '(see above)', tb), is_error=1)
                else:
                    body = self.setBody(b, is_error=1)
            else:
                body = self.setBody(
                    (str(t), b + self._traceback(t,'(see above)', tb, 0)),
                    is_error=1)
        del tb
        return body

    _wrote = None

    def _cookie_list(self):
        cookie_list = []
        for name, attrs in self.cookies.items():

            # Note that as of May 98, IE4 ignores cookies with
            # quoted cookie attr values, so only the value part
            # of name=value pairs may be quoted.

            cookie = 'Set-Cookie: %s="%s"' % (name, attrs['value'])
            for name, v in attrs.items():
                name = name.lower()
                if name == 'expires':
                    cookie = '%s; Expires=%s' % (cookie,v)
                elif name == 'domain':
                    cookie = '%s; Domain=%s' % (cookie,v)
                elif name == 'path':
                    cookie = '%s; Path=%s' % (cookie,v)
                elif name == 'max_age':
                    cookie = '%s; Max-Age=%s' % (cookie,v)
                elif name == 'comment':
                    cookie = '%s; Comment=%s' % (cookie,v)
                elif name == 'secure' and v:
                    cookie = '%s; Secure' % cookie
            cookie_list.append(cookie)

        # Should really check size of cookies here!

        return cookie_list

    def __str__(self,
                html_search=re.compile('<html>',re.I).search,
                ):
        if self._wrote:
            return ''       # Streaming output was used.

        headers = self.headers
        body = self.body

        if not headers.has_key('content-length') and \
                not headers.has_key('transfer-encoding'):
            self.setHeader('content-length',len(body))

        headersl = []
        append = headersl.append

        # status header must come first.
        append("Status: %s" % headers.get('status', '200 OK'))
        append("X-Powered-By: Zope (www.zope.org), Python (www.python.org)")
        if headers.has_key('status'):
            del headers['status']
        for key, val in headers.items():
            if key.lower() == key:
                # only change non-literal header names
                key = "%s%s" % (key[:1].upper(), key[1:])
                start = 0
                l = key.find('-',start)
                while l >= start:
                    key = "%s-%s%s" % (key[:l],key[l+1:l+2].upper(),key[l+2:])
                    start = l + 1
                    l = key.find('-', start)
            append("%s: %s" % (key, val))
        if self.cookies:
            headersl = headersl+self._cookie_list()
        headersl[len(headersl):] = [self.accumulated_headers, body]
        return '\n'.join(headersl)

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
        if not self._wrote:
            self.outputBody()
            self._wrote = 1
            self.stdout.flush()

        self.stdout.write(data)
