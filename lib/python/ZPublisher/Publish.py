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

Introduction

  The Python object publisher provides a simple mechanism for publishing a
  collection of Python objects as World-Wide-Web (Web) resources without any
  plumbing (e.g. CGI) specific code.

Benefits

  - Applications do not have to include code for interfacing with the
    web server.

  - Applications can be moved from one publishing mechanism, such as
    CGI, to another mechanism, such as Fast CGI or COM, with no change.

  - Python objects are published as Python objects.  The web server
    "calls" the objects in much the same way that other Python objects
    would.

  - Automatic conversion of URL to object/sub-object traversal.

  - Automatic marshaling of form data, cookie data, and request
    meta-data to Python function arguments.

  - Automated exception handling.

  - Automatic generation of CGI headers.

  - Automated authentication and authorization.

Published objects

  Objects are published by including them in a published module.
  When a module is published, any objects that:

    - can be found in the module's global name space,

    - that do not have names starting with an underscore, 

    - that have non-empty documentation strings, and 

    - that are not modules

  are published.

  Sub-objects (or sub-sub objects, ...) of published objects are
  also published, as long as the sub-objects:
   
    - have non-empty doc strings,

    - have names that do not begin with an underscore, and

    - are not modules.

  Note that object methods are considered to be subobjects.

  Object-to-subobject traversal is done by converting steps in the URI
  path to get attribute or get item calls.  For example, in traversing
  from 'http://some.host/some_module/object' to
  'http://some.host/some_module/object/subobject', the module
  publisher will try to get 'some_module.object.subobject'.  If the
  access fails with other than an attribute error, then the object
  publisher raises a "NotFound" exception.  If the access fails with
  an attribute error, then the object publisher will try to obtain the
  subobject with: 'some_module.object["subobject"]'.  If this access
  fails, then the object publisher raises a '"Not Found"' exception.  If
  either of the accesses suceeds, then, of course, processing continues.

  During object traversal, the names '.' and '..' have special meaning
  if the application does not provide meaning for them.  If the name
  '.' is encountered and the application does not provide a value,
  then the name is effectively skipped.  For example, the path 'x/./y'
  is equivalent to 'x/y'. If the name '..' is encountered and the
  application does not provide a value, then the parent of the object
  being traversed is used.  For example, 'x/y/../z' is almost
  equivalent to 'x/z', except that 'y' is considered to be part of the
  path to 'z'.  If 'y' has a user folder, it will be consulted when
  validadting access to 'z' before a user folder in 'x' is consulted.

  Normally, URL traversal begins with the published module.  If the
  Published module has a global variable named 'bobo_application',
  then traversal begins with this object instead.

  If the final object encountered when traversing the URL has an
  'index_html' attribute, the object traversal will continue to this
  attribute.   This is useful for providing default methods for objects.

Access Control

  Object access can be further controlled via
  *roles* and *user databases*.

  The Bobo authorization model uses roles to control access to
  objects.  As Bobo traverses URLs, it checked for '__roles__'
  attributes in the objects it encounters.  The last value found
  controls access to the published object.

  If found, '__roles__' should be None or a sequence of role names.  If
  '__roles__' is 'None', then the published object is public.  If
  '__roles__' is not 'None', then the user must provide a user name and
  password that can be validated by a user database.

  User Databases

     If an object has a '__roles__' attribute that is not empty and not
     'None', Bobo tries to find a user database to authenticate the user.
     It searches for user databases by looking for an '__allow_groups__'
     attribute, first in the published object, then in it's container,
     and so on until a user database is found.  When a user database
     is found, Bobo attempts to validate the user against the user
     database.  If validation fails, then Bobo will continue searching
     for user databases until the user can be validated or until no
     more user databases can be found.
   
     User database objects
   
       The user database may be an object that provides a validate method::
   
         validate(request, http_authorization, roles)
   
       where:
   
          'request' -- a mapping object that contains request information,
   
          'http_authorization' -- the value of the HTTP Authorization header
                   or 'None' if no authorization header was provided, and 
   
          'roles' -- a list of user role names
   
       The validate method returns 'None' if it cannot validate a user and
       a user object if it can.  Normally, if the validate method returns
       'None', Bobo will try to use other user databases, however, a user
       database can prevent this by raising an exception.

       If validation succeeds Bobo assigns the user object to the
       request variable, 'AUTHENTICATED_USER'.  Bobo currently places
       no restriction on user objects.

     Mapping user databases

       If the user database is a mapping object, then the keys of the
       object are role names and values are the associated user groups for
       the roles.   Bobo attempts to validate the user by searching
       for a user name and password matching the user name and
       password given in the HTTP Authorization header in a groups for
       role names matching the roles in the published object's
       __roles__ attribute.

       If validation succeeds Bobo assigns the user name to the
       request variable, 'AUTHENTICATED_USER'.
    
     Authentication user interface

       When a user first accesses a protected object, Bobo returns an
       error response to the web browser that causes a password dialog
       to be displayed. 

     Specifying a realm name for basic authentication

       You can control the realm name used for Bobo's Basic
       authentication by providing a module variable named
       '__bobo_realm__'.

     Using the web server to perform authentication

       Some web servers cannot be coaxed into passing authentication
       information to applications.  In this case, Bobo applications
       cannot perform authentication.  If the web server is configured
       to authenticate access to a Bobo application, then the Bobo
       application can still perform authorization using the
       'REMOTE_USER' variable.  Bobo does this automatically when
       mapping user databases are used, and custom user databases may
       do this too.

       In this case, it may be necessary to provide more than one path
       to an application, one that is authenticated, and one that
       isn't, if public methods and non-public methods are
       interspursed.

  Fixed-attribute objects

      For some interesting objects, such as functions, and methods,
      it may not be possible for applications to set
      '__roles__' attributes.  In these cases, the
      object's parent object may contain attribute
      'object_name__roles__', which
      will be used as surrogates for the object's
      '__role__' attribute.

