##############################################################################
#
# Zope Public License (ZPL) Version 0.9.4
# ---------------------------------------
# 
# Copyright (c) Digital Creations.  All rights reserved.
# 
# Redistribution and use in source and binary forms, with or
# without modification, are permitted provided that the following
# conditions are met:
# 
# 1. Redistributions in source code must retain the above
#    copyright notice, this list of conditions, and the following
#    disclaimer.
# 
# 2. Redistributions in binary form must reproduce the above
#    copyright notice, this list of conditions, and the following
#    disclaimer in the documentation and/or other materials
#    provided with the distribution.
# 
# 3. Any use, including use of the Zope software to operate a
#    website, must either comply with the terms described below
#    under "Attribution" or alternatively secure a separate
#    license from Digital Creations.
# 
# 4. All advertising materials, documentation, or technical papers
#    mentioning features derived from or use of this software must
#    display the following acknowledgement:
# 
#      "This product includes software developed by Digital
#      Creations for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
# 5. Names associated with Zope or Digital Creations must not be
#    used to endorse or promote products derived from this
#    software without prior written permission from Digital
#    Creations.
# 
# 6. Redistributions of any form whatsoever must retain the
#    following acknowledgment:
# 
#      "This product includes software developed by Digital
#      Creations for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
# 7. Modifications are encouraged but must be packaged separately
#    as patches to official Zope releases.  Distributions that do
#    not clearly separate the patches from the original work must
#    be clearly labeled as unofficial distributions.
# 
# Disclaimer
# 
#   THIS SOFTWARE IS PROVIDED BY DIGITAL CREATIONS ``AS IS'' AND
#   ANY EXPRESSED OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
#   LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND
#   FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.  IN NO EVENT
#   SHALL DIGITAL CREATIONS OR ITS CONTRIBUTORS BE LIABLE FOR ANY
#   DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
#   CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
#   PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
#   DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#   ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
#   LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING
#   IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF
#   THE POSSIBILITY OF SUCH DAMAGE.
# 
# Attribution
# 
#   Individuals or organizations using this software as a web site
#   must provide attribution by placing the accompanying "button"
#   and a link to the accompanying "credits page" on the website's
#   main entry point.  In cases where this placement of
#   attribution is not feasible, a separate arrangment must be
#   concluded with Digital Creations.  Those using the software
#   for purposes other than web sites must provide a corresponding
#   attribution in locations that include a copyright using a
#   manner best suited to the application environment.
# 
# This software consists of contributions made by Digital
# Creations and many individuals on behalf of Digital Creations.
# Specific attributions are listed in the accompanying credits
# file.
# 
##############################################################################
'''CGI Response Output formatter

$Id: Response.py,v 1.45 1998/12/04 20:15:34 jim Exp $'''
__version__='$Revision: 1.45 $'[11:-2]

import string, types, sys, regex
from string import find, rfind, lower, upper, strip, split, join, translate
from types import StringType, InstanceType

nl2sp=string.maketrans('\n',' ')

status_reasons={
    200: 'OK',
    201: 'Created',
    202: 'Accepted',
    204: 'No Content',
    300: 'Multiple Choices',
    301: 'Moved Permanently',
    302: 'Moved Temporarily',
    304: 'Not Modified',
    400: 'Bad Request',
    401: 'Unauthorized',
    403: 'Forbidden',
    404: 'Not Found',
    500: 'Internal Error',
    501: 'Not Implemented',
    502: 'Bad Gateway',
    503: 'Service Unavailable',
    }

