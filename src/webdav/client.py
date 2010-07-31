"""HTTP 1.1 / WebDAV client library."""

import sys, os,  time, types,re
import httplib, mimetools
from types import FileType
from mimetypes import guess_type
from base64 import encodestring
from common import rfc1123_date
from cStringIO import StringIO
from random import random
from urllib import quote


class NotAvailable(Exception):
    pass

class HTTP(httplib.HTTP):
    # A revised version of the HTTP class that can do basic
    # HTTP 1.1 connections, and also compensates for a bug
    # that occurs on some platforms in 1.5 and 1.5.1 with
    # socket.makefile().read()

    read_bug=sys.version[:5] in ('1.5 (','1.5.1')

    def putrequest(self, request, selector, ver='1.1'):
        selector=selector or '/'
        str = '%s %s HTTP/%s\r\n' % (request, selector, ver)
        self.send(str)

    def getreply(self):
        file=self.sock.makefile('rb')
        data=''.join(file.readlines())
        file.close()
        self.file=StringIO(data)
        line = self.file.readline()
        try:
            [ver, code, msg] = line.split( None, 2)
        except ValueError:
            try:
                [ver, code] = line.split( None, 1)
                msg = ""
            except ValueError:
                return -1, line, None
        if ver[:5] != 'HTTP/':
            return -1, line, None
        code=int(code)
        msg =msg.strip()
        headers =mimetools.Message(self.file, 0)
        return ver, code, msg, headers


