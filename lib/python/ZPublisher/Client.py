"""Bobo call interface"""
__version__='$Revision: 1.5 $'[11:-2]

import sys,regex
from httplib import HTTP
from time import time
from base64 import encodestring
from urllib import urlopen, quote
from string import split,atoi,join,rfind,splitfields
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

NotFound     ='bci.NotFound'
InternalError='bci.InternalError'
BadRequest   ='bci.BadRequest'
Unauthorized ='bci.Unauthorized'
ServerError  ='bci.ServerError'
NotAvailable ='bci.NotAvailable'

exceptmap   ={'AccessError'      :AccessError,
	      'AttributeError'   :AttributeError,
	      'BadRequest'       :BadRequest,
	      'ConflictError'    :ConflictError,
	      'EOFError'         :EOFError,
	      'IOError'          :IOError,
	      'ImportError'      :ImportError,
	      'IndexError'       :IndexError,
	      'InternalError'    :InternalError,
	      'KeyError'         :KeyError,
	      'MemoryError'      :MemoryError,
	      'NameError'        :NameError,
	      'NotFound'         :NotFound,
	      'OverflowError'    :OverflowError,
	      'RuntimeError'     :RuntimeError,
	      'ServerError'      :ServerError,
	      'SyntaxError'      :SyntaxError,
	      'SystemError'      :SystemError,
	      'SystemExit'       :SystemExit,
	      'TypeError'        :TypeError,
	      'Unauthorized'     :Unauthorized,
	      'ValueError'       :ValueError,
	      'ZeroDivisionError':ZeroDivisionError}



class RemoteException:
    def __init__(self,etype=None,evalue=None,url=None,query=None,
		 http_code=None, http_msg=None, http_resp=None):
        """Contains information about an exception which
           occurs in a remote method call"""
        self.exc_type    =etype
	self.exc_value   =evalue
        self.url         =url
	self.query       =query
	self.http_code   =http_code
        self.http_message=http_msg
        self.response    =http_resp

    def __repr__(self):
	return '%s\n%s %s for %s' % (self.exc_value,self.http_code,
				     self.http_message,self.url)




class RemoteMethod:
    username=password=''
    def __init__(self,url,*args):
	while url[-1:]=='/': url=url[:-1]
	self.url=url
	self.headers={}
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
	akw={}
	for i in range(len(args)):
	    try:
		k=self.args[i]
		if kw.has_key(k):
		    raise TypeError, 'keyword parameter redefined'
		akw[k]=args[i]
	    except IndexError:
		raise TypeError, 'too many arguments'
	query=[]
	for k,v in akw.items()+kw.items():
	    try: q=type2marshal[type(v)](k,v)
	    except KeyError: q='%s=%s' % (k,quote(v))
	    query.append(q)
	query=join(query,'&')
	try:
	    h=HTTP()
	    h.connect(self.host, self.port)
	    h.putrequest('POST', self.rurl)
	    h.putheader('Content-Type', 'application/x-www-form-urlencoded')
	    h.putheader('Content-Length', str(len(query)))
	    for hn,hv in self.headers.items(): h.putheader(hn,hv)
	    if self.username and self.password:
	        credentials=gsub('\012','',encodestring('%s:%s' % (
		                           self.username,self.password)))
	        h.putheader('Authorization',"Basic %s" % credentials)
	    h.endheaders()
	    h.send(query)
	    ec,em,headers=h.getreply()
	    response     =h.getfile().read()
	except:
	    raise NotAvailable, \
		  RemoteException(NotAvailable,sys.exc_value,self.rurl,query)

	if ec==200: return (headers,response)
	else:
	    try:    v=headers.dict['bobo-exception-value']
	    except: v=ec
	    try:    t=exceptmap[headers.dict['bobo-exception-type']]
	    except:
		if   ec >= 400 and ec < 500: t=NotFound
		elif ec >= 500 and ec < 600: t=ServerError
		else:                        t=NotAvailable
	    raise t, RemoteException(t,v,self.rurl,query,ec,em,response)






Function=RemoteMethod

def ErrorTypes(code):
    if code >= 400 and code < 500: return NotFound
    if code >= 500 and code < 600: return ServerError
    return 'HTTP_Error_%s' % code

class BoboFunction:
    """Make bobo-published callable objects look like functions"""
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
	akw={}
	for i in range(len(args)):
	    try:
		k=self.args[i]
		if kw.has_key(k):
		    raise TypeError, 'keyword parameter redefined'
		akw[k]=args[i]
	    except IndexError:
		raise TypeError, 'too many arguments'

	query=[]
	for k,v in akw.items()+kw.items():
	    try: q=type2marshal[type(v)](k,v)
	    except KeyError: q='%s=%s' % (k,quote(v))
	    query.append(q)
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
	__traceback_info__=query,self.__dict__,errcode,errmsg,response
	if errcode != 200:
	    raise ErrorTypes(errcode), self.rurl + '\n' + errmsg + response
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
# Revision 1.5  1997/04/16 21:56:27  jim
# repr now shows URL on Not Found.
#
# Revision 1.4  1997/04/12 17:18:18  jim
# Many wonderous changes by Brian.
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
