#!/bin/env python
#
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
# If you have questions regarding this software, contact:
#
#   Digital Creations, L.C.
#   910 Princess Ann Street
#   Fredericksburge, Virginia  22401
#
#   info@digicool.com
#
#   (540) 371-6909
# 
__doc__='''bobo call interface


$Id: Client.py,v 1.2 1997/03/27 18:10:47 jim Exp $'''
__version__='$Revision: 1.2 $'[11:-2]

import regex
from httplib import HTTP
from time import time
from base64 import encodestring
from urllib import urlopen, quote
from string import split,atoi,join,rfind
from regsub import gsub

def marshal_float(n,f): return '%s:float=%s' % (n,f)
def marshal_int(n,f):   return '%s:int=%s' % (n,f)
def marshal_long(n,f):  return ('%s:long=%s' % (n,f))[:-1]

sample_regex=regex.compile('')
def marshal_regex(n,r):
    if r.translate is sample_regex.translate:
	t='Regex'
    elif r.translate is regex.casefold:
	t='regex'
    else:
	raise ValueError, 'regular expression used unsupported translation'
    return "%s:%s=%s" % (n,t,quote(r.givenpat))

def marshal_list(n,l):
    return join(map(lambda v, n=n: "%s:list=%s" % (n,quote(v)),l),'&')

def marshal_tuple(n,l):
    return join(map(lambda v, n=n: "%s:tuple=%s" % (n,quote(v)),l),'&')
    
    

type2marshal={
    type(1.0): 			marshal_float,
    type(1): 			marshal_int,
    type(1L): 			marshal_long,
    type(regex.compile('')): 	marshal_regex,
    type([]): 			marshal_list,
    type(()): 			marshal_tuple,
    }

urlregex=regex.compile('http://\([^:/]+\)\(:[0-9]+\)?\(/.+\)', regex.casefold)

NotFound='bci.NotFound'
ServerError='bci.ServerError

def ErrorTypes(code):
    if code >= 400 and code < 500: return NotFound
    if code >= 500 and code < 600: return ServerError
    return 'HTTP_Error_%s' % code

class BoboFunction:
    '''Make bobo-published callable objects look like functions
    '''
    username=password=''

    def __init__(self,url,*args):
	while url[-1:]=='/': url=url[:-1]
	self.url=url
	self.func_name=self.__name__=url[rfind(url,'/')+1:]
	self.func_defaults=()
	
	self.args=args
	if urlregex.match(url) >= 0:
	    host,port,rurl=urlregex.group(1,2,3)
	    if port: port=atoi(port[1:])
	    else: port=80
	    self.host=host
	    self.port=port
	    self.rurl=rurl
	else: raise ValueError, url

    def __call__(self,*args,**kw):

	# get positional arguments
	akw={}
	for i in range(len(args)):
	    try:
		k=self.args[i]
		if kw.has_key(k): raise TypeError, 'keyword parameter redefined'
		akw[k]=args[i]
	    except IndexError: TypeError, 'too many arguments'

	query=[]
	for k,v in akw.items()+kw.items():
	    try:
		q=type2marshal[type(v)]
		q=q(k,v)
		query.append(q)
	    except KeyError:
		q='='+quote(v)
		query.append(quote(k)+q)
	query=join(query,'&')


	# Make http request:
	h=HTTP()
	h.connect(self.host, self.port)
	h.putrequest('POST', self.rurl)
	h.putheader('Content-Type', 'application/x-www-form-urlencoded')
	h.putheader('Content-Length', str(len(query)))
	if self.username and self.password:
	    credentials = encodestring('%s:%s' % (self.username,self.password))
	    credentials=gsub('\012','',credentials)
	    h.putheader('Authorization',"Basic %s" % credentials)
	h.endheaders()
	h.send(query)
	errcode,errmsg,headers=h.getreply()
	response=h.getfile().read()
	__traceback_info__=query, self.__dict__,errcode,errmsg,response
	if errcode != 200:
	    raise ErrorTypes(errcode), errmsg
	return response
	    
	

def main():
    # The "main" program for this module
    f=BoboFunction('http://ninny.digicool.com:8081'
		   '/projects/PyDB/customer/cgi-bin/Client.cgi/Queries'
		   '/ModuleParts/query', 'ModuleID', 'output-delimiter')

    print f('ABM', '\t')


if __name__ == "__main__": main()

#
# $Log: Client.py,v $
# Revision 1.2  1997/03/27 18:10:47  jim
# Fixed bugs.
#
# Revision 1.1  1997/03/27 17:13:54  jim
# *** empty log message ***
#
# Revision 1.5  1997/03/20 16:58:00  jim
# Pauls change
#
# Revision 1.4  1997/02/28 19:53:49  jim
# Fixed numerous bugs.
#
# Revision 1.3  1997/02/27 19:04:00  jim
# *** empty log message ***
#
# Revision 1.2  1997/02/27 19:00:33  jim
# *** empty log message ***
#
# Revision 1.1  1997/02/27 13:35:06  jim
# *** empty log message ***
#
#