class Resource:
    """An object representing a web resource."""

    def __init__(self, url, username=None, password=None):
        self.username=username
        self.password=password
        self.url=url

        mo = urlreg.match(url)
        if mo:
            host,port,uri=mo.group(1,2,3)
            self.host=host
            self.port=port and int(port[1:]) or 80
            self.uri=uri or '/'
        else: raise ValueError, url

    def __getattr__(self, name):
        url=os.path.join(self.url, name)
        return self.__class__(url, username=self.username,
                              password=self.password)

    def __get_headers(self, kw={}):
        headers={}
        headers=self.__set_authtoken(headers)
        headers['User-Agent']='WebDAV.client'
        headers['Host']=self.host
        headers['Connection']='close'
        headers['Accept']='*/*'
        if kw.has_key('headers'):
            for name, val in kw['headers'].items():
                headers[name]=val
            del kw['headers']
        return headers

    def __set_authtoken(self, headers, atype='Basic'):
        if not (self.username and self.password):
            return headers
        if headers.has_key('Authorization'):
            return headers
        if atype=='Basic':
            headers['Authorization']=(
                "Basic %s" % (encodestring('%s:%s' % (self.username,self.password))).replace(
                                            '\012',''))
            return headers
        raise ValueError, 'Unknown authentication scheme: %s' % atype

    def __enc_formdata(self, args={}):
        formdata=[]
        for key, val in args.items():
            n=key.rfind( '__')
            if n > 0:
                tag=key[n+2:]
                key=key[:n]
            else: tag='string'
            func=varfuncs.get(tag, marshal_string)
            formdata.append(func(key, val))
        return '&'.join(formdata)

    def __enc_multipart(self, args={}):
        return MultiPart(args).render()

    def __snd_request(self, method, uri, headers={}, body='', eh=1):
        try:
            h=HTTP()
            h.connect(self.host, self.port)
            h.putrequest(method, uri)
            for n, v in headers.items():
                h.putheader(n, v)
            if eh: h.endheaders()
            if body: h.send(body)
            ver, code, msg, hdrs=h.getreply()
            data=h.getfile().read()
            h.close()
        except:
            raise NotAvailable, sys.exc_value
        return http_response(ver, code, msg, hdrs, data)

    # HTTP methods

    def get(self, **kw):
        headers=self.__get_headers(kw)
        query=self.__enc_formdata(kw)
        uri=query and '%s?%s' % (self.uri, query) or self.uri
        return self.__snd_request('GET', uri, headers)

    def head(self, **kw):
        headers=self.__get_headers(kw)
        query=self.__enc_formdata(kw)
        uri=query and '%s?%s' % (self.uri, query) or self.uri
        return self.__snd_request('HEAD', uri, headers)

    def post(self, **kw):
        headers=self.__get_headers(kw)
        content_type=None
        for key, val in kw.items():
            if (key[-6:]=='__file') or hasattr(val, 'read'):
                content_type='multipart/form-data'
                break
        if content_type=='multipart/form-data':
            body=self.__enc_multipart(kw)
            return self.__snd_request('POST', self.uri, headers, body, eh=0)
        else:
            body=self.__enc_formdata(kw)
            headers['Content-Type']='application/x-www-form-urlencoded'
            headers['Content-Length']=str(len(body))
            return self.__snd_request('POST', self.uri, headers, body)

    def put(self, file='', content_type='', content_enc='',
            isbin=re.compile(r'[\000-\006\177-\277]').search,
            **kw):
        headers=self.__get_headers(kw)
        filetype=type(file)
        if filetype is type('') and (isbin(file) is None) and \
           os.path.exists(file):
            ob=open(file, 'rb')
            body=ob.read()
            ob.close()
            c_type, c_enc=guess_type(file)
        elif filetype is FileType:
            body=file.read()
            c_type, c_enc=guess_type(file.name)
        elif filetype is type(''):
            body=file
            c_type, c_enc=guess_type(self.url)
        else:
            raise ValueError, 'File must be a filename, file or string.'
        content_type=content_type or c_type
        content_enc =content_enc or c_enc
        if content_type: headers['Content-Type']=content_type
        if content_enc:  headers['Content-Encoding']=content_enc
        headers['Content-Length']=str(len(body))
        return self.__snd_request('PUT', self.uri, headers, body)

    def options(self, **kw):
        headers=self.__get_headers(kw)
        return self.__snd_request('OPTIONS', self.uri, headers)

    def trace(self, **kw):
        headers=self.__get_headers(kw)
        return self.__snd_request('TRACE', self.uri, headers)

    def delete(self, **kw):
        headers=self.__get_headers(kw)
        return self.__snd_request('DELETE', self.uri, headers)

    def propfind(self, body='', depth=0, **kw):
        headers=self.__get_headers(kw)
        headers['Depth']=str(depth)
        headers['Content-Type']='text/xml; charset="utf-8"'
        headers['Content-Length']=str(len(body))
        return self.__snd_request('PROPFIND', self.uri, headers, body)

    def proppatch(self, body, **kw):
        headers=self.__get_headers(kw)
        if body: headers['Content-Type']='text/xml; charset="utf-8"'
        headers['Content-Length']=str(len(body))
        return self.__snd_request('PROPPATCH', self.uri, headers, body)

    def copy(self, dest, depth='infinity', overwrite=0, **kw):
        """Copy a resource to the specified destination."""
        headers=self.__get_headers(kw)
        headers['Overwrite']=overwrite and 'T' or 'F'
        headers['Destination']=dest
        headers['Depth']=depth
        return self.__snd_request('COPY', self.uri, headers)

    def move(self, dest, depth='infinity', overwrite=0, **kw):
        """Move a resource to the specified destination."""
        headers=self.__get_headers(kw)
        headers['Overwrite']=overwrite and 'T' or 'F'
        headers['Destination']=dest
        headers['Depth']=depth
        return self.__snd_request('MOVE', self.uri, headers)

    def mkcol(self, **kw):
        headers=self.__get_headers(kw)
        return self.__snd_request('MKCOL', self.uri, headers)

    # class 2 support

    def lock(self, scope='exclusive', type='write', owner='',
             depth='infinity', timeout='Infinite', **kw):
        """Create a lock with the specified scope, type, owner, depth
        and timeout on the resource. A locked resource prevents a principal
        without the lock from executing a PUT, POST, PROPPATCH, LOCK, UNLOCK,
        MOVE, DELETE, or MKCOL on the locked resource."""
        if not scope in ('shared', 'exclusive'):
            raise ValueError, 'Invalid lock scope.'
        if not type in ('write',):
            raise ValueError, 'Invalid lock type.'
        if not depth in ('0', 'infinity'):
            raise ValueError, 'Invalid depth.'
        headers=self.__get_headers(kw)
        body='<?xml version="1.0" encoding="utf-8"?>\n' \
             '<d:lockinfo xmlns:d="DAV:">\n' \
             '  <d:lockscope><d:%s/></d:lockscope>\n' \
             '  <d:locktype><d:%s/></d:locktype>\n' \
             '  <d:depth>%s</d:depth>\n' \
             '  <d:owner>\n' \
             '  <d:href>%s</d:href>\n' \
             '  </d:owner>\n' \
             '</d:lockinfo>' % (scope, type, depth, owner)
        headers['Content-Type']='text/xml; charset="utf-8"'
        headers['Content-Length']=str(len(body))
        headers['Timeout']=timeout
        headers['Depth']=depth
        return self.__snd_request('LOCK', self.uri, headers, body)

    def unlock(self, token, **kw):
        """Remove the lock identified by token from the resource and all
        other resources included in the lock.  If all resources which have
        been locked under the submitted lock token can not be unlocked the
        unlock method will fail."""
        headers=self.__get_headers(kw)
        token='<opaquelocktoken:%s>' % str(token)
        headers['Lock-Token']=token
        return self.__snd_request('UNLOCK', self.uri, headers)

    def allprops(self, depth=0):
        return self.propfind('', depth)

    def propnames(self, depth=0):
        body='<?xml version="1.0" encoding="utf-8"?>\n' \
              '<d:propfind xmlns:d="DAV:">\n' \
              '  <d:propname/>\n' \
              '</d:propfind>'
        return self.propfind(body, depth)

    def getprops(self, *names):
        if not names: return self.propfind()
        tags='/>\n  <'.join(names )
        body='<?xml version="1.0" encoding="utf-8"?>\n' \
              '<d:propfind xmlns:d="DAV:">\n' \
              '  <d:prop>\n' \
              '  <%s>\n' \
              '  </d:prop>\n' \
              '</d:propfind>' % tags
        return self.propfind(body, 0)

    def setprops(self, **props):
        if not props:
            raise ValueError, 'No properties specified.'
        tags=[]
        for key, val in props.items():
            tags.append('  <%s>%s</%s>' % (key, val, key))
        tags='\n'.join(tags )
        body='<?xml version="1.0" encoding="utf-8"?>\n' \
              '<d:propertyupdate xmlns:d="DAV:">\n' \
              '<d:set>\n' \
              '  <d:prop>\n' \
              '  %s\n' \
              '  </d:prop>\n' \
              '</d:set>\n' \
              '</d:propertyupdate>' % tags
        return self.proppatch(body)

    def delprops(self, *names):
        if not names:
            raise ValueError, 'No property names specified.'
        tags='/>\n  <'.join(names)
        body='<?xml version="1.0" encoding="utf-8"?>\n' \
              '<d:propertyupdate xmlns:d="DAV:">\n' \
              '<d:remove>\n' \
              '  <d:prop>\n' \
              '  <%s>\n' \
              '  </d:prop>\n' \
              '</d:remove>\n' \
              '</d:propfind>' % tags
        return self.proppatch(body)

    def __str__(self):
        return '<HTTP resource %s>' % self.url

    __repr__=__str__