Function, method, and class objects
  
  If a published object is a function, method, or class, then the
  object will be called and the return value of the call will be
  returned as the HTTP resonse.  Calling arguments will be supplied
  from "environment variables", from URL-encoded form data, if any,
  and from HTTP cookies by matching argument names defined for the
  object with variable names.

  Accessing request data directly

    If the object being called has an argument named 'REQUEST', then
    a request object will be passed.  Request objects encapsulate
    request meta data and provide full access to all environment
    data, form data, cookies, and the input data stream (i.e. body
    data as a stream).

  Providing finer control over responses and stream output

    If the object being called has an argument named 'RESPONSE',
    then a response object will be passed.  This object can be used
    to specify HTTP headers and to perform stream-oriented output.
    Rather than returning a result, data may be output by calling
    the write and flush methods of the response object one or more
    times.  This is useful, for example, when outputing results from
    a time-consuming task, since partial results may be displayed
    long before complete results are available.

  Argument Types and File upload

    Normally, string arguments are passed to called objects. The
    called object must be prepared to convert string arguments to
    other data types, such as numbers.
    
    If file upload fields are used, however, then FileUpload objects
    will be passed instead for these fields.  FileUpload objects
    bahave like file objects and provide attributes for inspecting the
    uploaded file's source name and the upload headers, such as
    content-type. 

    If field names in form data are of the form: name:type, then an
    attempt will be to convert data from from strings to the indicated
    type.  The data types currently supported are: 

        float -- Python floating point numbers
    
        int -- Python integers
    
        long -- Python long integers
    
        string -- python strings
    
        required -- non-blank python strings

        date -- Date-time values

        list -- Python list of values, even if there is only
                one value.

        lines -- Python list of values entered as multiple lines
                 in a single field

        tokens -- Python list of values entered as multiple space-separated
                  tokens in a single field

        tuple -- Python tuple of values, even if there is only one.

        method -- Augment PATH_INFO with information from the form field.
                  (See "Method Arguments" blow.)
                  

    For example, if the name of a field in an input
    form is 'age:int', then the field value will be passed in argument,
    age, and an attempt will be made to convert the argument value to
    an integer.  This conversion also works with file upload, so using
    a file upload field with a name like myfile:string will cause the
    UploadFile to be converted to a string before being passed to the
    object.  

  Method Arguments

    Sometimes, it is desireble to control which method is called based
    on form data.  For example, one might have a form with a select
    list and want to choose which method to call depening on the item
    chosen. Similarly, one might have multiple submit buttons and want
    to invoke a different method for each button.

    Bobo provides a way to select methods using form variables through
    use of the "method" argument type.  The method type allows the
    request 'PATH_INFO' to be augmented using information from a
    form item name or value.

    If the name of a form field is ':method', then the value of the
    field is added to 'PATH_INFO'.  For example, if the original
    'PATH_INFO' is 'foo/bar' and the value of a ':method' field is
    'x/y', then 'PATH_INFO' is transformed to 'foo/bar/x/y'.  This is
    useful when presenting a select list.  Method names can be
    placed in the select option values.

    If the name of a form field ends in ':method' and is longer than 7
    characters, then the part of the name before ':method' is added to
    'PATH_INFO'.  For example, if the original 'PATH_INFO' is
    'foo/bar' and there is a 'x/y:method' field, then 'PATH_INFO' is
    transformed to 'foo/bar/x/y'.  In this case, the form value is
    ignored.  This is useful for mapping submit buttons to methods,
    since submit button values are displayed and should, therefore,
    not contain method names.

    Only one method field should be provided.  If more than one method
    field is included in the request, the behavior is undefined.

    The base HREF is set when method fields are provided.  In the
    above examples, the base HREF is set to '.../foo/bar/x'.  Of
    course, if, in this example, 'y' was an object with an index_html
    method, then the base HREF would be reset to '.../foo/bar/x/y'.

