##############################################################################
#
# Copyright (c) 1996-1998, Digital Creations, Fredericksburg, VA, USA.
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
# 
#   o Redistributions of source code must retain the above copyright
#     notice, this list of conditions, and the disclaimer that follows.
# 
#   o Redistributions in binary form must reproduce the above copyright
#     notice, this list of conditions, and the following disclaimer in
#     the documentation and/or other materials provided with the
#     distribution.
# 
#   o All advertising materials mentioning features or use of this
#     software must display the following acknowledgement:
# 
#       This product includes software developed by Digital Creations
#       and its contributors.
# 
#   o Neither the name of Digital Creations nor the names of its
#     contributors may be used to endorse or promote products derived
#     from this software without specific prior written permission.
# 
# 
# THIS SOFTWARE IS PROVIDED BY DIGITAL CREATIONS AND CONTRIBUTORS *AS IS*
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED
# TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
# PARTICULAR PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL DIGITAL
# CREATIONS OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS
# OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR
# TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE
# USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH
# DAMAGE.
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

__doc__="""Python Object Publisher -- Publish Python objects on web servers

$Id: Publish.py,v 1.107 1998/11/23 15:29:15 jim Exp $"""
__version__='$Revision: 1.107 $'[11:-2]

import sys, os, string, cgi, regex
from string import lower, atoi, rfind, split, strip, join, upper, find
from Response import Response
from urllib import quote, unquote
from cgi import FieldStorage
from Request import Request, isCGI_NAME
from Converters import type_converters

# Waaaa, I wish I didn't have to work this hard.
try: from thread import allocate_lock
except:
    class allocate_lock:
        def acquire(*args): pass
        def release(*args): pass


ListType=type([])
StringType=type('')

UNSPECIFIED_ROLES=''

try:
    from ExtensionClass import Base
    class RequestContainer(Base):
        def __init__(self,**kw):
            for k,v in kw.items(): self.__dict__[k]=v

        def manage_property_types(self):
            return type_converters.keys()
            
except:
    class RequestContainer:
        def __init__(self,**kw):
            for k,v in kw.items(): self.__dict__[k]=v