class http_response:
    def __init__(self, ver, code, msg, headers, body):
        self.version=ver
        self.code=code
        self.msg=msg
        self.headers=headers
        self.body=body

    def get_status(self):
        return '%s %s' % (self.code, self.msg)

    def get_header(self, name, val=None):
        return self.headers.dict.get(name.lower(), val)

    def get_headers(self):
        return self.headers.dict

    def get_body(self):
        return self.body

    def __str__(self):
        data=[]
        data.append('%s %s %s\r\n' % (self.version, self.code, self.msg))
        map(data.append, self.headers.headers)
        data.append('\r\n')
        data.append(self.body)
        return ''.join(data)


set_xml="""<?xml version="1.0" encoding="utf-8"?>
   <d:propertyupdate xmlns:d="DAV:"
   xmlns:z="http://www.zope.org/propsets/default">
   <d:set>
   <d:prop>
   <z:author>Brian Lloyd</z:author>
   <z:title>My New Title</z:title>
   </d:prop>
   </d:set>
   </d:propertyupdate>
"""

funny="""<?xml version="1.0" encoding="utf-8"?>
 <d:propertyupdate xmlns:d="DAV:"
    xmlns:z="http://www.zope.org/propsets/default"
    xmlns:q="http://www.something.com/foo/bar">
 <d:set>
 <d:prop>
   <z:author>Brian Lloyd</z:author>
   <z:color>blue</z:color>
   <z:count>72</z:count>
   <q:Authors q:type="authorthing" z:type="string" xmlns:k="FOO:" xml:lang="en">
     <q:Author>
       <q:Person k:thing="Im a thing!">
         <q:Name>Brian Lloyd</q:Name>
       </q:Person>
     </q:Author>
   </q:Authors>
   <q:color>
     red
   </q:color>
 </d:prop>
 </d:set>
</d:propertyupdate>
"""


rem_xml="""<?xml version="1.0" encoding="utf-8"?>
   <d:propertyupdate xmlns:d="DAV:"
   xmlns:z="http://www.zope.org/propsets/default">
   <d:remove>
   <d:prop>
   <z:author/>
   <z:title/>
   </d:prop>
   </d:remove>
   </d:propertyupdate>
"""

find_xml="""<?xml version="1.0" encoding="utf-8" ?>
   <D:propfind xmlns:D="DAV:">
     <D:prop xmlns:z="http://www.zope.org/propsets/default">
          <z:title/>
          <z:author/>
          <z:content_type/>
     </D:prop>
   </D:propfind>
"""



##############################################################################
# Implementation details below here


urlreg=re.compile(r'http://([^:/]+)(:[0-9]+)?(/.+)?', re.I)

def marshal_string(name, val):
    return '%s=%s' % (name, quote(str(val)))