status_codes={
    'ok': 200,
    'created':201,
    'accepted':202,
    'nocontent':204,
    'multiplechoices':300,
    'redirect':300,
    'movedpermanently':301,
    'movedtemporarily':302,
    'notmodified':304,
    'badrequest':400,
    'unauthorized':401,
    'forbidden':403,
    'notfound':404,
    'internalerror':500,
    'notimplemented':501,
    'badgateway':502,
    'serviceunavailable':503,
    'no content':204,
    'multiple choices':300,
    'moved permanently':301,
    'moved temporarily':302,
    'not modified':304,
    'bad request':400,
    'not found':404,
    'internal error':500,
    'not implemented':501,
    'bad gateway':502,
    'service unavailable':503,
    200: 200,
    201: 201,
    202: 202,
    204: 204,
    301: 301,
    302: 302,
    304: 304,
    400: 400,
    401: 401,
    403: 403,
    404: 404,
    500: 500,
    501: 501,
    502: 502,
    503: 503,

    # Map standard python exceptions to status codes:
    'accesserror':500,
    'attributeerror':500,
    'conflicterror':500,
    'eoferror':500,
    'ioerror':500,
    'importerror':500,
    'indexerror':500,
    'keyerror':503,
    'memoryerror':500,
    'nameerror':503,
    'overflowerror':500,
    'runtimeerror':500,
    'syntaxerror':500,
    'systemerror':500,
    'typeerror':500,
    'valueerror':500,
    'zerodivisionerror':500,
    }

end_of_header_search=regex.compile('</head>',regex.casefold).search

accumulate_header={'set-cookie': 1}.has_key

_tbopen, _tbclose = '<!--', '-->'