Published objects that are not functions, methods, or classes

  If a published object that is not a function, method, or class
  is accessed, then the object itself will be returned.

Return types

  A published object, or the returned value of a called published
  object can be of any Python type.  If the returned value has an
  'asHTML' method, then this method will be called to convert the
  object to HTML, otherwise the returned value will be converted to a
  string and examined to see if it appears to be an HTML document.  If
  it appears to be an HTML document, then the response content-type
  will be set to 'text/html'.  Otherwise the content-type will be set
  to 'text/plain'.

  If the returned object is None or the string representation of the
  returned object is an empty string, then the HTTP return status will
  be set to "No Content", and no body will be returned.  On some
  browsers, this will cause the displayed document to be unchanged.

Base References

  In general, in Bobo, relative URL references should be interpreted
  relative to the parent of the published object, to make it easy for
  objects to provide links to siblings.

  If 

   - the result of a request is HTML text,

   - the text does not define a 'base' tag in the 'head' portion of
     the HTML, and

   - The published object had an 'index_html' attribute that was not included
     in the request URL, 

  then a base reference will be inserted that is the URL of the
  published object.
      
Exception handling

  Unhandled exceptions are caught by the object publisher
  and are translated automatically to nicely formatted HTTP output.

  When an exception is raised, the exception type is mapped to an HTTP
  code by matching the value of the exception type with a list of
  standard HTTP status names.  Any exception types that do not match
  standard HTTP status names are mapped to "Internal Error" (500).
  The standard HTTP status names are: '"OK"', '"Created"',
  '"Accepted"', '"No Content"', '"Multiple Choices"', '"Redirect"',
  '"Moved Permanently"', '"Moved Temporarily"', '"Not Modified"',
  '"Bad Request"', '"Unauthorized"', '"Forbidden"', '"Not Found"',
  '"Internal Error"', '"Not Implemented"', '"Bad Gateway"', and
  '"Service Unavailable"', Variations on these names with different
  cases and without spaces are also valid.

  An attempt is made to use the exception value as the body of the
  returned response.  The object publisher will examine the exception
  value.  If the value is a string that contains some white space,
  then it will be used as the body of the return error message.  It it
  appears to be HTML, the the error content type will be set to
  'text/html', otherwise, it will be set to 'text/plain'.  If the
  exception value is not a string containing white space, then the
  object publisher will generate it's own error message.

  There are two exceptions to the above rule:

    1. If the exception type is: '"Redirect"', '"Multiple Choices"'
       '"Moved Permanently"', '"Moved Temporarily"', or
       '"Not Modified"', and the exception value is an absolute URI,
       then no body will be provided and a 'Location' header will be
       included in the output with the given URI.

    2. If the exception type is '"No Content"', then no body will be
       returned.

  When a body is returned, traceback information will be included in a
  comment in the output.  The module variable
  '__bobo_hide_tracebacks__' can be used to control how tracebacks are
  included.  If this variable and false, then tracebacks are included
  in PRE tags, rather than in comments.  This is very handy during
  debugging. 

Redirection

  Automatic redirection may be performed by a published object
  by raising an exception with a type and value of "Redirect" and
  a string containing an absolute URI.

The default object

  If no object is specified in a URI, then the publisher will try to
  publish the object 'index_html', if it exists, otherwise the module's
  doc string will be published.

