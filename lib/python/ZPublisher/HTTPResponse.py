#############################################################################
#
# Copyright (c) 2001 Zope Corporation and Contributors. All Rights Reserved.
# 
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
# 
##############################################################################
'''CGI Response Output formatter

$Id: HTTPResponse.py,v 1.61 2002/06/12 19:06:38 Brian Exp $'''
__version__='$Revision: 1.61 $'[11:-2]

import types, os, sys, re
from string import translate, maketrans
from types import StringType, InstanceType, LongType, UnicodeType
from BaseResponse import BaseResponse
from zExceptions import Unauthorized
from zExceptions.ExceptionFormatter import format_exception

nl2sp=maketrans('\n',' ')


# Enable APPEND_TRACEBACKS to make Zope append tracebacks like it used to,
# but a better solution is to make standard_error_message display error_tb.
APPEND_TRACEBACKS = 0


status_reasons={
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

status_codes={}
# Add mappings for builtin exceptions and
# provide text -> error code lookups.
for key, val in status_reasons.items():
    status_codes[''.join(val.split(' ')).lower()]=key
    status_codes[val.lower()]=key
    status_codes[key]=key
    status_codes[str(key)]=key
en=filter(lambda n: n[-5:]=='Error', dir(__builtins__))
for name in en:
    status_codes[name.lower()]=500
status_codes['nameerror']=503
status_codes['keyerror']=503
status_codes['redirect']=300


start_of_header_search=re.compile('(<head[^>]*>)', re.IGNORECASE).search

accumulate_header={'set-cookie': 1}.has_key


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

    accumulated_headers=''
    body=''
    realm='Zope'
    _error_format='text/html'
    _locked_status = 0

    def __init__(self,body='',status=200,headers=None,
                 stdout=sys.stdout, stderr=sys.stderr,):
        '''\
        Creates a new response. In effect, the constructor calls
        "self.setBody(body); self.setStatus(status); for name in
        headers.keys(): self.setHeader(name, headers[name])"
        '''
        if headers is None: headers={}
        self.headers=headers

        if status==200:
            self.status=200
            self.errmsg='OK'
            headers['status']="200 OK"      
        else: self.setStatus(status)
        self.base=''
        if body: self.setBody(body)
        self.cookies={}
        self.stdout=stdout
        self.stderr=stderr

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
        sys.ZServerExitCode = exitCode
        self._shutdown_flag = 1

    def _shutdownRequested(self):
        """Returns true if this request requested a server shutdown."""
        return self._shutdown_flag is not None

    def setStatus(self, status, reason=None):
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
                
        if type(status) is types.StringType:
            status=status.lower()
        if status_codes.has_key(status): status=status_codes[status]
        else: 
            status=500
        self.status=status
        if reason is None:
            if status_reasons.has_key(status): reason=status_reasons[status]
            else: reason='Unknown'
        self.setHeader('Status', "%d %s" % (status,str(reason)))
        self.errmsg=reason

    def setHeader(self, name, value, literal=0):
        '''\
        Sets an HTTP return header "name" with value "value", clearing
        the previous value set for the header, if one exists. If the
        literal flag is true, the case of the header name is preserved,
        otherwise word-capitalization will be performed on the header
        name on output.'''
        key=name.lower()
        if accumulate_header(key):
            self.accumulated_headers=(
                "%s%s: %s\n" % (self.accumulated_headers, name, value))
            return
        name=literal and name or key
        self.headers[name]=value

    def addHeader(self, name, value):
        '''\
        Set a new HTTP return header with the given value, while retaining
        any previously set headers with the same name.'''
        self.accumulated_headers=(
            "%s%s: %s\n" % (self.accumulated_headers, name, value))

    __setitem__=setHeader

    def setBody(self, body, title='', is_error=0,
                bogus_str_search=re.compile(" [a-fA-F0-9]+>$").search,
                latin1_alias_match=re.compile(
                r'text/html(\s*;\s*charset=((latin)|(latin[-_]?1)|'
                r'(cp1252)|(cp819)|(csISOLatin1)|(IBM819)|(iso-ir-100)|'
                r'(iso[-_]8859[-_]1(:1987)?)))?$',re.I).match
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
        if not body: return self
        
        if type(body) is types.TupleType and len(body) == 2:
            title,body=body

        if type(body) is not types.StringType:
            if hasattr(body,'asHTML'):
                body=body.asHTML()

        if type(body) is UnicodeType:
            body = self._encode_unicode(body)
        elif type(body) is StringType:
            pass
        else:
            try:
                body = str(body)
            except UnicodeError:
                body = _encode_unicode(unicode(body))

        l=len(body)
        if ((l < 200) and body[:1]=='<' and body.find('>')==l-1 and 
            bogus_str_search(body) is not None):
            self.notFoundError(body[1:-1])
        else:
            if(title):
                title=str(title)
                if not is_error:
                    self.body=self._html(title, body)
                else:
                    self.body=self._error_html(title, body)
            else:
                self.body=body


        if not self.headers.has_key('content-type'):
            isHTML=self.isHTML(self.body)
            if isHTML: c='text/html'
            else:      c='text/plain'
            self.setHeader('content-type', c)

        # Some browsers interpret certain characters in Latin 1 as html
        # special characters. These cannot be removed by html_quote,
        # because this is not the case for all encodings.
        content_type=self.headers['content-type']
        if content_type == 'text/html' or latin1_alias_match(
            content_type) is not None:
            body = '&lt;'.join(body.split('\213'))
            body = '&gt;'.join(body.split('\233'))

        self.setHeader('content-length', len(self.body))
        self.insertBase()
        return self

    def _encode_unicode(self,body,charset_re=re.compile(r'text/[0-9a-z]+\s*;\s*charset=([-_0-9a-z]+)(?:(?:\s*;)|\Z)',re.IGNORECASE)):
        # Encode the Unicode data as requested
        if self.headers.has_key('content-type'):
            match = charset_re.match(self.headers['content-type'])
            if match:
                encoding = match.group(1)
                return body.encode(encoding)
        # Use the default character encoding
        return body.encode('latin1','replace')

    def setBase(self,base):
        'Set the base URL for the returned document.'
        if base[-1:] != '/':
            base=base+'/'
        self.base=base

    def insertBase(self,
                   base_re_search=re.compile('(<base.*?>)',re.I).search
                   ):

        # Only insert a base tag if content appears to be html.
        content_type = self.headers.get('content-type', '').split(';')[0]
        if content_type and (content_type != 'text/html'):
            return

        if self.base:
            body=self.body
            if body:
                match=start_of_header_search(body)
                if match is not None:
                    index=match.start(0) + len(match.group(0))
                    ibase=base_re_search(body)
                    if ibase is None:
                        self.body=('%s\n<base href="%s" />\n%s' %
                                   (body[:index], self.base, body[index:]))
                        self.setHeader('content-length', len(self.body))

    def appendCookie(self, name, value):
        '''\
        Returns an HTTP header that sets a cookie on cookie-enabled
        browsers with a key "name" and value "value". If a value for the
        cookie has previously been set in the response object, the new
        value is appended to the old one separated by a colon. '''

        cookies=self.cookies
        if cookies.has_key(name): cookie=cookies[name]
        else: cookie=cookies[name]={}
        if cookie.has_key('value'):
            cookie['value']='%s:%s' % (cookie['value'], value)
        else: cookie['value']=value

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
        dict={'max_age':0, 'expires':'Wed, 31-Dec-97 23:59:59 GMT'}
        for k, v in kw.items():
            dict[k]=v
        apply(HTTPResponse.setCookie, (self, name, 'deleted'), dict)

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

    def appendHeader(self, name, value, delimiter=","):
        '''\
        Append a value to a header.
        
        Sets an HTTP return header "name" with value "value",
        appending it following a comma if there was a previous value
        set for the header. '''
        headers=self.headers
        if headers.has_key(name):
            h=headers[name]
            h="%s%s\n\t%s" % (h,delimiter,value)
        else: h=value
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

    def quoteHTML(self,text,
                  subs={'&':'&amp;', "<":'&lt;', ">":'&gt;', '\"':'&quot;'}
                  ):
        for ent in '&<>\"':
            if text.find( ent) >= 0:
                text=subs[ent].join(text.split(ent))

        return text
         

    def _traceback(self, t, v, tb, as_html=1):
        tb = format_exception(t, v, tb, as_html=as_html)
        return '\n'.join(tb)

    def redirect(self, location, status=302, lock=0):
        """Cause a redirection without raising an error"""
        self.setStatus(status)
        self.setHeader('Location', location)

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
<TABLE BORDER="0" WIDTH="100%">
<TR VALIGN="TOP">

<TD WIDTH="10%" ALIGN="CENTER">
&nbsp;
</TD>

<TD WIDTH="90%">
  <H2>Site Error</H2>
  <P>An error was encountered while publishing this resource.
  </P>""" + \
  """
  <P><STRONG>%s</STRONG></P>
  
  %s""" %(title,body) + \
  """
  <HR NOSHADE>

  <P>Troubleshooting Suggestions</P>

  <UL>
  <LI>The URL may be incorrect.</LI>
  <LI>The parameters passed to this resource may be incorrect.</LI>
  <LI>A resource that this resource relies on may be
      encountering an error.</LI>
  </UL>

  <P>For more detailed information about the error, please
  refer to the HTML source for this page.
  </P>

  <P>If the error persists please contact the site maintainer.
  Thank you for your patience.
  </P>
</TD></TR>
</TABLE>""")

    def notFoundError(self,entry='Unknown'):
        self.setStatus(404)
        raise 'NotFound',self._error_html(
            "Resource not found",
            "Sorry, the requested resource does not exist." +
            "<p>Check the URL and try again.</p>" +
            "<p><b>Resource:</b> %s</p>" % self.quoteHTML(entry))

    forbiddenError=notFoundError  # If a resource is forbidden,
                                  # why reveal that it exists?

    def debugError(self,entry):
        raise 'NotFound',self._error_html(
            "Debugging Notice",
            "Zope has encountered a problem publishing your object.<p>"
            "\n%s" % entry)

    def badRequestError(self,name):
        self.setStatus(400)
        if re.match('^[A-Z_0-9]+$',name):
            raise 'InternalError', self._error_html(
                "Internal Error",
                "Sorry, an internal error occurred in this resource.")

        raise 'BadRequest',self._error_html(
            "Invalid request",
            "The parameter, <em>%s</em>, " % name +
            "was omitted from the request.<p>" + 
            "Make sure to specify all required parameters, " +
            "and try the request again."
            )

    def _unauthorized(self):
        realm=self.realm
        if realm:
            self.setHeader('WWW-Authenticate', 'basic realm="%s"' % realm, 1)

    def unauthorized(self):
        self._unauthorized()
        m="<strong>You are not authorized to access this resource.</strong>"
        if self.debug_mode:
            if self._auth:
                m=m+'<p>\nUsername and password are not correct.'
            else:
                m=m+'<p>\nNo Authorization header found.'
        raise Unauthorized, m

    def exception(self, fatal=0, info=None,
                  absuri_match=re.compile(r'\w+://[\w\.]+').match,
                  tag_search=re.compile('[a-zA-Z]>').search,
                  abort=1
                  ):
        if type(info) is type(()) and len(info)==3:
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
            ev = translate(str(v), nl2sp)
            if ev.find( '<html>') >= 0:
                ev = 'bobo exception'
            self.setHeader('bobo-exception-value', ev[:255])
            # Get the tb tail, which is the interesting part:
            while tb.tb_next is not None:
                tb = tb.tb_next
            el = str(tb.tb_lineno)
            ef = str(tb.tb_frame.f_code.co_filename)
            self.setHeader('bobo-exception-file', ef)
            self.setHeader('bobo-exception-line', el)

        except:
            # Dont try so hard that we cause other problems ;)
            pass

        tb = stb # original traceback
        del stb
        self.setStatus(t)
        if self.status >= 300 and self.status < 400:
            if type(v) == types.StringType and absuri_match(v) is not None:
                if self.status==300:
                    self.setStatus(302)
                self.setHeader('location', v)
                tb = None # just one path covered
                return self
            else:
                try:
                    l, b = v
                    if (type(l) == types.StringType
                        and absuri_match(l) is not None):
                        if self.status==300:
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

    _wrote=None

    def _cookie_list(self):
        cookie_list=[]
        for name, attrs in self.cookies.items():

            # Note that as of May 98, IE4 ignores cookies with
            # quoted cookie attr values, so only the value part
            # of name=value pairs may be quoted.

            cookie='Set-Cookie: %s="%s"' % (name, attrs['value'])
            for name, v in attrs.items():
                name=name.lower()
                if name=='expires': cookie = '%s; Expires=%s' % (cookie,v)
                elif name=='domain': cookie = '%s; Domain=%s' % (cookie,v)
                elif name=='path': cookie = '%s; Path=%s' % (cookie,v)
                elif name=='max_age': cookie = '%s; Max-Age=%s' % (cookie,v)
                elif name=='comment': cookie = '%s; Comment=%s' % (cookie,v)
                elif name=='secure' and v: cookie = '%s; Secure' % cookie
            cookie_list.append(cookie)

        # Should really check size of cookies here!
        
        return cookie_list

    def __str__(self,
                html_search=re.compile('<html>',re.I).search,
                ):
        if self._wrote: return ''       # Streaming output was used.

        headers=self.headers
        body=self.body

        if not headers.has_key('content-length') and \
                not headers.has_key('transfer-encoding'):
            self.setHeader('content-length',len(body))

        # ugh - str(content-length) could be a Python long, which will
        # produce a trailing 'L' :( This can go away when we move to
        # Python 2.0...
        content_length= headers.get('content-length', None)
        if type(content_length) is LongType:
            str_rep=str(content_length)
            if str_rep[-1:]=='L':
                str_rep=str_rep[:-1]
                self.setHeader('content-length', str_rep)

        headersl=[]
        append=headersl.append

        # status header must come first.
        append("Status: %s" % headers.get('status', '200 OK'))
        append("X-Powered-By: Zope (www.zope.org), Python (www.python.org)")
        if headers.has_key('status'):
            del headers['status']
        for key, val in headers.items():
            if key.lower()==key:
                # only change non-literal header names
                key="%s%s" % (key[:1].upper(), key[1:])
                start=0
                l=key.find('-',start)
                while l >= start:
                    key="%s-%s%s" % (key[:l],key[l+1:l+2].upper(),key[l+2:])
                    start=l+1
                    l=key.find('-',start)
            append("%s: %s" % (key, val))
        if self.cookies:
            headersl=headersl+self._cookie_list()
        headersl[len(headersl):]=[self.accumulated_headers, body]
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
            self._wrote=1
            self.stdout.flush()

        self.stdout.write(data)


