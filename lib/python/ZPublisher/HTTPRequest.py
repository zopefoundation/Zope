##############################################################################
# 
# Zope Public License (ZPL) Version 1.0
# -------------------------------------
# 
# Copyright (c) Digital Creations.  All rights reserved.
# 
# This license has been certified as Open Source(tm).
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
# 
# 1. Redistributions in source code must retain the above copyright
#    notice, this list of conditions, and the following disclaimer.
# 
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions, and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
# 
# 3. Digital Creations requests that attribution be given to Zope
#    in any manner possible. Zope includes a "Powered by Zope"
#    button that is installed by default. While it is not a license
#    violation to remove this button, it is requested that the
#    attribution remain. A significant investment has been put
#    into Zope, and this effort will continue if the Zope community
#    continues to grow. This is one way to assure that growth.
# 
# 4. All advertising materials and documentation mentioning
#    features derived from or use of this software must display
#    the following acknowledgement:
# 
#      "This product includes software developed by Digital Creations
#      for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
#    In the event that the product being advertised includes an
#    intact Zope distribution (with copyright and license included)
#    then this clause is waived.
# 
# 5. Names associated with Zope or Digital Creations must not be used to
#    endorse or promote products derived from this software without
#    prior written permission from Digital Creations.
# 
# 6. Modified redistributions of any form whatsoever must retain
#    the following acknowledgment:
# 
#      "This product includes software developed by Digital Creations
#      for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
#    Intact (re-)distributions of any official Zope release do not
#    require an external acknowledgement.
# 
# 7. Modifications are encouraged but must be packaged separately as
#    patches to official Zope releases.  Distributions that do not
#    clearly separate the patches from the original work must be clearly
#    labeled as unofficial distributions.  Modifications which do not
#    carry the name Zope may be packaged in any form, as long as they
#    conform to all of the clauses above.
# 
# 
# Disclaimer
# 
#   THIS SOFTWARE IS PROVIDED BY DIGITAL CREATIONS ``AS IS'' AND ANY
#   EXPRESSED OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
#   IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
#   PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL DIGITAL CREATIONS OR ITS
#   CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
#   SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
#   LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF
#   USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#   ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
#   OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT
#   OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
#   SUCH DAMAGE.
# 
# 
# This software consists of contributions made by Digital Creations and
# many individuals on behalf of Digital Creations.  Specific
# attributions are listed in the accompanying credits file.
# 
##############################################################################

__version__='$Revision: 1.10 $'[11:-2]

import regex, sys, os, string
from string import lower, atoi, rfind, split, strip, join, upper, find
from BaseRequest import BaseRequest
from HTTPResponse import HTTPResponse
from cgi import FieldStorage
from urllib import quote, unquote
from Converters import type_converters
from maybe_lock import allocate_lock
xmlrpc=None # Placeholder for module that we'll import if we have to.

isCGI_NAME = {
        'SERVER_SOFTWARE' : 1, 
        'SERVER_NAME' : 1, 
        'GATEWAY_INTERFACE' : 1, 
        'SERVER_PROTOCOL' : 1, 
        'SERVER_PORT' : 1, 
        'REQUEST_METHOD' : 1, 
        'PATH_INFO' : 1, 
        'PATH_TRANSLATED' : 1, 
        'SCRIPT_NAME' : 1, 
        'QUERY_STRING' : 1, 
        'REMOTE_HOST' : 1, 
        'REMOTE_ADDR' : 1, 
        'AUTH_TYPE' : 1, 
        'REMOTE_USER' : 1, 
        'REMOTE_IDENT' : 1, 
        'CONTENT_TYPE' : 1, 
        'CONTENT_LENGTH' : 1,
        'SERVER_URL': 1,
        }.has_key

hide_key={'HTTP_AUTHORIZATION':1,
          'HTTP_CGI_AUTHORIZATION': 1,
          }.has_key

