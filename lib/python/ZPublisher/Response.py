#!/usr/local/bin/python 
# $What$

__doc__='''CGI Response Output formatter

$Id: Response.py,v 1.28 1998/03/13 22:13:35 jim Exp $'''
#     Copyright 
#
#       Copyright 1996 Digital Creations, L.C., 910 Princess Anne
#       Street, Suite 300, Fredericksburg, Virginia 22401 U.S.A. All
#       rights reserved.  Copyright in this software is owned by DCLC,
#       unless otherwise indicated. Permission to use, copy and
#       distribute this software is hereby granted, provided that the
#       above copyright notice appear in all copies and that both that
#       copyright notice and this permission notice appear. Note that
#       any product, process or technology described in this software
#       may be the subject of other Intellectual Property rights
#       reserved by Digital Creations, L.C. and are not licensed
#       hereunder.
#
#     Trademarks 
#
#       Digital Creations & DCLC, are trademarks of Digital Creations, L.C..
#       All other trademarks are owned by their respective companies. 
#
#     No Warranty 
#
#       The software is provided "as is" without warranty of any kind,
#       either express or implied, including, but not limited to, the
#       implied warranties of merchantability, fitness for a particular
#       purpose, or non-infringement. This software could include
#       technical inaccuracies or typographical errors. Changes are
#       periodically made to the software; these changes will be
#       incorporated in new editions of the software. DCLC may make
#       improvements and/or changes in this software at any time
#       without notice.
#
#     Limitation Of Liability 
#
#       In no event will DCLC be liable for direct, indirect, special,
#       incidental, economic, cover, or consequential damages arising
#       out of the use of or inability to use this software even if
#       advised of the possibility of such damages. Some states do not
#       allow the exclusion or limitation of implied warranties or
#       limitation of liability for incidental or consequential
#       damages, so the above limitation or exclusion may not apply to
#       you.
#  
#
# If you have questions regarding this software,
# contact:
#
#   Digital Creations, info@Digicool.com
#   (540) 371-6909
# 
__version__='$Revision: 1.28 $'[11:-2]

import string, types, sys, regex, regsub
from string import find, rfind, lower, upper, strip, split, join

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

end_of_header_re=regex.compile('</head>',regex.casefold)

absuri_re=regex.compile("[a-zA-Z0-9+.-]+:[^\0- \"\#<>]+\(#[^\0- \"\#<>]*\)?")