class ModulePublisher:

    HTTP_AUTHORIZATION=None
    _hacked_path=None
    
    def __init__(self,
                 stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr,
                 environ=os.environ):
        self.environ=environ
        fp=None
        try:
            if environ['REQUEST_METHOD'] != 'GET': fp=stdin
        except: pass

        if environ.has_key('HTTP_AUTHORIZATION'):
            self.HTTP_AUTHORIZATION=environ['HTTP_AUTHORIZATION']
            try: del environ['HTTP_AUTHORIZATION']
            except: pass
        elif environ.has_key('HTTP_CGI_AUTHORIZATION'):
            self.HTTP_AUTHORIZATION=environ['HTTP_CGI_AUTHORIZATION']
            try: del environ['HTTP_CGI_AUTHORIZATION']
            except: pass

        form={}
        form_has=form.has_key
        other={}
        fs=FieldStorage(fp=fp,environ=environ,keep_blank_values=1)
        if not hasattr(fs,'list') or fs.list is None:
            form['BODY']=other['BODY']=fs.value
        else:
            fslist=fs.list
            tuple_items={}

            type_re=regex.compile(':[a-zA-Z][a-zA-Z0-9_]+')
            type_search=type_re.search
            lt=type([])
            CGI_name=isCGI_NAME
            meth=None
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

                seqf=None

                l=type_search(key)
                while l >= 0:
                    type_name=type_re.group(0)[1:]
                    key=key[:l]+key[l+len(type_name)+1:]
                    if type_name == 'list':
                        seqf=list
                    elif type_name == 'tuple':
                        seqf=tuple
                        tuple_items[key]=1
                    elif type_name == 'method':
                        if l: meth=key
                        else: meth=item
                    elif type_name == 'default_method':
                        if not meth:
                            if l: meth=key
                            else: meth=item
                    else:
                        item=type_converters[type_name](item)
                    l=type_search(key)
                    
                # Filter out special names from form:
                if CGI_name(key) or key[:5]=='HTTP_': continue

                if form_has(key):
                    found=form[key]
                    if type(found) is lt: found.append(item)
                    else:
                        found=[found,item]
                        form[key]=found
                        other[key]=found
                else:
                    if seqf: item=[item]
                    form[key]=item
                    other[key]=item

            for key in tuple_items.keys():
                item=tuple(form[key])
                form[key]=item
                other[key]=item

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
            parse_cookie(self.environ['HTTP_COOKIE'],cookies)
            for k,item in cookies.items():
                if not other.has_key(k):
                    other[k]=item

        request=self.request=Request(environ,other,stdin)
        request.form=form
        if cookies is not None: request.cookies=cookies
        self.response=response=Response(stdout=stdout, stderr=stderr)
        request['RESPONSE']=response
        self.stdin=stdin
        self.stdout=stdout
        self.stderr=stderr
        self.base=request.base
        self.script=request.script

    def html(self,title,body):
        return ("<html>\n"
                "<head>\n<title>%s</title>\n</head>\n"
                "<body>\n%s\n</body>\n"
                "</html>\n" % (title,body))

    def notFoundError(self,entry='who knows!'):
        raise 'NotFound',self.html(
            "Resource not found",
            "Sorry, the requested document does not exist.<p>"
            "\n<!--\n%s\n-->" % entry)

    forbiddenError=notFoundError  # If a resource is forbidden,
                                  # why reveal that it exists?

    def debugError(self,entry):
        raise 'NotFound',self.html(
            "Debugging Notice",
            "Bobo has encountered a problem publishing your object.<p>"
            "\n%s" % entry)

    def badRequestError(self,name):
        if regex.match('^[A-Z_0-9]+$',name) >= 0:
            raise 'InternalError', self.html(
                "Internal Error",
                "Sorry, an internal error occurred in this resource.")

        raise 'BadRequest',self.html(
            "Invalid request",
            "The parameter, <em>%s</em>, was omitted from the request."
            "<!--%s-->"
            % (name,self.request))

    def unauthorized(self, realm,debug_mode=None):
        if not (self.request.has_key('REMOTE_USER') and
                self.request['REMOTE_USER']):
            self.response['WWW-authenticate']='basic realm="%s"' % realm
        m="<strong>You are not authorized to access this resource.</strong>"
        if debug_mode:
            if self.HTTP_AUTHORIZATION:
                m=m+'\nUsername and password are not correct.'
            else:
                m=m+'\nNo Authorization header found.'
        raise 'Unauthorized', m

    def forbiddenError(self,object=None):
        raise 'NotFound',self.html(
            "Resource not found",
            "Sorry, the requested document does not exist.<p>"
            "<!--%s-->" % object)

    def get_request_data(self,request_params):
        try: request_params=request_params()
        except: pass
        for key in request_params.keys():
                self.request[key]=request_params[key]


    def publish(self, module_name, after_list, published='web_objects',
                imported_modules={}, module_dicts={},debug=0):

        request=self.request
        request_get=request.get
        response=self.response

        # First check for "cancel" redirect:
        cancel=''
        if request_get('SUBMIT','')=='cancel':
            cancel=request_get('CANCEL_ACTION','')
            if cancel: raise 'Redirect', cancel

        (bobo_before, bobo_after, request_params,
         inherited_groups, groups, roles,
         object, doc, published, realm, module_name,
         debug_mode)= get_module_info(module_name)
 
        after_list[0]=bobo_after

        if bobo_before is not None: bobo_before();

        if request_params: self.get_request_data(request_params)

        # Get a nice clean path list:
        path=strip(request_get('PATH_INFO'))

        __traceback_info__=path

        if path[:1] != '/': path='/'+path
        if path[-1:] != '/': path=path+'/'
        if find(path,'/.') >= 0:
            path=join(split(path,'/./'),'/')
            l=find(path,'/../',1)
            while l > 0:
                p1=path[:l]
                path=path[:rfind(p1,'/')+1]+path[l+4:]
                l=find(path,'/../',1)
        path=path[1:-1]

        path=split(path,'/')
        while path and not path[0]: path = path[1:]

        method=upper(request_get('REQUEST_METHOD'))
        if method=='GET' or method=='POST': method='index_html'

        URL=self.script

        # if the top object has a __bobo_traverse__ method, then use it
        # to possibly traverse to an alternate top-level object.
        if hasattr(object,'__bobo_traverse__'):
            request['URL']=URL
            try: object=object.__bobo_traverse__(request)
            except: pass            

        # Get default object if no path was specified:
        if not path:
            entry_name=method
            try:
                if hasattr(object,entry_name):
                    response.setBase(URL)
                    path=[entry_name]
                else:
                    try:
                        if object.has_key(entry_name):
                            path=[entry_name]
                    except: pass
            except: pass
            if not path: path = ['help']

        # Traverse the URL to find the object:
        request['PARENTS']=parents=[]
    
        if hasattr(object, '__of__'): 
            # Try to bind the top-level object to the request
            object=object.__of__(RequestContainer(REQUEST=request))

        steps=[]
        while path:
            entry_name,path=path[0], path[1:]
            URL="%s/%s" % (URL,quote(entry_name))
            got=0
            if entry_name:
                if entry_name[:1]=='_':
                    if debug_mode:
                        self.debugError("Object name begins with an underscore at: %s" % URL)
                    else: self.forbiddenError(entry_name)

                if hasattr(object,'__bobo_traverse__'):
                    request['URL']=URL
                    subobject=object.__bobo_traverse__(request,entry_name)
                    if type(subobject) is type(()) and len(subobject) > 1:
                        while len(subobject) > 2:
                            parents.append(subobject[0])
                            subobject=subobject[1:]
                        object, subobject = subobject
                else:
                    try:
                        subobject=getattr(object,entry_name)
                    except AttributeError:
                        got=1
                        try: subobject=object[entry_name]
                        except (KeyError, IndexError,
                                TypeError, AttributeError):
                            if entry_name=='.': subobject=object
                            elif entry_name=='..' and parents:
                                subobject=parents[-1]
                            elif debug_mode:
                                self.debugError("Cannot locate object at: %s" %URL) 
                            else: self.notFoundError(URL)

                if subobject is object and entry_name=='.':
                    URL=URL[:rfind(URL,'/')]
                else:
                    try:
                        try: doc=subobject.__doc__
                        except: doc=getattr(object, entry_name+'__doc__')
                        if not doc: raise AttributeError, entry_name
                    except:
                        if debug_mode:
                            self.debugError("Missing doc string at: %s" % URL)
                        else: self.notFoundError("%s" % (URL))

                    if hasattr(subobject,'__roles__'):
                        roles=subobject.__roles__
                    else:
                        if not got:
                            roleshack=entry_name+'__roles__'
                            if hasattr(object, roleshack):
                                roles=getattr(object, roleshack)
    
                    # Promote subobject to object
                
                    parents.append(object)
                    object=subobject

                    steps.append(entry_name)
    
                # Check for method:
                if not path:
                    if hasattr(object,method) and entry_name != method:
                        response.setBase(URL)
                        path=[method]
                    else:
                        if (hasattr(object, '__call__') and
                            hasattr(object.__call__,'__roles__')):
                            roles=object.__call__.__roles__
                        if self._hacked_path:
                            i=rfind(URL,'/')
                            if i > 0: response.setBase(URL[:i])
    
        if entry_name != method and method != 'index_html':
            if debug_mode: self.debugError("Method %s not found at: %s" % (method,URL))
            else: self.notFoundError(method)

        request.steps=steps
        parents.reverse()

        # Do authorization checks
        user=None
        i=0
        if roles is not None:

            last_parent_index=len(parents)
            if hasattr(object, '__allow_groups__'):
                groups=object.__allow_groups__
                inext=0
            else:
                inext=None
                for i in range(last_parent_index):
                    if hasattr(parents[i],'__allow_groups__'):
                        groups=parents[i].__allow_groups__
                        inext=i+1
                        break

            if inext is not None:
                i=inext

                if hasattr(groups, 'validate'): v=groups.validate
                else: v=old_validation

                auth=self.HTTP_AUTHORIZATION

                if v is old_validation and roles is UNSPECIFIED_ROLES:
                    # No roles, so if we have a named group, get roles from
                    # group keys
                    if hasattr(groups,'keys'): roles=groups.keys()
                    else:
                        try: groups=groups()
                        except: pass
                        try: roles=groups.keys()
                        except: pass

                    if groups is None:
                        # Public group, hack structures to get it to validate
                        roles=None
                        auth=''

                if v is old_validation:
                    user=old_validation(groups, request, auth, roles)
                elif roles is UNSPECIFIED_ROLES: user=v(request, auth)
                else: user=v(request, auth, roles)

                while user is None and i < last_parent_index:
                    parent=parents[i]
                    i=i+1
                    if hasattr(parent, '__allow_groups__'): 
                        groups=parent.__allow_groups__
                    else: continue
                    if hasattr(groups,'validate'): v=groups.validate
                    else: v=old_validation
                    if v is old_validation:
                        user=old_validation(groups, request, auth, roles)
                    elif roles is UNSPECIFIED_ROLES: user=v(request, auth)
                    else: user=v(request, auth, roles)
                    
            if user is None and roles != UNSPECIFIED_ROLES:
                self.unauthorized(realm,debug_mode)

        steps=join(steps[:-i],'/')
        if user is not None:
            request['AUTHENTICATED_USER']=user
            request['AUTHENTICATION_PATH']=steps
   
        # Attempt to start a transaction:
        try: transaction=get_transaction()
        except: transaction=None
        if transaction is not None:
            info="\t" + request_get('PATH_INFO')
       
            auth_user=request_get('AUTHENTICATED_USER',None)
            if auth_user is not None:
                info=("%s %s" % (steps,auth_user))+info
            transaction.begin(info)

        # Now get object meta-data to decide if and how it should be
        # called:
        object_as_function=object
                
        # First, assume we have a method:
        if hasattr(object_as_function,'im_func'):
            f=object_as_function.im_func
            c=f.func_code
            defaults=f.func_defaults
            argument_names=c.co_varnames[1:c.co_argcount]
        else:
            # Rather than sniff for FunctionType, assume its a
            # function and fall back to returning the object itself:        
            if hasattr(object_as_function,'func_defaults'):
                defaults=object_as_function.func_defaults
                c=object_as_function.func_code
                argument_names=c.co_varnames[:c.co_argcount]

                # Make sure we don't have a class that smells like a func
                if hasattr(object_as_function, '__bases__'):
                    self.forbiddenError(entry_name)
                
            else: return response.setBody(object)

        request['URL']=URL
        request['PARENT_URL']=URL[:rfind(URL,'/')]

        args=[]
        nrequired=len(argument_names) - (len(defaults or []))
        for name_index in range(len(argument_names)):
            argument_name=argument_names[name_index]
            v=request_get(argument_name, args)
            if v is args:
                if argument_name=='self': args.append(parents[0])
                elif name_index < nrequired:
                    self.badRequestError(argument_name)
                else: args.append(defaults[name_index-nrequired])
            else: args.append(v)

        args=tuple(args)
        if debug: result=self.call_object(object,args)
        else:     result=apply(object,args)

        if result and result is not response: response.setBody(result)

        if transaction: transaction.commit()

        return response

    def call_object(self,object,args):
        result=apply(object,args) # Type s<cr> to step into published object.
        return result