_marker=[]
class HTTPRequest(BaseRequest):
    """\
    Model HTTP request data.
    
    This object provides access to request data.  This includes, the
    input headers, form data, server data, and cookies.

    Request objects are created by the object publisher and will be
    passed to published objects through the argument name, REQUEST.

    The request object is a mapping object that represents a
    collection of variable to value mappings.  In addition, variables
    are divided into four categories:

      - Environment variables

        These variables include input headers, server data, and other
        request-related data.  The variable names are as <a
        href="http://hoohoo.ncsa.uiuc.edu/cgi/env.html">specified</a>
        in the <a
        href="http://hoohoo.ncsa.uiuc.edu/cgi/interface.html">CGI
        specification</a>

      - Form data

        These are data extracted from either a URL-encoded query
        string or body, if present.

      - Cookies

        These are the cookie data, if present.

      - Other

        Data that may be set by an application object.

    The form attribute of a request is actually a Field Storage
    object.  When file uploads are used, this provides a richer and
    more complex interface than is provided by accessing form data as
    items of the request.  See the FieldStorage class documentation
    for more details.

    The request object may be used as a mapping object, in which case
    values will be looked up in the order: environment variables,
    other variables, form data, and then cookies.
    """
    _hacked_path=None
    args=()
    
    def __init__(self, stdin, environ, response, clean=0):
        # Avoid the overhead of scrubbing the environment in the
        # case of request cloning for traversal purposes. If the
        # clean flag is set, we know we can use the passed in
        # environ dict directly.

        if not clean: environ=sane_environment(environ)

        method=environ.get('REQUEST_METHOD','GET')
        
        if method != 'GET': fp=stdin
        else:               fp=None

        if environ.has_key('HTTP_AUTHORIZATION'):
            self._auth=environ['HTTP_AUTHORIZATION']
            response._auth=1
            del environ['HTTP_AUTHORIZATION']

        form={}
        defaults={}

        # add class
        class record:
            def __str__(self):
              L1 = self.__dict__.items()
              L1.sort()
              return join(map(lambda item: "%s: %s" %item, L1), ", ") 
            __repr__ = __str__
            
        meth=None
        fs=FieldStorage(fp=fp,environ=environ,keep_blank_values=1)
        if not hasattr(fs,'list') or fs.list is None:
            # Hm, maybe it's an XML-RPC
            if (fs.headers.has_key('content-type') and
                fs.headers['content-type'] == 'text/xml' and
                method == 'POST'):
                # Ye haaa, XML-RPC!
                global xmlrpc
                if xmlrpc is None: import xmlrpc
                meth, self.args = xmlrpc.parse_input(fs.value)
                response=xmlrpc.response(response)
            else:
                form['BODY']=fs.value
        else:
            fslist=fs.list
            tuple_items={}
            type_re=regex.compile(':[a-zA-Z][a-zA-Z0-9_]+')
            type_search=type_re.search
            lt=type([])
            CGI_name=isCGI_NAME
            for item in fslist:
                key=unquote(item.name)
                if (hasattr(item,'file') and hasattr(item,'filename')
                    and hasattr(item,'headers')):
                    if (item.file and
                        (item.filename is not None or
                         'content-type' in map(lower,
                                               item.headers.keys()))):
                        item=FileUpload(item)
                    else:
                        item=item.value

                # tuple, list flag
                seqf=None
                # default flag
                setting_a_default=0
                # record flag
                record_flag=0
                # records_flag
                records_flag=0
                # empty_flag
                empty_flag=0
                # Use converter variable to defer conversion
                converter=None
                # add dictionary of types
                d1 = {'list':1, 'tuple':1, 'method':1, 'default_method':1,
                      'default':1, 'record':1, 'records':1, 'ignore_empty':1}

                # Loop through the different types and set
                # the appropriate flags
                l=type_search(key)
                while l >= 0:
                    type_name=type_re.group(0)[1:]
                    key=key[:l]+key[l+len(type_name)+1:]
                    if type_name not in d1.keys():
                       converter=type_converters[type_name]
                    else:
                       if type_name == 'list':
                          seqf=list
                       if type_name == 'tuple':
                          seqf=tuple
                          tuple_items[key]=1
                       if type_name == 'method':
                          if l: meth=key
                          else: meth=item
                       if type_name == 'default_method':
                          if not meth:
                             if l: meth=key
                             else: meth=item
                       if type_name == 'default':
                          setting_a_default = 1
                       if type_name == 'record':
                          record_flag = 1
                       if type_name == 'records':
                          records_flag = 1
                       if type_name == 'ignore_empty':
                          if item == "":
                             empty_flag = 1
                    l=type_search(key)

                # skip over empty fields    
                if empty_flag: continue
             
                # Filter out special names from form:
                if CGI_name(key) or key[:5]=='HTTP_': continue

                #Split the key and its attribute
                if record_flag or records_flag:
                       key=split(key,".")
                       key, attr=join(key[:-1],"."), key[-1]
                       
                # defer conversion
                if converter is not None:
                    try:
                        item=converter(item)
                    except:
                        if not item and not setting_a_default and defaults.has_key(key):
                            item = defaults[key]
                            if record_flag:
                                item=getattr(item,attr)
                            if records_flag:
                                item.reverse()
                                item = item[0]
                                item=getattr(item,attr)
                        else:
                            raise
                         
                #Determine which dictionary to use
                if setting_a_default:
                   mapping_object = defaults
                else:
                   mapping_object = form

                #Insert in dictionary
                if mapping_object.has_key(key):
                   if records_flag:
                       #Get the list and the last record
                       #in the list
                       reclist = mapping_object[key]
                       reclist.reverse()
                       x=reclist[0]
                       reclist.reverse()
                       if not hasattr(x,attr):
                           #If the attribute does not
                           #exist, set it
                           if seqf: item=[item]
                           reclist.remove(x)
                           setattr(x,attr,item)
                           reclist.append(x)
                           mapping_object[key] = reclist
                       else:
                           if seqf:
                              # If the attribute is a
                              # sequence, append the item
                              # to the existing attribute
                               reclist.remove(x)
                               y = getattr(x, attr)
                               y.append(item)
                               setattr(x, attr, y)
                               reclist.append(x)
                               mapping_object[key] = reclist
                           else:
                              # Create a new record and add
                              # it to the list
                               n=record()
                               setattr(n,attr,item)
                               reclist.append(n)
                               mapping_object[key]=reclist
                   elif record_flag:
                       b=mapping_object[key]
                       if seqf:
                          item=[item]
                          if not hasattr(b,attr):
                              # if it does not have the
                              # attribute, set it
                              setattr(b,attr,item)
                          else:
                             # it has the attribute so
                             # append the item to it
                              setattr(b,attr,getattr(b,attr)+item)
                       else:
                          # it is not a sequence so
                          # set the attribute
                          setattr(b,attr,item)        
                   else:
                      # it is not a record or list of records
                       found=mapping_object[key]
                       if type(found) is lt:
                           found.append(item)
                       else:
                           found=[found,item]
                           mapping_object[key]=found
                else:
                   # The dictionary does not have the key
                   if records_flag:
                       # Create a new record, set its attribute
                       # and put it in the dictionary as a list
                       a = record()
                       if seqf: item=[item]
                       setattr(a,attr,item)
                       mapping_object[key]=[a]
                   elif record_flag:
                       # Create a new record, set its attribute
                       # and put it in the dictionary
                       if seqf: item=[item]
                       r = mapping_object[key]=record()
                       setattr(r,attr,item)
                   else:
                       # it is not a record or list of records
                       if seqf: item=[item]
                       mapping_object[key]=item
           
        #insert defaults into form dictionary
        for keys, values in defaults.items():
            if not form.has_key(keys) and not form == {}:
                # if the form does not have the key and the
                # form is not empty, set the default
                form[keys]=values
            else:
               # the form has the key
               if not form == {}:
                  if hasattr(values, '__class__') and  values.__class__ is record:
                     # if the key is mapped to a record, get the
                     # record
                     r = form[keys]
                     for k, v in values.__dict__.items():
                        # loop through the attributes and values
                        # in the default dictionary
                        if not hasattr(r, k):
                           # if the form dictionary doesn't have
                           # the attribute, set it to the default
                           setattr(r,k,v)
                           form[keys] = r    
                  else:
                     # the key is mapped to a list
                     l = form[keys]
                     for x in values:
                        # for each x in the list
                        if hasattr(x, '__class__') and x.__class__ is record:
                           # if the x is a record
                           for k, v in x.__dict__.items():
                              # loop through each attribute and value in the
                              # record
                              for y in l:
                                 # loop through each record in the form list
                                 # if it doesn't have the attributes in the
                                 # default dictionary, set them
                                 if not hasattr(y, k):
                                    setattr(y, k, v)
                        else:
                           # x is not a record
                           if not a in l:
                              l.append(a)
                     form[keys] = l       
                            
        # Convert to tuples
        for key in tuple_items.keys():
           # Split the key and get the attr
           k=split(key, ".")
           k,attr=join(k[:-1], "."), k[-1]
           a = attr
           # remove any type_names in the attr
           while not a=='':
              a=split(a, ":")
              a,new=join(a[:-1], ":"), a[-1]
           attr = new
           if form.has_key(k):
              # If the form has the split key get its value
              item =form[k]
              if hasattr(item, '__class__') and item.__class__ is record:
                 # if the value is mapped to a record, check if it
                 # has the attribute, if it has it, convert it to
                 # a tuple and set it
                 if hasattr(item,attr):
                    value=tuple(getattr(item,attr))
                    setattr(item,attr,value)
              else:
                 # It is mapped to a list of  records
                 for x in item:
                    # loop through the records
                    if hasattr(x, attr):
                       # If the record has the attribute
                       # convert it to a tuple and set it
                       value=tuple(getattr(x,attr))
                       setattr(x,attr,value)          
           else:
              # the form does not have the split key 
              if form.has_key(key):
                 # if it has the original key, get the item
                 # convert it to a tuple
                 item=form[key]  
                 item=tuple(form[key])
                 form[key]=item
                     
        other=self.other={}
        other.update(form)
        if meth:
            if environ.has_key('PATH_INFO'):
                path=environ['PATH_INFO']
                while path[-1:]=='/': path=path[:-1]
            else: path=''
            other['PATH_INFO']=path="%s/%s" % (path,meth)
            self._hacked_path=1

        # Cookie values should *not* be appended to existing form
        # vars with the same name - they are more like default values
        # for names not otherwise specified in the form.
        cookies={}
        if environ.has_key('HTTP_COOKIE'):
            parse_cookie(environ['HTTP_COOKIE'],cookies)
            for k,item in cookies.items():
                if not other.has_key(k):
                    other[k]=item

        self.form=form
        self.cookies=cookies
        other['RESPONSE']=self.response=response

        self.environ=environ
        self.stdin=stdin
        have_env=environ.has_key

        b=script=strip(environ['SCRIPT_NAME'])
        while b and b[-1]=='/': b=b[:-1]
        p = rfind(b,'/')
        if p >= 0: b=b[:p+1]
        else: b=''
        while b and b[0]=='/': b=b[1:]
        
        if have_env('SERVER_URL'):
             server_url=strip(environ['SERVER_URL'])
        else:
             if have_env('HTTPS') and (
                 environ['HTTPS'] == "on" or environ['HTTPS'] == "ON"):
                 server_url='https://'
             elif (have_env('SERVER_PORT_SECURE') and 
                   environ['SERVER_PORT_SECURE'] == "1"):
                 server_url='https://'
             else: server_url='http://'

             if have_env('HTTP_HOST'):
                 server_url=server_url+strip(environ['HTTP_HOST'])
             else:
                 server_url=server_url+strip(environ['SERVER_NAME'])
                 server_port=environ['SERVER_PORT']
                 if server_port!='80': server_url=server_url+':'+server_port
             other['SERVER_URL']=server_url
             
        if server_url[-1:]=='/': server_url=server_url[:-1]
                        
        if b: self.base="%s/%s" % (server_url,b)
        else: self.base=server_url
        while script[:1]=='/': script=script[1:]
        if script: script="%s/%s" % (server_url,script)
        else:      script=server_url
        other['URL']=self.script=script

    def resolve_url(self, url):
        # Attempt to resolve a url into an object in the Zope
        # namespace. The url must be a fully-qualified url. The
        # method will return the requested object if it is found
        # or raise the same HTTP error that would be raised in
        # the case of a real web request. If the passed in url
        # does not appear to describe an object in the system
        # namespace (e.g. the host, port or script name dont
        # match that of the current request), a ValueError will
        # be raised.
        if find(url, self.script) != 0:
            raise ValueError, 'Different namespace.'
        path=url[len(self.script):]
        while path and path[0]=='/':  path=path[1:]
        while path and path[-1]=='/': path=path[:-1]
        req=self.clone()
        rsp=req.response
        req['PATH_INFO']=path
        object=None
        try: object=req.traverse(path)
        except: rsp.exception(0)
        if object is not None:
            # waaa - traversal may return a "default object"
            # like an index_html document, though you really
            # wanted to get a Folder back :(
            if hasattr(object, 'id'):
                if callable(object.id):
                    name=object.id()
                else: name=object.id
            elif hasattr(object, '__name__'):
                name=object.__name__
            else: name=''
            if name != os.path.split(path)[-1]:
                return req.PARENTS[0]
            return object
        raise rsp.errmsg, sys.exc_value

    def clone(self):
        # Return a clone of the current request object 
        # that may be used to perform object traversal.
        environ=self.environ.copy()
        environ['REQUEST_METHOD']='GET'
        if self._auth: environ['HTTP_AUTHORIZATION']=self._auth
        clone=HTTPRequest(None, environ, HTTPResponse(), clean=1)
        clone['PARENTS']=[self['PARENTS'][-1]]
        clone._auth=self._auth
        return clone

    def get_header(self, name, default=None):
        """Return the named HTTP header, or an optional default
        argument or None if the header is not found. Note that
        both original and CGI-ified header names are recognized,
        e.g. 'Content-Type', 'CONTENT_TYPE' and 'HTTP_CONTENT_TYPE'
        should all return the Content-Type header, if available.
        """
        environ=self.environ
        name=upper(join(split(name,"-"),"_"))
        val=environ.get(name, None)
        if val is not None:
            return val
        if name[:5] != 'HTTP_':
            name='HTTP_%s' % name
        return environ.get(name, default)

    def __getitem__(self,key,
                    default=_marker, # Any special internal marker will do
                    URLmatch=regex.compile('URL[0-9]$').match,
                    BASEmatch=regex.compile('BASE[0-9]$').match,
                    ):
        """Get a variable value

        Return a value for the required variable name.
        The value will be looked up from one of the request data
        categories. The search order is environment variables,
        other variables, form data, and then cookies. 
        
        """ #"
        other=self.other
        if other.has_key(key):
            if key=='REQUEST': return self
            return other[key]

        if key[:1]=='U' and URLmatch(key) >= 0:
            n=ord(key[3])-ord('0')
            URL=other['URL']
            for i in range(0,n):
                l=rfind(URL,'/')
                if l >= 0: URL=URL[:l]
                else: raise KeyError, key
                if len(URL) < len(self.base) and n > 1: raise KeyError, key
            other[key]=URL
            return URL

        if isCGI_NAME(key) or key[:5] == 'HTTP_':
            environ=self.environ
            if environ.has_key(key) and (not hide_key(key)):
                return environ[key]
            return ''

        if key=='REQUEST': return self

        if key[:1]=='B' and BASEmatch(key) >= 0:
            n=ord(key[4])-ord('0')
            if n:
                if self.environ.get('SCRIPT_NAME',''): n=n-1
                if len(self.steps) < n:
                    raise KeyError, key

                v=self.script
                while v[-1:]=='/': v=v[:-1]
                v=join([v]+self.steps[:n],'/')
            else:
                v=self.base
                while v[-1:]=='/': v=v[:-1]
            other[key]=v
            return v

        v=self.common.get(key, default)
        if v is not _marker: return v

        raise KeyError, key

    __getattr__=get=__getitem__

    def keys(self):
        keys = {}
        keys.update(self.common)

        for key in self.environ.keys():
            if (isCGI_NAME(key) or key[:5] == 'HTTP_') and \
               (not hide_key(key)):
                    keys[key] = 1
        keys.update(self.other)
        lasturl = ""
        for n in "0123456789":
            key = "URL%s"%n
            try:
                if lasturl != self[key]:
                    keys[key] = 1
                    lasturl = self[key]
                else:
                    break
            except KeyError:
                pass
        for n in "0123456789":
            key = "BASE%s"%n
            try:
                if lasturl != self[key]:
                    keys[key] = 1
                    lasturl = self[key]
                else:
                    break
            except KeyError:
                pass

        return keys.keys()

    def __str__(self):
        result="<h3>form</h3><table>"
        row='<tr valign="top" align="left"><th>%s</th><td>%s</td></tr>'
        for k,v in self.form.items():
            result=result + row % (k,v)
        result=result+"</table><h3>cookies</h3><table>"
        for k,v in self.cookies.items():
            result=result + row % (k,v)
        result=result+"</table><h3>other</h3><table>"
        for k,v in self.other.items():
            if k in ('PARENTS','RESPONSE'): continue
            result=result + row % (k,v)
    
        for n in "0123456789":
            key = "URL%s"%n
            try: result=result + row % (key,self[key]) 
            except KeyError: pass
        for n in "0123456789":
            key = "BASE%s"%n
            try: result=result + row % (key,self[key]) 
            except KeyError: pass

        result=result+"</table><h3>environ</h3><table>"
        for k,v in self.environ.items():
            if not hide_key(k):
                result=result + row % (k,v)
        return result+"</table>"

    __repr__=__str__

    def _authUserPW(self):
        global base64
        auth=self._auth
        if auth:
            if lower(auth[:6]) == 'basic ':
                if base64 is None: import base64
                [name,password] = split(
                    base64.decodestring(split(auth)[-1]), ':')
                return name, password