def marshal_float(name, val):
    return '%s:float=%s' % (name, val)

def marshal_int(name, val):
    return '%s:int=%s' % (name, val)

def marshal_long(name, val):
    value = '%s:long=%s' % (name, val)
    if value[-1] == 'L':
        value = value[:-1]
    return value

def marshal_list(name, seq, tname='list', lt=type([]), tt=type(())):
    result=[]
    for v in seq:
        tp=type(v)
        if tp in (lt, tt):
            raise TypeError, 'Invalid recursion in data to be marshaled.'
        result.append(marshal_var("%s:%s" % (name, tname), v))
    return '&'.join(result)

def marshal_tuple(name, seq):
    return marshal_list(name, seq, 'tuple')

varfuncs={}
vartypes=(('int',    type(1), marshal_int),
          ('float',  type(1.0), marshal_float),
          ('long',   type(1L), marshal_long),
          ('list',   type([]), marshal_list),
          ('tuple',  type(()), marshal_tuple),
          ('string', type(''), marshal_string),
          ('file',   types.FileType, None),
          )
for name, tp, func in vartypes:
    varfuncs[name]=func
    varfuncs[tp]=func

def marshal_var(name, val):
    return varfuncs.get(type(val), marshal_string)(name, val)



class MultiPart:
    def __init__(self,*args):
        c=len(args)
        if c==1:    name,val=None,args[0]
        elif c==2:  name,val=args[0],args[1]
        else:       raise ValueError, 'Invalid arguments'

        h={'Content-Type':              {'_v':''},
           'Content-Transfer-Encoding': {'_v':''},
           'Content-Disposition':       {'_v':''},
           }
        dt=type(val)
        b=t=None

        if dt==types.DictType:
            t=1
            b=self.boundary()
            d=[]
            h['Content-Type']['_v']='multipart/form-data; boundary=%s' % b
            for n,v in val.items():
                d.append(MultiPart(n,v))

        elif (dt==types.ListType) or (dt==types.TupleType):
            raise ValueError, 'Sorry, nested multipart is not done yet!'

        elif dt==types.FileType or hasattr(val,'read'):
            if hasattr(val,'name'):
                ct, enc=guess_type(val.name)
                if not ct: ct='application/octet-stream'
                fn=val.name.replace('\\','/')
                fn=fn[(fn.rfind('/')+1):]
            else:
                ct='application/octet-stream'
                enc=''
                fn=''

            enc=enc or (ct[:6] in ('image/', 'applic') and 'binary' or '')

            h['Content-Disposition']['_v']      ='form-data'
            h['Content-Disposition']['name']    ='"%s"' % name
            h['Content-Disposition']['filename']='"%s"' % fn
            h['Content-Transfer-Encoding']['_v']=enc
            h['Content-Type']['_v']             =ct
            d=[]
            l=val.read(8192)
            while l:
                d.append(l)
                l=val.read(8192)
        else:
            n=name.rfind( '__')
            if n > 0: name='%s:%s' % (name[:n], name[n+2:])
            h['Content-Disposition']['_v']='form-data'
            h['Content-Disposition']['name']='"%s"' % name
            d=[str(val)]

        self._headers =h
        self._data    =d
        self._boundary=b
        self._top     =t


    def boundary(self):
        return '%s_%s_%s' % (int(time.time()), os.getpid(), random())

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
            for d in self._data:
                p.append(d.render())
            t.append('--%s\n' % b)
            t.append(('\n--%s\n' % b).join(p))
            t.append('\n--%s--\n' % b)
            t=''.join(t)
            s.append('Content-Length: %s\n\n' % len(t))
            s.append(t)
            return ''.join(s)

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
                for d in self._data:
                    p.append(d.render())
                s.append('--%s\n' % b)
                s.append(('\n--%s\n' % b).join(p))
                s.append('\n--%s--\n' % b)
                return ''.join(s)
            else:
                return ''.join(s+self._data)


    _extmap={'':     'text/plain',
             'rdb':  'text/plain',
             'html': 'text/html',
             'dtml': 'text/html',
             'htm':  'text/html',
             'dtm':  'text/html',
             'gif':  'image/gif',
             'jpg':  'image/jpeg',
             'exe':  'application/octet-stream',
             None :  'application/octet-stream',
             }

    _encmap={'image/gif': 'binary',
             'image/jpg': 'binary',
             'application/octet-stream': 'binary',
             }


bri =Resource('http://tarzan.digicool.com/dev/brian3/',
              username='brian',
              password='123')
abri=Resource('http://tarzan.digicool.com/dev/brian3/')

dav =Resource('http://tarzan.digicool.com/dev/dav/',
              username='brian',
              password='123')
adav=Resource('http://tarzan.digicool.com/dev/dav/')