_l=allocate_lock()
def get_module_info(module_name, modules={},
                    acquire=_l.acquire,
                    release=_l.release,
                    ):

    if modules.has_key(module_name): return modules[module_name]

    if module_name[-4:]=='.cgi': module_name=module_name[:-4]

    acquire()
    tb=None
    try:
      try:
        module=__import__(module_name, globals(), globals(), ('__doc__',))
    
        realm=module_name
                
        # Let the app specify a realm
        if hasattr(module,'__bobo_realm__'):
            realm=module.__bobo_realm__
        elif os.environ.has_key('BOBO_REALM'):
            realm=request.environ['BOBO_REALM']
        else: realm=module_name

        # Check for debug mode
        if hasattr(module,'__bobo_debug_mode__'):
            debug_mode=not not module.__bobo_debug_mode__
        elif os.environ.has_key('BOBO_DEBUG_MODE'):
            debug_mode=lower(os.environ['BOBO_DEBUG_MODE'])
            if debug_mode=='y' or debug_mode=='yes':
                debug_mode=1
            else:
                try: debug_mode=atoi(debug_mode)
                except: debug_mode=None
        else: debug_mode=None

        # Check whether tracebacks should be hidden:
        if hasattr(module,'__bobo_hide_tracebacks__'):
            hide_tracebacks=not not module.__bobo_hide_tracebacks__
        elif os.environ.has_key('BOBO_HIDE_TRACEBACKS'):
            hide_tracebacks=lower(os.environ['BOBO_HIDE_TRACEBACKS'])
            if hide_tracebacks=='y' or hide_tracebacks=='yes':
                hide_tracebacks=1
            else:
                try: hide_tracebacks=atoi(hide_tracebacks)
                except: hide_tracebacks=None
        else: hide_tracebacks=None

        # Reset response handling of tracebacks, if necessary:
        if debug_mode or not hide_tracebacks:
            def hack_response():
                import Response
                Response._tbopen  = '<PRE>'
                Response._tbclose = '</PRE>'

            hack_response()
 
        if hasattr(module,'__bobo_before__'):
            bobo_before=module.__bobo_before__
        else: bobo_before=None
                
        if hasattr(module,'__bobo_after__'): bobo_after=module.__bobo_after__
        else: bobo_after=None
    
        # Get request data from outermost environment:
        if hasattr(module,'__request_data__'):
            request_params=module.__request_data__
        else: request_params=None
    
        # Get initial group data:
        inherited_groups=[]
        if hasattr(module,'__allow_groups__'):
            groups=module.__allow_groups__
            inherited_groups.append(groups)
        else: groups=None
    
        web_objects=None
        roles=UNSPECIFIED_ROLES
        if hasattr(module,'bobo_application'):
            object=module.bobo_application
            if hasattr(object,'__allow_groups__'):
                groups=object.__allow_groups__
                inherited_groups.append(groups)
            else: groups=None
            if hasattr(object,'__roles__'): roles=object.__roles__
        else:
            if hasattr(module,'web_objects'):
                web_objects=module.web_objects
                object=web_objects
            else: object=module
        published=web_objects
    
        try: doc=module.__doc__
        except:
            if web_objects is not None: doc=' '
            else: doc=None
    
        info= (bobo_before, bobo_after, request_params,
                inherited_groups, groups, roles,
                object, doc, published, realm, module_name,
                debug_mode)
    
        modules[module_name]=modules[module_name+'.cgi']=info

        return info
      except:
          if hasattr(sys, 'exc_info'): t,v,tb=sys.exc_info()
          else: t, v, tb = sys.exc_type, sys.exc_value, sys.exc_traceback
          v=str(v)
          raise ImportError, (t, v), tb
    finally:
        tb=None
        release()

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
                     '\([^\0- ;,=\"]+\)=\([^\0;-=\"]*\)'
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
            if not text or not strip(text): return result
            raise "InvalidParameter", text
    finally: release()

    if not already_have(name): result[name]=value

    return apply(parse_cookie,(text[l:],result))

