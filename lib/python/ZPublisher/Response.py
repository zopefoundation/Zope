#!/usr/local/bin/python 
# $What$

__doc__='''CGI Response Output formatter

$Id: Response.py,v 1.1 1996/06/17 18:57:18 jfulton Exp $'''
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
# Revision 1.1  1996/06/17 18:57:18  jfulton
# Almost initial version.
#
#
# 
__version__='$Revision: 1.1 $'[11:-2]

import string, types, sys

status_codes={
    'ok': 200,
    'created':201,
    'accepted':202,
    'nocontent':204,
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
    'accesserror':403,
    'attributeerror':501,
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


class Response:
    def __init__(self,body='',status=200,headers=None):
	'''\
	Creates a new response. In effect, the constructor calls
	"self.setBody(body); self.setStatus(status); for name in
	headers.keys(): self.setHeader(name, headers[name])"'''
	if not headers:
	    headers={}
	self.headers=headers
	self.setStatus(status)
	self.setBody(body)
    
    def setStatus(self,status):
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
	self.setHeader('status',status)

    def setHeader(self, name, value):
	'''\
	Sets an HTTP return header "name" with value "value", clearing
	the previous value set for the header, if one exists. '''
	self.headers[name]=value

    def setBody(self, body, title=''):
	'''\
	Sets the return body equal to the (string) argument "body". Also
	updates the "content-length" return header. '''
	if type(body)==types.TupleType:
	    title,body=body
	if(title):
	    self.body=('<html>\n<head>\n<title>%s</title>\n</head>\n'
		       '<body>\n%s\n</body>\n</html>'
		       % (str(title),str(body)))
	else:
	    self.body=str(body)

    def getStatus(self):
	'Returns the current HTTP status code as an integer. '
	return self.status

    def appendCookie(self, name, value):
	'''\
	Returns an HTTP header that sets a cookie on cookie-enabled
	browsers with a key "name" and value "value". If a value for the
	cookie has previously been set in the response object, the new
	value is appended to the old one separated by a colon. '''

    def expireCookie(self, name):
	'''\
	Returns an HTTP header that will remove the cookie
	corresponding to "name" on the client, if one exists. This is
	accomplished by sending a new cookie with an expiration date
	that has already passed. '''

    def setCookie(self, name, value):
	'''\
	Returns an HTTP header that sets a cookie on cookie-enabled
	browsers with a key "name" and value "value". This overwrites
	any previously set value for the cookie in the Response object. '''

    def appendBody(self, body):
	''
	self.setBody(self.getBody() + body)

    def getHeader(self, name):
	 '''\
	 Returns the value associated with a HTTP return header, or
	 "None" if no such header has been set in the response yet. '''
	 return self.headers[name]

    def getBody(self):
	'Returns a string representing the currently set body. '
	return self.body

    def appendHeader(self, name, value, delimiter=","):
	'''\
	Sets an HTTP return header "name" with value "value",
	appending it following a comma if there was a previous value
	set for the header. '''
	try:
	    h=self.header[name]
	    h="%s%s\n\t%s" % (h,delimiter,value)
	except: h=value
	self.setHeader(name,h)

    def __str__(self):
	headers=self.headers
	body=self.body
	if body:
	    if not headers.has_key('content-type'):
		if len(body) > 6 and string.lower(body[:6]) == '<html>':
		    c='text/html'
		else:
		    c='text/plain'
		self.setHeader('content-type',c)
	    if not headers.has_key('content-length'):
		self.setHeader('content-length',len(body))
	
	headers=map(lambda k,d=headers: "%s: %s" % (k,d[k]), headers.keys())
	if body: headers[len(headers):]=['',body]

	return string.joinfields(headers,'\n')

def ExceptionResponse(body="Sorry, an error occurred"):
    import traceback
    t,v,tb=sys.exc_type, sys.exc_value,sys.exc_traceback
    body=("%s<p>\n<!--\n%s\n-->" %
	  (body,
	   string.joinfields(traceback.format_exception(t,v,tb,200),'\n')
	   ))
    return Response(('Error',body),t)
    # return Response('',t)

def main():
    print Response('hello world')
    print '-' * 70
    print Response(('spam title','spam spam spam'))
    print '-' * 70
    try:
	1.0/0.0
    except: print ExceptionResponse()


if __name__ == "__main__": main()
