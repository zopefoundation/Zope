#!/bin/env python
############################################################################## 
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
############################################################################## 
__doc__="""Bobo call interface"""
__version__='$Revision: 1.13 $'[11:-2]

import sys,regex,socket,mimetools
from httplib import HTTP, replyprog
from os import getpid
from time import time
from rand import rand
from regsub import gsub
from base64 import encodestring
from urllib import urlopen, quote
from types import FileType,ListType,DictType,TupleType
from string import strip,split,atoi,join,rfind,splitfields,joinfields







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
	      'NotAvailable'     :NotAvailable,
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

    def __init__(self,etype=None,evalue=None,efile=None,eline=None,url=None,
		 query=None,http_code=None,http_msg=None, http_resp=None):
        """Contains information about an exception which
           occurs in a remote method call"""
        self.exc_type    =etype
	self.exc_value   =evalue
	self.exc_file    =efile
	self.exc_line    =eline
        self.url         =url
	self.query       =query
	self.http_code   =http_code
        self.http_message=http_msg
        self.response    =http_resp

    def __repr__(self):
	return '%s (File: %s Line: %s)\n%s %s for %s' % (
	        self.exc_value,self.exc_file,self.exc_line,
		self.http_code,self.http_message,self.url)




class RemoteMethod:

    username=password=''

    def __init__(self,url,*args):
	while url[-1:]=='/': url=url[:-1]
	self.url=url
	self.headers={}
	self.func_name=url[rfind(url,'/')+1:]
	self.__dict__['__name__']=self.func_name
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

	if query:
	    method='POST'
	    query=join(query,'&')
	else: method='GET'

	try:
	    h=HTTP()
	    h.connect(self.host, self.port)
	    h.putrequest(method, self.rurl)
	    h.putheader('Content-Type', 'application/x-www-form-urlencoded')
	    if query: h.putheader('Content-Length', str(len(query)))
	    for hn,hv in self.headers.items(): h.putheader(hn,hv)
	    if self.username and self.password:
	        credentials=gsub('\012','',encodestring('%s:%s' % (
		                           self.username,self.password)))
	        h.putheader('Authorization',"Basic %s" % credentials)
	    h.endheaders()
	    if query: h.send(query)
	    ec,em,headers=h.getreply()
	    response     =h.getfile().read()
	except:
	    raise NotAvailable, \
		  RemoteException(NotAvailable,sys.exc_value,self.url,query)

	if ec==200: return (headers,response)
	else:
	    try:    v=headers.dict['bobo-exception-value']
	    except: v=ec
	    try:    f=headers.dict['bobo-exception-file']
	    except: f='Unknown'
	    try:    l=headers.dict['bobo-exception-line']
	    except: l='Unknown'
	    try:    t=exceptmap[headers.dict['bobo-exception-type']]
	    except:
		if   ec >= 400 and ec < 500: t=NotFound
		elif ec == 503:              t=NotAvailable
		else:                        t=ServerError
	    raise t, RemoteException(t,v,f,l,self.url,query,ec,em,response)







# This section added for multipart/form-data
# file upload support...

class MultiPart:
    def __init__(self,*args):
        c=len(args)
        if c==1:    name,val=None,args[0]
        elif c==2:  name,val=args[0],args[1]
        else:       raise ValueError, 'Invalid arguments'


        h={'Content-Type':              {'_v':''},
           'Content-Transfer-Encoding': {'_v':''},
           'Content-Disposition':       {'_v':''},}
        dt=type(val)
        b=t=None

        if dt==DictType:
	    t=1
            b=self.boundary()
            d=[]
            h['Content-Type']['_v']='multipart/form-data; boundary=%s' % b
            for n,v in val.items(): d.append(MultiPart(n,v))

        elif (dt==ListType) or (dt==TupleType):
            raise ValueError, 'Sorry, nested multipart is not done yet!'

        elif dt==FileType:
            fn=gsub('\\\\','/',val.name)
            fn=fn[(rfind(fn,'/')+1):]
            ex=fn[(rfind(fn,'.')+1):]
            try:    ct=self._extmap[ex]
            except: ct=self._extmap['']
            try:    ce=self._encmap[ct]
            except: ce=''

            h['Content-Disposition']['_v']      ='form-data'
            h['Content-Disposition']['name']    ='"%s"' % name
            h['Content-Disposition']['filename']='"%s"' % fn
            h['Content-Transfer-Encoding']['_v']=ce
            h['Content-Type']['_v']             =ct
            d=val.read()

        else:
            h['Content-Disposition']['_v']='form-data'
            h['Content-Disposition']['name']='"%s"' % name
            d=str(val)

        self._headers =h
        self._data    =d
        self._boundary=b
        self._top     =t


    def boundary(self):
        return '%s_%s_%s' % (int(time()), getpid(), rand())


    def render(self):
        h=self._headers
        s=[]

	if self._top:
            for n,v in h.items():
                if v['_v']:
                    s.append('%s: %s' % (n,v['_v']))
                    for k in v.keys():
                        if k != '_v': s.append('; %s=%s' % (k, v[k]))
                    s.append('\n')
            p=[]
            t=[]
            b=self._boundary
            for d in self._data: p.append(d.render())
            t.append('--%s\n' % b)
            t.append(joinfields(p,'\n--%s\n' % b))
            t.append('\n--%s--\n' % b)
            t=joinfields(t,'')
            s.append('Content-Length: %s\n\n' % len(t))
            s.append(t)
            return joinfields(s,'')

	else:
            for n,v in h.items():
                if v['_v']:
                    s.append('%s: %s' % (n,v['_v']))
                    for k in v.keys():
                        if k != '_v': s.append('; %s=%s' % (k, v[k]))
                    s.append('\n')
            s.append('\n')

            if self._boundary:
	        p=[]
                b=self._boundary
                for d in self._data: p.append(d.render())
	        s.append('--%s\n' % b)
                s.append(joinfields(p,'\n--%s\n' % b))
                s.append('\n--%s--\n' % b)
                return joinfields(s,'')
            else:
                return joinfields(s,'')+self._data


    _extmap={'':     'text/plain',
             'rdb':  'text/plain',
             'html': 'text/html',
             'dtml': 'text/html',
             'htm':  'text/html',
             'dtm':  'text/html',
             'gif':  'image/gif',
             'jpg':  'image/jpeg',
             'exe':  'application/octet-stream',
             }

    _encmap={'image/gif': 'binary',
             'image/jpg': 'binary',
             'application/octet-stream': 'binary',
             }