base64=None
def old_validation(groups, request, HTTP_AUTHORIZATION,
                   roles=UNSPECIFIED_ROLES):
    global base64
    if base64 is None: import base64

    if HTTP_AUTHORIZATION:
        if lower(HTTP_AUTHORIZATION[:6]) != 'basic ':
            if roles is None: return ''
            return None
        [name,password] = split(
            base64.decodestring(
                split(HTTP_AUTHORIZATION)[-1]), ':')
    elif request.environ.has_key('REMOTE_USER'):
        name=request.environ['REMOTE_USER']
        password=None
    else:
        if roles is None: return ''
        return None

    if roles is None: return name

    keys=None
    try:
        keys=groups.keys
    except:
        try:
            groups=groups() # Maybe it was a method defining a group
            keys=groups.keys
        except: pass

    if keys is not None:
        # OK, we have a named group, so apply the roles to the named
        # group.
        if roles is UNSPECIFIED_ROLES: roles=keys()
        g=[]
        for role in roles:
            if groups.has_key(role): g.append(groups[role])
        groups=g

    for d in groups:
        if d.has_key(name) and (d[name]==password or password is None):
            return name

    if keys is None:
        # Not a named group, so don't go further
        raise 'Forbidden', (
            """<strong>You are not authorized to access this resource""")

    return None