base64=None

def sane_environment(env):
    # return an environment mapping which has been cleaned of
    # funny business such as REDIRECT_ prefixes added by Apache
    # or HTTP_CGI_AUTHORIZATION hacks.
    dict={}
    for key, val in env.items():
        while key[:9]=='REDIRECT_':
            key=key[9:]
        dict[key]=val
    if dict.has_key('HTTP_CGI_AUTHORIZATION'):
        dict['HTTP_AUTHORIZATION']=dict['HTTP_CGI_AUTHORIZATION']
        try: del dict['HTTP_CGI_AUTHORIZATION']
        except: pass
    return dict



def str_field(v):
    if type(v) is ListType:
        return map(str_field,v)

    if hasattr(v,'__class__') and v.__class__ is FieldStorage:
        v=v.value
    elif type(v) is not StringType:
        if hasattr(v,'file') and v.file: v=v.file
        elif hasattr(v,'value'): v=v.value
    return v


class FileUpload:
    '''\
    File upload objects

    File upload objects are used to represent file-uploaded data.

    File upload objects can be used just like files.

    In addition, they have a 'headers' attribute that is a dictionary
    containing the file-upload headers, and a 'filename' attribute
    containing the name of the uploaded file.
    '''

    def __init__(self, aFieldStorage):

        file=aFieldStorage.file
        if hasattr(file, '__methods__'): methods=file.__methods__
        else: methods= ['close', 'fileno', 'flush', 'isatty',
                        'read', 'readline', 'readlines', 'seek',
                        'tell', 'truncate', 'write', 'writelines']

        d=self.__dict__
        for m in methods:
            if hasattr(file,m): d[m]=getattr(file,m)

        self.headers=aFieldStorage.headers
        self.filename=aFieldStorage.filename
    