class Response:
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
            headers['status']="200 OK"      
        else: self.setStatus(status)
        self.base=''
        if body: self.setBody(body)
        self.cookies={}
        self.stdout=stdout
        self.stderr=stderr
    
    def setStatus(self, status, reason=None):
        '''\
        Sets the HTTP status code of the response; the argument may
        either be an integer or a string from { OK, Created, Accepted,
        NoContent, MovedPermanently, MovedTemporarily,
        NotModified, BadRequest, Unauthorized, Forbidden,
        NotFound, InternalError, NotImplemented, BadGateway,
        ServiceUnavailable } that will be converted to the correct
        integer value. '''
        if type(status) is types.StringType:
            status=lower(status)
        if status_codes.has_key(status): status=status_codes[status]
        else: status=500
        self.status=status
        if reason is None:
            if status_reasons.has_key(status): reason=status_reasons[status]
            else: reason='Unknown'
        self.setHeader('Status', "%d %s" % (status,str(reason)))

    def setHeader(self, name, value):
        '''\
        Sets an HTTP return header "name" with value "value", clearing
        the previous value set for the header, if one exists. '''
        n=lower(name)
        if accumulate_header(n):
            self.accumulated_headers=(
                "%s%s: %s\n" % (self.accumulated_headers, name, value))
        else:
            self.headers[n]=value

    __setitem__=setHeader

    def setBody(self, body, title='',
                bogus_str_search=regex.compile(" [a-fA-F0-9]+>$").search,
                ):
        '''\
        Set the body of the response
        
        Sets the return body equal to the (string) argument "body". Also
        updates the "content-length" return header.

        You can also specify a title, in which case the title and body
        will be wrapped up in html, head, title, and body tags.

        If the body is a 2-element tuple, then it will be treated
        as (title,body)
        '''
        if type(body) is types.TupleType:
            title,body=body

        if type(body) is not types.StringType:
            if hasattr(body,'asHTML'):
                body=body.asHTML()

        body=str(body)
        l=len(body)
        if (find(body,'>')==l-1 and body[:1]=='<' and l < 200 and
            bogus_str_search(body) > 0):
            raise 'NotFound', (
                "Sorry, the requested document does not exist.<p>"
                "\n%s\n%s\n%s" % (_tbopen, body[1:-1], _tbclose))
            
        if(title):
            self.body=('<html>\n<head>\n<title>%s</title>\n</head>\n'
                       '<body>\n%s\n</body>\n</html>'
                       % (str(title),str(body)))
        else:
            self.body=str(body)
        self.insertBase()
        return self

    def getStatus(self):
        'Returns the current HTTP status code as an integer. '
        return self.status

    def setBase(self,base):
        'Set the base URL for the returned document.'
        if base[-1:] != '/': base=base+'/'
        self.base=base
        self.insertBase()

    def insertBase(self,
                   base_re_search=regex.compile('\(<base[\0- ]+[^>]+>\)',
                                                regex.casefold).search
                   ):
        if (self.headers.has_key('content-type') and
            self.headers['content-type']!='text/html'): return

        if self.base:
            body=self.body
            if body:
                e=end_of_header_search(body)
                if e >= 0:
                    b=base_re_search(body) 
                    if b < 0:
                        self.body=('%s\t<base href="%s">\n%s' %
                                   (body[:e],self.base,body[e:]))

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
        apply(Response.setCookie, (self, name, 'deleted'), dict)

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
         headers=self.headers
         if headers.has_key(name): return headers[name]

    def __getitem__(self, name):
        'Get the value of an output header'
        return self.headers[name]

    def getBody(self):
        'Returns a string representing the currently set body. '
        return self.body

    def appendHeader(self, name, value, delimiter=","):
        '''\
        Append a value to a cookie
        
        Sets an HTTP return header "name" with value "value",
        appending it following a comma if there was a previous value
        set for the header. '''
        headers=self.headers
        if headers.has_key(name):
            h=self.header[name]
            h="%s%s\n\t%s" % (h,delimiter,value)
        else: h=value
        self.setHeader(name,h)

    def isHTML(self,str):
        return lower(strip(str)[:6]) == '<html>' or find(str,'</') > 0

    def quoteHTML(self,text,
                  subs={'&':'&amp;', "<":'&lt;', ">":'&gt;', '\"':'&quot;'}
                  ):
        for ent in '&<>\"':
            if find(text, ent) >= 0:
                text=join(split(text,ent),subs[ent])

        return text
         

    def format_exception(self,etype,value,tb,limit=None):
        import traceback
        result=['Traceback (innermost last):']
        if limit is None:
                if hasattr(sys, 'tracebacklimit'):
                        limit = sys.tracebacklimit
        n = 0
        while tb is not None and (limit is None or n < limit):
                f = tb.tb_frame
                lineno = tb.tb_lineno
                co = f.f_code
                filename = co.co_filename
                name = co.co_name
                locals=f.f_locals
                result.append('  File %s, line %d, in %s'
                              % (filename,lineno,name))
                try: result.append('    (Object: %s)' %
                                   locals[co.co_varnames[0]].__name__)
                except: pass
                try: result.append('    (Info: %s)' %
                                   str(locals['__traceback_info__']))
                except: pass
                tb = tb.tb_next
                n = n+1
        result.append(join(traceback.format_exception_only(etype, value),
                           ' '))
        return result

    def _traceback(self,t,v,tb):
        tb=self.format_exception(t,v,tb,200)
        tb=join(tb,'\n')
        tb=self.quoteHTML(tb)
        return "\n%s\n%s\n%s" % (_tbopen, tb, _tbclose)

    def redirect(self, location):
        """Cause a redirection without raising an error"""
        self.status=302
        headers=self.headers
        headers['status']='302 Moved Temporarily'
        headers['location']=location
        return location

    def exception(self, fatal=0, info=None,
                  absuri_match=regex.compile(
                      "^"
                      "\(/\|\([a-zA-Z0-9+.-]+:\)\)"
                      "[^\000- \"\\#<>]*"
                      "\\(#[^\000- \"\\#<>]*\\)?"
                      "$"
                      ).match,
                  tag_search=regex.compile('[a-zA-Z]>').search,
                  ):
        if type(info) is type(()) and len(info)==3: t,v,tb = info
        elif hasattr(sys, 'exc_info'): t,v,tb = sys.exc_info()
        else: t,v,tb = sys.exc_type, sys.exc_value, sys.exc_traceback

        stb=tb

        # Abort running transaction, if any:
        try: get_transaction().abort()
        except: pass

        try:
            # Try to capture exception info for bci calls
            et=translate(str(t),nl2sp)
            ev=translate(str(v),nl2sp)
            # Get the tb tail, which is the interesting part:
            while tb.tb_next is not None: tb=tb.tb_next
            el=str(tb.tb_lineno)
            ef=str(tb.tb_frame.f_code.co_filename)
            if find(ev,'<html>') >= 0: ev='bobo exception'
            self.setHeader('bobo-exception-type',et)
            self.setHeader('bobo-exception-value',ev[:255])
            self.setHeader('bobo-exception-file',ef)
            self.setHeader('bobo-exception-line',el)

        except:
            # Dont try so hard that we cause other problems ;)
            pass

        tb=stb
        stb=None
        self.setStatus(t)
        if self.status >= 300 and self.status < 400:
            if type(v) == types.StringType and absuri_match(v) >= 0:
                if self.status==300: self.setStatus(302)
                self.setHeader('location', v)
                tb=None
                return self
            else:
                try:
                    l,b=v
                    if type(l) == types.StringType and absuri_match(l) >= 0:
                        if self.status==300: self.setStatus(302)
                        self.setHeader('location', l)
                        self.setBody(b)
                        tb=None
                        return self
                except: pass

        b=v
        if isinstance(b,Exception): b=str(b)

        if fatal:
            if t is SystemExit and v.code==0:
                tb=self.setBody(
                    (str(t),
                    'This application has exited normally.<p>'
                     + self._traceback(t,v,tb)))
            else:
                tb=self.setBody(
                    (str(t),
                    'Sorry, a SERIOUS APPLICATION ERROR occurred.<p>'
                     + self._traceback(t,v,tb)))

        elif type(b) is not types.StringType or tag_search(b) < 0:
            tb=self.setBody(
                (str(t),
                 'Sorry, an error occurred.<p>'
                 + self._traceback(t,v,tb)))

        elif self.isHTML(b):
            tb=self.setBody(b+self._traceback(t,'(see above)',tb))
        else:
            tb=self.setBody((str(t),b+self._traceback(t,'(see above)',tb)))

        return tb

    _wrote=None

    def _cookie_list(self):
        cookie_list=[]
        for name, attrs in self.cookies.items():

            # Note that as of May 98, IE4 ignores cookies with
            # quoted cookie attr values, so only the value part
            # of name=value pairs may be quoted.

            cookie='Set-Cookie: %s="%s"' % (name, attrs['value'])
            for name, v in attrs.items():
                name=lower(name)
                if name=='expires': cookie = '%s; Expires=%s' % (cookie,v)
                elif name=='domain': cookie = '%s; Domain=%s' % (cookie,v)
                elif name=='path': cookie = '%s; Path=%s' % (cookie,v)
                elif name=='max_age': cookie = '%s; Max-Age=%s' % (cookie,v)
                elif name=='comment': cookie = '%s; Comment=%s' % (cookie,v)
                elif name=='secure': cookie = '%s; Secure' % cookie
            cookie_list.append(cookie)

        # Should really check size of cookies here!
        
        return cookie_list

    def __str__(self,
                html_search=regex.compile('<html>',regex.casefold).search,
                ):
        if self._wrote: return ''       # Streaming output was used.

        headers=self.headers
        body=self.body
        if body:
            isHTML=self.isHTML(body)
            if not headers.has_key('content-type'):
                if isHTML:
                    c='text/html'
                else:
                    c='text/plain'
                self.setHeader('content-type',c)
            else:
                isHTML = headers['content-type']=='text/html'
            if isHTML and end_of_header_search(self.body) < 0:
                lhtml=html_search(body)
                if lhtml >= 0:
                    lhtml=lhtml+6
                    body='%s<head></head>\n%s' % (body[:lhtml],body[lhtml:])
                else:
                    body='<html><head></head>\n' + body
                self.setBody(body)
                body=self.body
                    
            if not headers.has_key('content-length'):
                self.setHeader('content-length',len(body))
                

        if not headers.has_key('content-type') and self.status == 200:
            self.setStatus('nocontent')

        headersl=[]
        append=headersl.append

        # Make sure status comes out first!
        try:
            v=headers['status']
            del headers['status']
        except: v="200 OK"
        append("Status: "+v)

        for k,v in headers.items():

            k=upper(k[:1])+k[1:]

            start=0
            l=find(k,'-',start)
            while l >= start:
                k="%s-%s%s" % (k[:l],upper(k[l+1:l+2]),k[l+2:])
                start=l+1
                l=find(k,'-',start)
            append("%s: %s" % (k,v))

        if self.cookies:
            headersl=headersl+self._cookie_list()
        headersl[len(headersl):]=[self.accumulated_headers,body]

        return join(headersl,'\n')

    def __repr__(self):
        return 'Response(%s)' % `self.body`
        

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
        headers=self.headers
        if headers.has_key('content-length'):
            del headers['content-length']
        if not self.headers.has_key('content-type'):
            self.setHeader('content-type', 'text/html')
        self.insertBase()
        body=self.body
        self.body=''
        self.write=write=self.stdout.write
        try: self.flush=self.stdout.flush
        except: pass
        write(str(self))
        self._wrote=1
        write(body)