def publish_module(module_name,
                   stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr,
                   environ=os.environ, debug=0):
    must_die=0
    status=200
    after_list=[None]
    request=None
    try:
        try:
            try:
                response=Response(stdout=stdout, stderr=stderr)
                publisher = ModulePublisher(
                    stdin=stdin, stdout=stdout, stderr=stderr,
                    environ=environ)
                response = publisher.response
                request=publisher.request
            finally:
                pass
            response = publisher.publish(module_name,after_list,
                                         debug=debug)
        except SystemExit, v:
            if hasattr(sys, 'exc_info'): must_die=sys.exc_info()
            else: must_die = SystemExit, v, sys.exc_traceback
            response.exception(must_die)
        except ImportError, v:
            if type(v) is type(()) and len(v)==3: must_die=v
            elif hasattr(sys, 'exc_info'): must_die=sys.exc_info()
            else: must_die = SystemExit, v, sys.exc_traceback
            response.exception(1, v)
        except:
            response.exception()
            status=response.getStatus()
        if response:
            response=str(response)
        if response: stdout.write(response)

        # The module defined a post-access function, call it
        if after_list[0] is not None: after_list[0]()

    finally:
        if request is not None: request.other={}

    if must_die: raise must_die[0], must_die[1], must_die[2]
    sys.exc_type, sys.exc_value, sys.exc_traceback = None, None, None
    return status