Pre- and post-call hooks

  If a published module defines objects '__bobo_before__' or
  '__bobo_after__', then these functions will be called before 
  or after a request is processed.  One possible use for this is to
  acquire and release application locks in applications with
  background threads.

Publishing a module using CGI

    o Do not copy the module to be published to the cgi-bin
      directory.

    o Copy the files: cgi_module_publisher.pyc and CGIResponse.pyc
      to the directory containing the module to be published, or to a
      directory in the standard (compiled in) Python search path.

    o Copy the file cgi-module-publisher to the directory containing the
      module to be published.

    o Create a symbolic link from cgi-module-publisher (in the directory
      containing the module to be published) to the module name in the
      cgi-bin directory.

$Id: Publish.py,v 1.99 1998/09/21 22:49:26 jim Exp $"""
#'
#
##########################################################################
__version__='$Revision: 1.99 $'[11:-2]

import sys, os, string, cgi, regex
from string import *
import CGIResponse
from CGIResponse import Response
from urllib import quote, unquote
from cgi import FieldStorage, MiniFieldStorage

# Waaaa, I wish I didn't have to work this hard.
try: from thread import allocate_lock
except:
    class allocate_lock:
        def acquire(*args): pass
        def release(*args): pass


ListType=type([])
StringType=type('')
TupleType=type(())

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
                        if environ.has_key('PATH_INFO'):
                            path=environ['PATH_INFO']
                            while path[-1:]=='/': path=path[:-1]
                        else: path=''
                        if l: m=key
                        else: m=item
                        path="%s/%s" % (path,m)
                        other['PATH_INFO']=path
                        self._hacked_path=1
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

    def unauthorized(self, realm):
        if not (self.request.has_key('REMOTE_USER') and
                self.request['REMOTE_USER']):
            self.response['WWW-authenticate']='basic realm="%s"' % realm
        raise 'Unauthorized', (
            """<strong>You are not authorized to access this resource.
            </strong>
            """
            )

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
         object, doc, published, realm, module_name
         ) = get_module_info(module_name)
            
        after_list[0]=bobo_after

        if bobo_before is not None: bobo_before();

        if request_params: self.get_request_data(request_params)

        # Get a nice clean path list:
        path=strip(request_get('PATH_INFO'))
        if path[:1]=='/': path=path[1:]
        if path[-1:]=='/': path=path[:-1]
        path=split(path,'/')
        while path and not path[0]: path = path[1:]

        method=upper(request_get('REQUEST_METHOD'))
        if method=='GET' or method=='POST': method='index_html'

        URL=self.script

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

        # if the top object has a __bobo_traverse__ method, then use it
        # to possibly traverse to an alternate top-level object.
        if hasattr(object,'__bobo_traverse__'):
            request['URL']=URL
            try: object=object.__bobo_traverse__(request)
            except: pass            
    
        if hasattr(object, '__of__'): 
            # Try to bind the top-level object to the request
            object=object.__of__(RequestContainer(REQUEST=request))

        steps=[]
        while path:
            entry_name,path=path[0], path[1:]
            URL="%s/%s" % (URL,quote(entry_name))
            got=0
            if entry_name:
                if entry_name[:1]=='_': self.forbiddenError(entry_name)

                if hasattr(object,'__bobo_traverse__'):
                    request['URL']=URL
                    subobject=object.__bobo_traverse__(request,entry_name)
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
                            else: self.notFoundError(URL)
    
                try:
                    try: doc=subobject.__doc__
                    except: doc=getattr(object, entry_name+'__doc__')
                    if not doc: raise AttributeError, entry_name
                except: self.notFoundError("%s" % (entry_name))

                if hasattr(subobject,'__roles__'): roles=subobject.__roles__
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
                            i=string.rfind(URL,'/')
                            if i > 0: response.setBase(URL[:i])
    
        if entry_name != method and method != 'index_html':
            self.notFoundError(method)

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
                self.unauthorized(realm)

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
        if hasattr(module,'__bobo_realm__'): realm=module.__bobo_realm__
        else: realm=module_name

        # Check whether tracebacks should be hidden:
        if (hasattr(module,'__bobo_hide_tracebacks__')
            and not module.__bobo_hide_tracebacks__):
            CGIResponse._tbopen, CGIResponse._tbclose = '<PRE>', '</PRE>'
        
        if hasattr(module,'__bobo_before__'): bobo_before=module.__bobo_before__
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
                object, doc, published, realm, module_name)
    
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
    

def field2string(v):
    if hasattr(v,'read'): v=v.read()
    else: v=str(v)
    return v

def field2text(v, nl=regex.compile('\r\n\|\n\r').search):
    if hasattr(v,'read'): v=v.read()
    else: v=str(v)
    l=nl(v)
    if l < 0: return v
    r=[]
    s=0
    while l >= s:
        r.append(v[s:l])
        s=l+2
        l=nl(v,s)
    r.append(v[s:])
        
    return join(r,'\n')

def field2required(v):
    if hasattr(v,'read'): v=v.read()
    else: v=str(v)
    if strip(v): return v
    raise ValueError, 'No input for required field<p>'

def field2int(v):
    if hasattr(v,'read'): v=v.read()
    else: v=str(v)
    # we can remove the check for an empty string when we go to python 1.4
    if v: return atoi(v)
    raise ValueError, 'Empty entry when <strong>integer</strong> expected'

def field2float(v):
    if hasattr(v,'read'): v=v.read()
    else: v=str(v)
    # we can remove the check for an empty string when we go to python 1.4
    if v: return atof(v)
    raise ValueError, (
        'Empty entry when <strong>floating-point number</strong> expected')

def field2long(v):
    if hasattr(v,'read'): v=v.read()
    else: v=str(v)
    # we can remove the check for an empty string when we go to python 1.4
    if v: return atol(v)
    raise ValueError, 'Empty entry when <strong>integer</strong> expected'

def field2tokens(v):
    if hasattr(v,'read'): v=v.read()
    else: v=str(v)
    return split(v)

def field2lines(v):
    return split(field2text(v),'\n')

def field2date(v):
    from DateTime import DateTime
    if hasattr(v,'read'): v=v.read()
    else: v=str(v)
    return DateTime(v)

def field2list(v):
    if type(v) is not ListType: v=[v]
    return v

def field2tuple(v):
    if type(v) is not ListType: v=(v,)
    return tuple(v)


type_converters = {
    'float':    field2float,
    'int':      field2int,
    'long':     field2long,
    'string':   field2string,
    'date':     field2date,
    'list':     field2list,
    'tuple':    field2tuple,
    'required': field2required,
    'tokens':   field2tokens,
    'lines':    field2lines,
    'text':     field2text,
    }


class Request:
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

    def __init__(self,environ,form,stdin):
        self.environ=environ
        self.other=form
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

        if server_url[-1:]=='/': server_url=server_url[:-1]
                        
        self.base="%s/%s" % (server_url,b)
        while script[:1]=='/': script=script[1:]
        if script: self.script="%s/%s" % (server_url,script)
        else:  self.script=server_url

    def __setitem__(self,key,value):
        """Set application variables

        This method is used to set a variable in the requests "other"
        category.
        """
        
        self.other[key]=value

    set=__setitem__

    def __str__(self):

        def str(self,name):
            dict=getattr(self,name)
            return "%s:\n\t%s\n\n" % (
                name,
                join(
                    map(lambda k, d=dict: "%s: %s" % (k, `d[k]`), dict.keys()),
                    "\n\t"
                    )
                )
            
        return "%s\n%s\n" % (
            str(self,'form'),str(self,'environ'))

    __repr__=__str__

    def __getitem__(self,key,
                    default=field2list, # Any special internal marker will do
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

        if key[:1]=='U' and URLmatch(key) >= 0 and other.has_key('URL'):
            n=ord(key[3])-ord('0')
            URL=other['URL']
            for i in range(0,n):
                l=rfind(URL,'/')
                if l >= 0: URL=URL[:l]
                else: raise KeyError, key
            other[key]=URL
            return URL

        if isCGI_NAME(key) or key[:5] == 'HTTP_':
            environ=self.environ
            if environ.has_key(key): return environ[key]
            return ''

        if key=='REQUEST': return self

        if key[:1]=='B' and BASEmatch(key) >= 0 and other.has_key('URL'):
            n=ord(key[4])-ord('0')
            if n:
                v=self.script
                while v[-1:]=='/': v=v[:-1]
                v=join([v]+self.steps[:n-1],'/')
            else:
                v=self.base
                while v[-1:]=='/': v=v[:-1]
            other[key]=v
            return v

        if default is not field2list: return default

        raise KeyError, key

    __getattr__=get=__getitem__

    def has_key(self,key):
        return self.get(key, field2tuple) is not field2tuple

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
        }.has_key

                

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
        [name,password] = string.splitfields(
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