parse_cookie_lock=allocate_lock()
def parse_cookie(text,
                 result=None,
                 qparmre=regex.compile(
                     '\([\0- ]*'
                     '\([^\0- ;,=\"]+\)="\([^"]*\)\"'
                     '\([\0- ]*[;,]\)?[\0- ]*\)'
                     ),
                 parmre=regex.compile(
                     '\([\0- ]*'
                     '\([^\0- ;,=\"]+\)=\([^\0- ;,\"]*\)'
                     '\([\0- ]*[;,]\)?[\0- ]*\)'
                     ),
                 acquire=parse_cookie_lock.acquire,
                 release=parse_cookie_lock.release,
                 ):

    if result is None: result={}
    already_have=result.has_key

    acquire()
    try:
        if qparmre.match(text) >= 0:
            # Match quoted correct cookies
            name=qparmre.group(2)
            value=qparmre.group(3)
            l=len(qparmre.group(1))
        elif parmre.match(text) >= 0:
            # Match evil MSIE cookies ;)
            name=parmre.group(2)
            value=parmre.group(3)
            l=len(parmre.group(1))
        else:
            # this may be an invalid cookie.
            # We'll simply bail without raising an error
            # if the cookie is invalid.
            return result
            
    finally: release()

    if not already_have(name): result[name]=value

    return apply(parse_cookie,(text[l:],result))