class mpRemoteMethod:
    username=password=''
    def __init__(self,url,*args):
	while url[-1:]=='/': url=url[:-1]
	self.url=url
	self.headers={}
	self.func_name=url[rfind(url,'/')+1:]
	self.__dict__['__name__']=self.func_name
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


    type2suffix={type(1.0): ':float',
		 type(1):   ':int',
		 type(1L):  ':long',
		 type([]):  ':list',
		 type(()):  ':tuple',
		 }

    def __call__(self,*args,**kw):
	for i in range(len(args)):
	    try:
		k=self.args[i]
		if kw.has_key(k): raise TypeError, 'Keyword arg redefined'
		kw[k]=args[i]
	    except IndexError:    raise TypeError, 'Too many arguments'

	d={}
	smap=self.type2suffix
	for k,v in kw.items():
	    s=''
	    if ':' not in k:
	        try:    s=smap(type(v))
	        except: pass
	    d['%s%s' % (k,s)]=v

        rq=[('POST %s HTTP/1.0' % self.rurl),]
	for n,v in self.headers.items():
	    rq.append('%s: %s' % (n,v))
	if self.username and self.password:
	    c=gsub('\012','',encodestring('%s:%s' % (
		             self.username,self.password)))
	    rq.append('Authorization: Basic %s' % c)
        rq.append(MultiPart(d).render())
        rq=joinfields(rq,'\n')

	try:
            sock=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            sock.connect(self.host,self.port)
            sock.send(rq)
            reply=sock.makefile('rb')
            sock=None
            line=reply.readline()
	    if replyprog.match(line) < 0:
		raise 'BadReply','Bad reply from server'
            ec,em=replyprog.group(1,2)
            ec=atoi(ec)
            em=strip(em)
            headers=mimetools.Message(reply,0)
            response=reply.read()
	except:
	    raise NotAvailable, \
		  RemoteException(NotAvailable,sys.exc_value,
				  self.url,'<MultiPart Form>')
		
	if ec==200: return (headers,response)
	else:
	    try:    v=headers.dict['bobo-exception-value']
	    except: v=ec
	    try:    f=headers.dict['bobo-exception-file']
	    except: f='Unknown'
	    try:    l=headers.dict['bobo-exception-line']
	    except: l='Unknown'
	    try:    t=exceptmap[headers.dict['bobo-exception-type']]
	    except:
		if   ec >= 400 and ec < 500: t=NotFound
		elif ec == 503:              t=NotAvailable
		else:                        t=ServerError
	    raise t, RemoteException(t,v,f,l,self.url,'<MultiPart Form>',
				     ec,em,response)










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
    import getopt
    from string import split

    user=None

    try:
	optlist, args = getopt.getopt(sys.argv[1:],'u:')
	url=args[0]
	u =filter(lambda o: o[0]=='-u', optlist)
	if u:
	    [user, pw] = split(u[0][1],':')

	kw={}
	for arg in args[1:]:
	    [name,v]=split(arg)
	    kw[name]=v

    except:
	print """
	Usage: %s [-u username:password] url [name=value ...]

	where url is the web resource to call.

	The -u option may be used to provide a user name and password.

	Optional arguments may be provides as name=value pairs.
	""" % sys.argv[0]
	sys.exit(1)

    # The "main" program for this module
    f=BoboFunction(url)
    if user: f.username, f.password = user, pw
    print apply(f,(),kw)


if __name__ == "__main__": main()

#
# $Log: Client.py,v $
# Revision 1.13  1997/09/11 22:27:27  jim
# Added logic to usef GET when no query parameters.
#
# Revision 1.12  1997/07/09 15:03:08  jim
# Fixed usage info.
#
# Revision 1.11  1997/07/09 14:51:53  jim
# Added command-line interface.
#
# Revision 1.10  1997/06/06 14:26:32  brian
# Added multipart/form-data support with a new mpRemoteMethod object
# which allows file upload via bci.
#
# Revision 1.9  1997/05/05 21:58:20  brian
# Worked around weird problem where python didnt want to assign to
# __name__ in RemoteMethod's __init__
#
# Revision 1.8  1997/04/29 16:23:27  brian
# Added logic to work with the pcgi-wrapper - bci.NotAvailable will be raised
# by a RemoteMethod if the remote host is not reachable from a network problem
# or if the request timed out at the other end.
#
# Revision 1.7  1997/04/18 19:45:47  jim
# Brian's changes to try and get file name and line no in exceptions.
#
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
