#!/usr/local/bin/python 
# $What$

__doc__='''CGI Response Output formatter

$Id: Response.py,v 1.5 1996/07/10 22:45:57 jfulton Exp $'''
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
#   Jim Fulton, jim@digicool.com
#
#   (540) 371-6909
#
# $Log: Response.py,v $
# Revision 1.5  1996/07/10 22:45:57  jfulton
# Made exception handling fussier about exception values.
# Now the value must contain white space to be considered an error
# message.
#
# Revision 1.4  1996/07/08 20:34:09  jfulton
# Many changes, including:
#
#   - Butter realm management
#   - Automatic type conversion
#   - Improved documentation
#   - ...
#
# Revision 1.3  1996/07/03 18:25:50  jfulton
# Added support for file upload via newcgi module.
#
# Revision 1.2  1996/07/01 11:51:54  jfulton
# Updated code to:
#
#   - Provide a first cut authentication.authorization scheme
#   - Fix several bugs
#   - Provide better error messages
#   - Provide automagic insertion of base
#   - Support Fast CGI module publisher.
#
# Revision 1.1  1996/06/17 18:57:18  jfulton
# Almost initial version.
#
#
# 
__version__='$Revision: 1.5 $'[11:-2]

import string, types, sys, regex

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
base_re=regex.compile('<base',regex.casefold)

absuri_re=regex.compile("[a-zA-Z0-9+.-]+:[^\0- \"\#<>]+\(#[^\0- \"\#<>]*\)?")

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
    """
    

    def __init__(self,body='',status=200,headers=None,
		 stdout=sys.stdout, stderr=sys.stderr,):
	'''\
	Creates a new response. In effect, the constructor calls
	"self.setBody(body); self.setStatus(status); for name in
	headers.keys(): self.setHeader(name, headers[name])"'''
	if not headers:
	    headers={}
	self.headers=headers
	self.setStatus(status)
	self.base=''
	self.setBody(body)
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
	    status=string.lower(status)
	try: status=status_codes[status]
	except: status=500
	self.status=status
	if reason is None:
	    try: reason=status_reasons[status]
	    except: reason='Unknown'
	self.setHeader('Status', "%d %s" % (status,str(reason)))

    def setHeader(self, name, value):
	'''\
	Sets an HTTP return header "name" with value "value", clearing
	the previous value set for the header, if one exists. '''
	self.headers[string.lower(name)]=value

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
	if type(body)==types.TupleType:
	    title,body=body
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
	self.base=base
	self.insertBase()

    def insertBase(self):
	if self.base:
	    body=self.body
	    e=end_of_header_re.search(body)
	    if e >= 0 and base_re.search(body) < 0:
		self.body=('%s\t<base href="%s">\n%s' %
			   (body[:e],self.base,body[e:]))

    def appendCookie(self, name, value):
	'''\
	Returns an HTTP header that sets a cookie on cookie-enabled
	browsers with a key "name" and value "value". If a value for the
	cookie has previously been set in the response object, the new
	value is appended to the old one separated by a colon. '''
	try:
	    v,expires,domain,path,secure=self.cookies[name]
	except:
	    v,expires,domain,path,secure='','','','',''
	self.cookies[name]=v+value,expires,domain,path,secure

    def expireCookie(self, name):
	'''\
	Cause an HTTP cookie to be removed from the browser
	
	The response will include an HTTP header that will remove the cookie
	corresponding to "name" on the client, if one exists. This is
	accomplished by sending a new cookie with an expiration date
	that has already passed. '''
	self.cookies[name]='deleted','01-Jan-96 11:11:11 GMT','','',''

    def setCookie(self,name, value=None,
		  expires=None, domain=None, path=None, secure=None):
	'''\
	Set an HTTP cookie on the browser

	The response will include an HTTP header that sets a cookie on cookie-enabled
	browsers with a key "name" and value "value". This overwrites
	any previously set value for the cookie in the Response object. '''
	try: cookie=self.cookies[name]
	except: cookie=('')*5

	def f(a,b):
	    if b is not None: return b
	    return a

	self.cookies[name]=tuple(map(f,cookie,
				     (value,expires,domain,path,secure)
				     )
				 )


    def appendBody(self, body):
	self.setBody(self.getBody() + body)

    def getHeader(self, name):
	 '''\
	 Get a header value
	 
	 Returns the value associated with a HTTP return header, or
	 "None" if no such header has been set in the response
	 yet. '''
	 try: return self.headers[name]
	 except: return None

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
	try:
	    h=self.header[name]
	    h="%s%s\n\t%s" % (h,delimiter,value)
	except: h=value
	self.setHeader(name,h)

    def isHTML(self,str):
	return (string.lower(string.strip(str)[:6]) == '<html>' or
		string.find(str,'</') > 0)

    def _traceback(self,t,v,tb):
	import traceback
	return ("\n<!--\n%s\n-->" %
		string.joinfields(traceback.format_exception(t,v,tb,200),'\n')
		)

    def exception(self):
	t,v,tb=sys.exc_type, sys.exc_value,sys.exc_traceback

	self.setStatus(t)
	if self.status >= 300 and self.status < 400:
	    if type(v) == types.StringType and absuri_re.match(v) >= 0:
		self.setHeader('location', v)
		return self
	    else:
		try:
		    l,b=v
		    if type(l) == types.StringType and absuri_re.match(l) >= 0:
			self.setHeader('location', l)
			self.setBody(b)
			return self
		except: pass

	b=v
	if type(b) is not types.StringType or regex.search(' \t\n',b) < 0:
	    return self.setBody(
		(str(t),
		 'Sorry, an error occurred.<p>'
		 + self._traceback(t,v,tb)))

	if self.isHTML(b): return self.setBody(b+self._traceback(t,v,tb))

	return self.setBody((str(t),b+self._traceback(t,v,tb)))

    _wrote=None

    def _cookie_list(self):
	cookie_list=[]
	for name in self.cookies.keys():
	    value,expires,domain,path,secure=self.cookies[name]
	    cookie='set-cookie: %s=%s' % (name,value)
	    if expires: cookie = "%s; expires=%s" % (cookie,expires)
	    if domain: cookie = "%s; domain=%s" % (cookie,domain)
	    if path: cookie = "%s; path=%s" % (cookie,path)
	    if secure: cookie = cookie+'; secure'
	    cookie_list.append(cookie)
	return cookie_list

    def __str__(self):
	if self._wrote: return ''	# Streaming output was used.

	headers=self.headers
	body=self.body
	if body:
	    if not headers.has_key('content-type'):
		if self.isHTML(body):
		    c='text/html'
		else:
		    c='text/plain'
		self.setHeader('content-type',c)
	    if not headers.has_key('content-length'):
		self.setHeader('content-length',len(body))

	if not headers.has_key('content-type') and self.status == 200:
	    self.setStatus('nocontent')

	headersl=map(lambda k,d=headers: "%s: %s" % (k,d[k]), headers.keys())
	if self.cookies:
	    headersl=headersl+self._cookie_list()
	headersl[len(headersl):]=['',body]

	return string.joinfields(headersl,'\n')

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
	    try: del self.headers['content-length']
	    except: pass
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

def main():
    print Response('hello world')
    print '-' * 70
    print Response(('spam title','spam spam spam'))
    print '-' * 70
    try:
	1.0/0.0
    except: print ExceptionResponse()


if __name__ == "__main__": main()