bogus_str=regex.compile(" [a-fA-F0-9]+>$")
accumulate_header={'set-cookie': 1}.has_key

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

    def setBody(self, body, title=''):
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
	    bogus_str.search(body) > 0):
	    raise 'NotFound', (
		"Sorry, the requested document does not exist.<p>"
		"\n<!--\n%s\n-->" % body[1:-1])
	    
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
		   base_re=regex.compile('\(<base[\0- ]+[^>]+>\)',
					 regex.casefold)
		   ):
        if (self.headers.has_key('content-type') and
	    self.headers['content-type']!='text/html'): return

	if self.base:
	    body=self.body
	    if body:
		e=end_of_header_re.search(body)
		if e >= 0:
		    b=base_re.search(body) 
		    if b < 0:
			self.body=('%s\t<base href="%s">\n%s' %
				   (body[:e],self.base,body[e:]))

    def appendCookie(self, name, value):
	'''\
	Returns an HTTP header that sets a cookie on cookie-enabled
	browsers with a key "name" and value "value". If a value for the
	cookie has previously been set in the response object, the new
	value is appended to the old one separated by a colon. '''
	self.setCookie(name,value)

    def expireCookie(self, name):
	'''\
	Cause an HTTP cookie to be removed from the browser
	
	The response will include an HTTP header that will remove the cookie
	corresponding to "name" on the client, if one exists. This is
	accomplished by sending a new cookie with an expiration date
	that has already passed. '''
	self.setCookie(name,'deleted', max_age=0)

    def setCookie(self,name,value,**kw):
	'''\
	Set an HTTP cookie on the browser

	The response will include an HTTP header that sets a cookie on
	cookie-enabled browsers with a key "name" and value
	"value". This overwrites any previously set value for the
	cookie in the Response object.
	'''
	cookies=self.cookies
	if cookies.has_key(name): cookie=cookies[name]
	else: cookie=cookies[name]={}

	for k, v in kw.items(): cookie[k]=v
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
		  character_entities=(
		      (regex.compile('&'), '&amp;'),
		      (regex.compile("<"), '&lt;' ),
		      (regex.compile(">"), '&gt;' ),
		      (regex.compile('"'), '&quot;'))): #"
	for re,name in character_entities:
	    text=regsub.gsub(re,name,text)
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
	sys.exc_type,sys.exc_value,sys.exc_traceback=etype,value,tb
	return result

    def _traceback(self,t,v,tb):
	tb=self.format_exception(t,v,tb,200)
	tb=join(tb,'\n')
	tb=self.quoteHTML(tb)
	return "\n<!--\n%s\n-->" % tb

    def redirect(self, location):
	"""Cause a redirection without raising an error"""
	self.status=302
	headers=self.headers
	headers['status']='302 Moved Temporarily'
	headers['location']=location
	return location

    def exception(self, fatal=0):
	t,v,tb=sys.exc_type, sys.exc_value,sys.exc_traceback
	stb=tb

	# Abort running transaction, if any:
	try: get_transaction().abort()
	except: pass

	try:
	    # Try to capture exception info for bci calls
	    et=regsub.gsub('\n',' ',str(t))
            ev=regsub.gsub('\n',' ',str(v))
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
	    if type(v) == types.StringType and absuri_re.match(v) >= 0:
		if self.status==300: self.setStatus(302)
		self.setHeader('location', v)
		tb=None
		return self
	    else:
		try:
		    l,b=v
		    if type(l) == types.StringType and absuri_re.match(l) >= 0:
			if self.status==300: self.setStatus(302)
			self.setHeader('location', l)
			self.setBody(b)
			tb=None
			return self
		except: pass

	b=v
	if fatal:
	    if t is SystemExit and v==0:
		tb=self.setBody(
		    (str(t),
		    'This application has exited normally.<p>'
		     + self._traceback(t,v,tb)))
	    else:
		tb=self.setBody(
		    (str(t),
		    'Sorry, a SERIOUS APPLICATION ERROR occurred.<p>'
		     + self._traceback(t,v,tb)))

	elif type(b) is not types.StringType or regex.search('[a-zA-Z]>',b) < 0:
	    tb=self.setBody(
		(str(t),
		 'Sorry, an error occurred.<p>'
		 + self._traceback(t,v,tb)))

	elif self.isHTML(b):
	    tb=self.setBody(b+self._traceback(t,v,tb))
	else:
	    tb=self.setBody((str(t),b+self._traceback(t,v,tb)))

	return tb

    _wrote=None

    def _cookie_list(self):
	cookie_list=[]
	for name, attrs in self.cookies.items():

            cookie='set-cookie: %s="%s"' % (name,attrs['value'])
	    for name, v in attrs.items():
		if name=='expires': cookie = '%s; Expires="%s"' % (cookie,v)
		elif name=='domain': cookie = '%s; Domain="%s"' % (cookie,v)
		elif name=='path': cookie = '%s; Path=%s' % (cookie,v)
		elif name=='max_age': cookie = '%s; Max-Age="%s"' % (cookie,v)
		elif name=='comment': cookie = '%s; Comment="%s"' % (cookie,v)
		elif name=='secure': cookie = '%s; Secure' % cookie
		#elif name!='value':
		#    raise ValueError, (
		#	'Invalid cookie attribute, <em>%s</em>' % name)
	    cookie_list.append(cookie)
	return cookie_list

    def __str__(self):
	if self._wrote: return ''	# Streaming output was used.

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
	    if isHTML and end_of_header_re.search(self.body) < 0:
		htmlre=regex.compile('<html>',regex.casefold)
		lhtml=htmlre.search(body)
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
	return 'CGIResponse(%s)' % `self.body`
	

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
	if end_of_header_re.search(self.body) >= 0:
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
	    write('\n\n')
	    write(body)
