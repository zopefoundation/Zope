#!/usr/local/bin/python 
# $What$

__doc__="""\
Python Object Publisher -- Publish Python objects on web servers

Introduction

  The Python object publisher provides a simple mechanism for publishing a
  collection of Python objects as World-Wide-Web (Web) resources without any
  plumbing (e.g. CGI) specific code.

Benefits

  - Applications do not have to include code for interfacing with the
    web server.

  - Applications can be moved from one publishing mechanism, such as
    CGI, to another mechanism, such as Fast CGI or ILU Requestor, with
    no change.

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

  Alternatively, a module variable, named 'web_objects' can be
  defined.  If this variable is defined, it should be bound to a
  mapping object that maps published names to published objects.
  Objects that are published through a module's 'web_objects' are not
  subject to the restrictions listed above. For example, modules or
  objects without documentation strings may be published by including
  them in a module's 'web_objects' attribute.

  Sub-objects (or sub-sub objects, ...) of published objects are
  also published, as long as the sub-objects:
   
    - have non-empty doc strings,

    - have names that do not begin with an underscore, and

    - are not modules.

  A sub-object that cannot have a doc strings may be published by
  including a special attribute in the containing object named:
  subobject_name__doc__.  For example, if foo.bar.spam doesn't have a
  doc string, but foo.bar has a non-empty attribute
  foo.bar.spam__doc__, then foo.bar.spam can be published.

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

  If the final object encountered when traversing the URL has an
  'index_html' attribute, the object traversal will continue to this
  attribute.   This is useful for providing default methods for objects.

  In some cases, a parent object may hold special attributed for a
  subobject.  This may be the case either when a sub-object cannot have
  the special attribute or when it is convenience for the parent
  object to manage attribute data (e.g. to share attribute data among
  multiple children).  When the object publisher looks for a special
  attribute, it first trys to get the attribute from the published
  object.  If it fails to get the special attribute, it uses the same
  access mechanism used to extract the subobject from the parent
  object to get an attribute (or item) using a name obtained by
  concatinating the sub-object name with the special attribute
  name. For example, let 'foo.bar' be a dictionary, and foo.bar.spam
  an item in the dictionary.  When attempting to obtain the special
  attribute '__roles__', the object publisher will first try to
  evaluate 'foo.bar.spam.__roles__', and then try to evaluate:
  'foo.bar["spam"+"__roles__"]'. 

Access Control

  Access to an object (and it's sub-objects) may be further restricted
  by specifying an object attribute named '__allow_groups__'.  If set,
  this attribute should contain a collection of authorization groups.
  The '__allow_groups__' attribute may be a mapping object, in which
  case it is a collection of named groups.  Alternatively, the
  '__allow_groups__' attribute may be a sequence, in which case it is
  a collection of named groups.  Each group must be a dictionary that
  use names as keys (i.e. sets of names).  The values in these
  dictionaries may contain passwords for authenticating each of the
  names.  The basic authentication realm name used is
  'module_name.server_name', where 'module_name' is the name of the
  module containing the published objects, and server_name is the name
  of the web server.

  The module used to publish an object may contain it's own
  '__allow_groups__' attribute, thereby limiting access to all of the
  objects in a module.

  If multiple objects in the URI path have '__allow_groups__'
  attributes, then the '__allow_groups__' attribute from the last
  object in the path that has this attribute will be used.  The
  '__allow_groups__' attribute for a subobject overides
  '__allow_groups__' attributes for containing objects, however, if
  named groups are used, group data from containing objects may be
  acquired by contained objects.  If a published object uses named
  groups, then for each named group in the published object, group
  data from groups with the same name in container objects will be
  acquired from container objects.

  If the name of a group is the python object, 'None', then data from
  named groups in container objects will be acquired even if the
  group names don't appear in the acquiring object.

  When group data are acquired, then acquired data is appended to
  the existing data.  When groups contain names and passwords,
  individual user names may have multiple passwords if they appear in
  multiple groups.

  Note that an object may have an '__allow_groups__' attribute that is
  set to None, in which case the object will be public, even if
  containing objects are not.

  Roles

      Meaning of __roles__:

         None  -- Public
         False and not None -- private
         A sequence of role names.

  Fixed-attribute objects

      For some interesting objects, such as functions, and methods,
      it may not be possible for applications to set
      '__roles__' attributes.  In these cases, the
      object's parent object may contain attribute
      'object_name__roles__', which
      will be used as surrogates for the object's
      '__role__' attribute.

  Determining the authenticated user name

      If authentication is performed, then the name of the
      authenticated user is saved in the request with the name
      'AUTHENTICATED_USER', and will be passed to called objects
      through the argument name 'AUTHENTICATED_USER'.

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
    
	regex -- Python case-sensitive regular expressions
    
	Regex -- Python case-insensitive regular expressions
    
	regexs -- Multiple Python case-sensitive regular expressions
	          separated by spaces
    
	Regexs -- Multiple Python case-insensitive regular expressions
	          separated by spaces

	date -- Date-time values

        list -- Python list of values, even if there is only
	        one value.

        lines -- Python list of values entered as multiple lines
	         in a single field

        tokens -- Python list of values entered as multiple space-separated
	          tokens in a single field

        tuple -- Python tuple of values, even if there is only one.

    For example, if the name of a field in an input
    form is age:int, then the field value will be passed in argument,
    age, and an attempt will be made to convert the argument value to
    an integer.  This conversion also works with file upload, so using
    a file upload field with a name like myfile:string will cause the
    UploadFile to be converted to a string before being passed to the
    object.  

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

  A special case is when the returned object is a two-element tuple.
  If the return object is a two-element tuple, then the first element
  will be converted to a string and treated as an HTML title, and
  the second element will be converted to a string and treated as
  the contents of an HTML body. An HTML document is created and
  returned (with type text/html) by adding necessary html, head,
  title, and body tags.

  If the returned object is None or the string representation of the
  returned object is an empty string, then HTTP the return status will
  be set "No Content", and no body will be returned.  On some
  browsers, this will cause the displayed document to be unchanged.

Base References

  If result of a request is HTML text and the text does not define a
  'base' tag in the 'head' portion of the HTML, then a base reference
  will be inserted that is the location of the directory in which the
  published module was published, such as a cgi-directory.  If the
  HTML text contains a base reference that begins with a slash, then
  the server URL will be prepended to the reference.  If the base
  reference is a relative reference beginning with a dot, then an
  absolute reference will be constructed from the effective URL used
  to access the published object and from the relative reference. 

Providing On-Line help

  On-line help is provided for published objects, both explicitly and
  implicitly.  To provide on-line help for an object, simply provide a
  'help' attribute for the object.  If a 'help' attribute is not
  provided, then the object's documentation string is used. When a URI
  like: 'http:/some.server/cgi-bin/some_module/foo/bar/help' is
  presented to the publisher, it will try to access the 'help'
  attribute of 'some_module.foo.bar'.  If the object does not have a
  'help' attribute, then the object's documentation string will be
  returned.
      
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
  comment in the output. 

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

Examples

  Consider the following example:
  
        "sample.py -- sample published module"

	# URI: http://some.host/cgi-bin/sample/called
	_called=0
	def called():
	    "Report how many times I've been called"
	    global _called
	    _called=_called+1
	    return _called
	
	# URI: http://some.host/cgi-bin/sample/hi
	def hi():
	    "say hello"
	    return "<html><head><base href=spam></head>hi"
	
	# URI: http://some.host/cgi-bin/sample/add?x=1&y=2
	def add(x,y):
	    "add two numbers"
	    from string import atof
	    return atof(x)+atof(y)
	
	# Note that doc is not published
	def doc(m):
	  d={}
	  exec "import " + m in d
	  return d[m].__doc__
	
	# URI: http://some.host/cgi-bin/sample/spam
	class spam:
	    "spam is good"
	
	    __allow_groups__=[{"jim":1, "super":1}]
	
	    # URI: http://some.host/cgi-bin/sample/aSpam/hi
	    def hi(self):
	      return self.__doc__
	
	    __super_group=[{"super":1}]

	    # URI: http://some.host/cgi-bin/sample/aSpam/eat?module_name=foo
	    # Note that eat requires "super" access.
	    eat__allow_groups__=__super_group
	    def eat(self,module_name):
		"document a module"
		if not module_name:
		    raise "BadRequest", "The module name is blank"
		return doc(module_name)

	    # URI: http://some.host/cgi-bin/sample/aSpam/list
	    # Here we have a stream output example.
	    # Note that only jim and super can use this.
    	    def list(self, RESPONSE):
		"list some elements"
		RESPONSE.setCookie("spam","eggs",path="/")
		RESPONSE.write("<html><head><title>A list</title></head>")
		RESPONSE.write("list: \\n")
		for i in range(10): RESPONSE.write("\\telement %d" % i)
		RESPONSE.write("\\n")
	
	
	# URI: http://some.host/cgi-bin/sample/aSpam
	aSpam=spam()
	
	# We create another spam that paul can use,
	# but he still can't eat.
	# URI: http://some.host/cgi-bin/sample/moreSpam
	moreSpam=spam()
	moreSpam.__dict__['__allow_groups__']=[{'paul':1}]
	
	
	# URI: http://some.host/cgi-bin/sample/taste
	def taste(spam):
	    "a favorable reviewer"
	    return spam,'yum yum, I like ' + spam
	
	# If we uncomment this, then only hi and add can be used, but
	# with the names greet and addxy.
	# web_objects={'greet':hi, 'addxy':add}


Publishing a module using CGI

    o Do not copy the module to be published to the cgi-bin
      directory.

    o Copy the files: cgi_module_publisher.pyc and CGIResponse.pyc,
      and newcgi.pyc, to the directory containing the
      module to be published, or to a directory in the standard
      (compiled in) Python search path.

    o Copy the file cgi-module-publisher to the directory containing the
      module to be published.

    o Create a symbolic link from cgi-module-publisher (in the directory
      containing the module to be published) to the module name in the
      cgi-bin directory.

Publishing a module using Fast CGI

    o Copy the files: cgi_module_publisher.pyc and CGIResponse.pyc,
      and newcgi.pyc, to the directory containing the
      module to be published, or to a directory in the standard
      (compiled in) Python search path.

    o Copy the file fcgi-module-publisher to the directory containing the
      module to be published.

    o Create a symbolic link from fcgi-module-publisher (in the directory
      containing the module to be published) to the module name in some
      directory accessable to the Fast CGI-enabeled web server.
	
    o Configure the Fast CGI-enabled web server to execute this
      file.

$Id: Publish.py,v 1.55 1997/09/26 19:15:47 jim Exp $"""
#'
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
# See end of file for change log.
#
##########################################################################
__version__='$Revision: 1.55 $'[11:-2]


def main():
    # The "main" program for this module
    pass


if __name__ == "__main__": main()

import sys, os, string, types, cgi, regex, regsub, base64
from string import *
from CGIResponse import Response
from urllib import quote, unquote
from cgi import FieldStorage, MiniFieldStorage

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

    def __init__(self,
		 stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr,
		 environ=os.environ):
	self.environ=environ
	fp=None
	try:
	    if environ['REQUEST_METHOD'] != 'GET': fp=stdin
	except: pass

	try:
	    self.HTTP_AUTHORIZATION=environ['HTTP_AUTHORIZATION']
	    del environ['HTTP_AUTHORIZATION']
	except:
	    try:
		self.HTTP_AUTHORIZATION=environ['HTTP_CGI_AUTHORIZATION']
		del environ['HTTP_CGI_AUTHORIZATION']
	    except: pass

	form={}
	fs=FieldStorage(fp=fp,environ=environ,keep_blank_values=1)
	try: fslist=fs.list
	except: fslist=None
	if fslist is None: form={'BODY':fs.value}
	else:
	    tuple_items={}

	    type_re=regex.compile(':[a-zA-Z][a-zA-Z0-9_]+')
	    type_search=type_re.search
	    lt=type([])
	    CGI_name=isCGI_NAME
	    for item in fslist:
		key=unquote(item.name)
		
		try:
		    if (item.file and
			(item.filename is not None or
			 'content-type' in map(lower,
					       item.headers.keys()))):
		        item=FileUpload(item)
		    else:
			item=item.value
		except: pass

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
		    else:
			item=type_converters[type_name](item)
		    l=type_search(key)
		    
		# Filter out special names from form:
		if CGI_name(key) or key[:5]=='HTTP_': continue

		try:
		    found=form[key]
		    if type(found) is lt: found.append(item)
		    else:
			found=[found,item]
			form[key]=found
		except:
		    if seqf: item=[item]
		    form[key]=item

	    for key in tuple_items.keys(): form[key]=tuple(form[key])

	# Cookie values should *not* be appended to existing form
	# vars with the same name - they are more like default values
	# for names not otherwise specified in the form.

	if environ.has_key('HTTP_COOKIE'):
	    d=parse_cookie(self.environ['HTTP_COOKIE'])
	    for k in d.keys():
		if not form.has_key(k):
		    form[k]=d[k]

        request=self.request=Request(environ,form,stdin)
	self.response=Response(stdout=stdout, stderr=stderr)
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
	    "\n<!--\n%s\n-->" % entry), sys.exc_traceback

    forbiddenError=notFoundError  # If a resource is forbidden,
                                  # why reveal that it exists?

    def badRequestError(self,name):
	if regex.match('^[A-Z_0-9]+$',name) >= 0:
	    raise 'InternalError', self.html(
		"Internal Error",
		"Sorry, an internal error occurred in this resource.")

	raise 'BadRequest',self.html(
	    "Invalid request",
	    "The parameter, %s, was omitted from the request."
	    "<!--%s-->"
	    % (name,self.request))

    def unauthorized(self, realm):
	self.response['WWW-authenticate']='basic realm="%s"' % realm
	raise 'Unauthorized', (
	    """<strong>You are not authorized to access this resource.
	    </strong>
	    """
	    )

    def forbiddenError(self,object=None):
	raise 'NotFound',self.html(
	    "Resource not found",
	    "Sorry, the requested document does not exist.\n"
	    "<!--%s-->" % object)

    def get_request_data(self,request_params):
	try: request_params=request_params()
	except: pass
	for key in request_params.keys():
		self.request[key]=request_params[key]


    def get_module_info(self, server_name, module_name, module):

	realm="%s.%s" % (module_name,server_name)
		
	try: bobo_before=module.__bobo_before__
	except: bobo_before=None

	try: bobo_after=module.__bobo_after__
	except: bobo_after=None

	# Get request data from outermost environment:
	try: request_params=module.__request_data__
	except: request_params=None

	# Get initial group data:
	inherited_groups=[]
	try:
	    groups=module.__allow_groups__
	    inherited_groups.append(groups)
	except: groups=None

	web_objects=None
	try:
	    object=module.bobo_application
	    try:
		groups=object.__allow_groups__
		inherited_groups.append(groups)
	    except: groups=None
	    try: roles=object.__roles__
	    except: roles=UNSPECIFIED_ROLES
	except: 
	    try:
		web_objects=module.web_objects
		object=web_objects
	    except: object=module
	published=web_objects

	try: doc=module.__doc__
	except:
	    if web_objects is not None: doc=' '
	    else: doc=None
	
	return (bobo_before, bobo_after, request_params,
		inherited_groups, groups, roles,
		object, doc, published, realm)
		

    def publish(self, module_name, after_list, published='web_objects',
		imported_modules={}, module_dicts={},debug=0):

        # First check for "cancel" redirect:
	cancel=''
	try:
	    if lower(self.request['SUBMIT'])=='cancel':
		cancel=self.request['CANCEL_ACTION']
	except: pass
	if cancel:
	    raise 'Redirect', cancel

	if module_name[-4:]=='.cgi': module_name=module_name[:-4]
	self.module_name=module_name
	request=self.request
	response=self.response
	server_name=request.SERVER_NAME

	try:
	    (bobo_before, bobo_after, request_params,
	     inherited_groups, groups, roles,
	     object, doc, published, realm
	     ) = info = module_dicts[server_name, module_name]
	except:
	    info={}
	    try:
		exec 'import %s' % module_name in info
		info=self.get_module_info(server_name, module_name,
					  info[module_name])
		module_dicts[server_name, module_name]=info
		(bobo_before, bobo_after, request_params,
		 inherited_groups, groups, roles,
		 object, doc, published, realm
		 ) = info
	    except: raise ImportError, (
		sys.exc_type, sys.exc_value, sys.exc_traceback)
	    
	after_list[0]=bobo_after

	if bobo_before is not None: bobo_before();

	if request_params: self.get_request_data(request_params)

	# Get a nice clean path list:
	path=strip(request['PATH_INFO'])
	if path[:1]=='/': path=path[1:]
	if path[-1:]=='/': path=path[:-1]
	path=split(path,'/')
	while path and not path[0]: path = path[1:]

	method=upper(request['REQUEST_METHOD'])
	if method=='GET' or method=='POST': method='index_html'

    	# Get default object if no path was specified:
    	if not path:
    	    entry_name=method
    	    try:
    		if hasattr(object,entry_name):
    		    path=[entry_name]
    		else:
    		    try:
    			if object.has_key(entry_name):
    			    path=[entry_name]
    		    except: pass
    	    except: pass
    	    if not path: path = ['help']

	# Traverse the URL to find the object:
	URL=self.script
	parents=[]
    
	try:  # Try to bind the top-level object to the request
	    object=object.__of__(RequestContainer(REQUEST=self.request))
	except: pass

	steps=[]
	while path:
	    entry_name,path=path[0], path[1:]
	    URL="%s/%s" % (URL,quote(entry_name))
	    got=0
	    if entry_name:
		if entry_name[:1]=='_': self.forbiddenError(entry_name)
		try: traverse=object.__bobo_traverse__
		except: traverse=None
		if traverse is not None:
		    request['URL']=URL
		    subobject=traverse(request,entry_name)
		else:
		    try:
			subobject=getattr(object,entry_name)
		    except AttributeError:
			try:
			    subobject=object[entry_name]
			    got=1
			except:
			    self.notFoundError("%s" % (entry_name))
    
		try:
		    try: doc=subobject.__doc__
		    except: doc=getattr(subobject, entry_name+'__doc__')
		    if not doc: raise AttributeError, entry_name
		except: self.notFoundError("%s" % (entry_name))
		
		try: roles=subobject.__roles__
		except:
		    if not got:
			try: roles=getattr(object,entry_name+'__roles__')
			except:
			    if (entry_name=='manage' or
				entry_name[:7]=='manage_'):
				roles='manage',
    
		# Promote subobject to object
		parents.append(object)
		object=subobject

		steps.append(entry_name)
    
		# Check for method:
		if (not path and hasattr(object,method) and
		    entry_name != method):
		    response.setBase(URL+'/','')
		    path=[method]
    
	if entry_name != method and method != 'index_html':
	    self.notFoundError(method)
	
	parents.append(object)
	parents.reverse()

	# Do authorization checks
	user=None
	i=0
	if roles is not None:

	    last_parent_index=len(parents)
	    for i in range(last_parent_index):
		try: groups=parents[i].__allow_groups__
		except: groups=-1
		if groups == -1: continue

		try: v=groups.validate
		except: v=old_validation

		if v is old_validation and roles is UNSPECIFIED_ROLES:
		    # No roles, so if we have a named group, get roles from
		    # group keys
		    try: roles=groups.keys()
		    except AttributeError:
			try: groups=groups()
			except: pass
			try: roles=groups.keys()
			except: pass

		    if groups is None: break # Public group

		try: auth=self.HTTP_AUTHORIZATION
		except: self.unauthorized(realm)

		if v is old_validation:
		    user=old_validation(groups, auth, roles)
		elif roles is UNSPECIFIED_ROLES: user=v(request, auth)
		else: user=v(request, auth, roles)

		while user is None and i < last_parent_index:
		    try: groups=parents[i].__allow_groups__
		    except: groups=-1
		    i=i+1
		    if groups == -1: continue
		    try: v=groups.validate
		    except: v=old_validation
		    if v is old_validation:
			user=old_validation(groups, auth, roles)
		    elif roles is UNSPECIFIED_ROLES: user=v(request, auth)
		    else: user=v(request, auth, roles)
		    
		if user is None: self.unauthorized(realm)

		break

	steps=join(steps[:-i],'/')
	if user is not None:
	    request['AUTHENTICATED_USER']=user
	    request['AUTHENTICATION_PATH']=steps
	del parents[0]
   
	# Attempt to start a transaction:
	try: transaction=get_transaction()
	except: transaction=None
	if transaction is not None:
	    info="\t" + request['PATH_INFO']
	    try: info=("%s %s" % (steps,request['AUTHENTICATED_USER']))+info
	    except: pass
	    transaction.begin(info)

	# Now get object meta-data to decide if and how it should be
	# called:
	object_as_function=object	
	if type(object_as_function) is types.ClassType:
	    if hasattr(object_as_function,'__init__'):
		object_as_function=object_as_function.__init__
	    else:
		def function_with_empty_signature(): pass
		object_as_function=function_with_empty_signature
		
	# First, assume we have a method:
	try:
	    defaults=object_as_function.im_func.func_defaults
	    argument_names=(
		object_as_function.im_func.
		func_code.co_varnames[
		    1:object_as_function.im_func.func_code.co_argcount])
	except:
	    # Rather than sniff for FunctionType, assume its a
	    # function and fall back to returning the object itself:	    
	    try:
		defaults=object_as_function.func_defaults
		argument_names=object_as_function.func_code.co_varnames[
		    :object_as_function.func_code.co_argcount]
	    except:
		return response.setBody(object)

	request['RESPONSE']=response
	request['URL']=URL
	request['PARENT_URL']=URL[:rfind(URL,'/')]
	if parents:
	    selfarg=parents[0]
	    for i in range(len(parents)):
		try:
		    p=parents[i].aq_self
		    parents[i]=p
		except: pass
	request['PARENTS']=parents

	args=[]
	nrequired=len(argument_names) - (len(defaults or []))
	for name_index in range(len(argument_names)):
	    argument_name=argument_names[name_index]
	    try:
		v=request[argument_name]
		args.append(v)
	    except (KeyError,AttributeError,IndexError):
		if argument_name=='self': args.append(selfarg)
		elif name_index < nrequired:
		    self.badRequestError(argument_name)
		else:
		    args.append(defaults[name_index-nrequired])
	    except:
		raise 'BadRequest', ('<strong>Invalid entry for %s </strong>'
				     % argument_name)

	if debug: result=self.call_object(object,tuple(args))
	else:     result=apply(object,tuple(args))

	if result and result is not response: response.setBody(result)

	if transaction: transaction.commit()

	return response

    def call_object(self,object,args):
	result=apply(object,args) # Type s<cr> to step into published object.
	return result

def str_field(v):
    if type(v) is types.ListType:
	return map(str_field,v)

    if type(v) is types.InstanceType and v.__class__ is FieldStorage:
        v=v.value
    elif type(v) is not types.StringType:
	try:
	    if v.file:
		v=v.file
	    else:
		v=v.value
	except: pass
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
	try: methods=file.__methods__
	except: methods= ['close', 'fileno', 'flush', 'isatty',
			  'read', 'readline', 'readlines', 'seek',
			  'tell', 'truncate', 'write', 'writelines']
	for m in methods:
	    try: self.__dict__[m]=getattr(file,m)
	    except: pass

	self.headers=aFieldStorage.headers
	self.filename=aFieldStorage.filename
    

def field2string(v):
    try: v=v.read()
    except: v=str(v)
    return v

def field2text(v, nl=regex.compile('\r\n\|\n\r'), sub=regsub.gsub):
    try: v=v.read()
    except: v=str(v)
    v=sub(nl,'\n',v)
    return v

def field2required(v):
    try: v=v.read()
    except: v=str(v)
    if strip(v): return v
    raise ValueError, 'No input for required field'

def field2int(v):
    try: v=v.read()
    except: v=str(v)
    # we can remove the check for an empty string when we go to python 1.4
    if v: return atoi(v)
    raise ValueError, 'Empty entry when integer expected'

def field2float(v):
    try: v=v.read()
    except: v=str(v)
    # we can remove the check for an empty string when we go to python 1.4
    if v: return atof(v)
    raise ValueError, 'Empty entry when floating-point number expected'

def field2long(v):
    try: v=v.read()
    except: v=str(v)
    # we can remove the check for an empty string when we go to python 1.4
    if v: return atol(v)
    raise ValueError, 'Empty entry when integer expected'

def field2Regex(v):
    try: v=v.read()
    except: v=str(v)
    if v: return regex.compile(v)

def field2regex(v):
    try: v=v.read()
    except: v=str(v)
    if v: return regex.compile(v,regex.casefold)

def field2Regexs(v):
    try: v=v.read()
    except: v=str(v)
    v= map(lambda v: regex.compile(v), split(v))
    if v: return v

def field2regexs(v):
    try: v=v.read()
    except: v=str(v)
    v= map(lambda v: regex.compile(v, regex.casefold), split(v))
    if v: return v

def field2tokens(v):
    try: v=v.read()
    except: v=str(v)
    return split(v)

def field2lines(v, crlf=regex.compile('\r\n\|\n\r')):
    try: v=v.read()
    except: v=str(v)
    v=regsub.gsub(crlf,'\n',v)
    return split(v,'\n')

def field2date(v):
    from DateTime import DateTime
    try: v=v.read()
    except: v=str(v)
    return DateTime(v)

def field2list(v):
    if type(v) is not types.ListType: v=[v]
    return v

def field2tuple(v):
    if type(v) is not types.ListType: v=(v,)
    return tuple(v)


type_converters = {
    'float':	field2float,
    'int': 	field2int,
    'long':	field2long,
    'string':	field2string,
    'date':	field2date,
    'list':	field2list,
    'tuple':	field2tuple,
    'regex':	field2regex,
    'Regex':	field2Regex,
    'regexs':	field2regexs,
    'Regexs':	field2Regexs,
    'required':	field2required,
    'tokens':	field2tokens,
    'lines':	field2lines,
    'text':     field2text,
    }


class Request:
    """\
    Model HTTP request data.
    
    This object provides access to request data.  This includes, the input headers,
    form data, server data, and cookies.

    Request objects are created by the object publisher and will be
    passed to published objects through the argument name, REQUEST.

    The request object is a mapping object that represents a collection of variable
    to value mappings.  In addition, variables are divided into four categories:

      - Environment variables

        These variables include input headers, server data, and other
        request-related data.  The variable names are as 
        <a href="http://hoohoo.ncsa.uiuc.edu/cgi/env.html">specified</a>
        in the
	<a href="http://hoohoo.ncsa.uiuc.edu/cgi/interface.html">CGI specification</a>

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

	b=script=strip(environ['SCRIPT_NAME'])
	while b and b[-1]=='/': b=b[:-1]
	p = rfind(b,'/')
	if p >= 0: b=b[:p+1]
	else: b=''
	while b and b[0]=='/': b=b[1:]
	try:
	    try:
		server_url="http://%s" % strip(environ['HTTP_HOST'])
	    except:
		server_url=strip(environ['SERVER_URL'])
	    if server_url[-1:]=='/': server_url=server_url[:-1]
	except:
	    server_port=environ['SERVER_PORT']
	    server_url=('http://'+
			strip(environ['SERVER_NAME']) +
			(server_port and ':'+server_port)
			)
			
	self.base="%s/%s" % (server_url,b)
	while script[:1]=='/': script=script[1:]
	self.script="%s/%s" % (server_url,script)

    def __setitem__(self,key,value):
	"""Set application variables

	This method is used to set a variable in the requests "other"
	category.
	"""
	
	self.other[key]=value

    def __str__(self):

	def str(self,name):
	    dict=getattr(self,name)
	    return "%s:\n\t%s\n\n" % (
		name,
		join(
		    map(lambda k, d=dict: "%s: %s" % (k, d[k]), dict.keys()),
		    "\n\t"
		    )
		)
	    
	return "%s\n%s\n" % (
	    str(self,'other'),str(self,'environ'))

    __repr__=__str__

    def has_key(self,key):
	try:
	    self[key]
	    return 1
	except: return 0

    def __getitem__(self,key,
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
	try: return other[key]
	except: pass

	if URLmatch(key) >= 0 and other.has_key('URL'):
	    n=ord(key[3])-ord('0')
	    URL=other['URL']
	    for i in range(0,n):
		l=rfind(URL,'/')
		if l >= 0: URL=URL[:l]
		else: raise KeyError, key
	    other[key]=URL
	    return URL

	if isCGI_NAME(key) or key[:5] == 'HTTP_':
	    try: return self.environ[key]
	    except: return ''

	if key=='REQUEST': return self

        if BASEmatch(key) >= 0 and other.has_key('URL'):
            n=ord(key[4])-ord('0')
            URL=other['URL']
            baselen=len(self.base)
            for i in range(0,n):
                baselen=find(URL,'/',baselen+1)
                if baselen < 0:
                    baselen=len(URL)
                    break
            base=URL[:baselen]
            if base[-1:]=='/': base=base[:-1]
            other[key]=base
            return base

	raise KeyError, key

    __getattr__=__getitem__


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

		

def parse_cookie(text,
		 result=None,
		 parmre=regex.compile(
		     '\([\0- ]*'
		     '\([^\0- ;,=\"]+\)=\([^\0- =\"]+\)'
		     '\([\0- ]*[;,]\)?[\0- ]*\)'
		     ),
		 qparmre=regex.compile(
		     '\([\0- ]*'
		     '\([^\0- ;,=\"]+\)="\([^"]*\)\"'
		     '\([\0- ]*[;,]\)?[\0- ]*\)'
		     ),
		 ):

    if result is None: result={}
    
    if parmre.match(text) >= 0:
	name=parmre.group(2)
	value=parmre.group(3)
	l=len(parmre.group(1))
    elif qparmre.match(text) >= 0:
	name=qparmre.group(2)
	value=qparmre.group(3)
	l=len(qparmre.group(1))
    else:
	if not text or not strip(text): return result
	raise "InvalidParameter", text
    
    result[name]=value

    return apply(parse_cookie,(text[l:],result))

def old_validation(groups, HTTP_AUTHORIZATION, roles=UNSPECIFIED_ROLES):
    if lower(HTTP_AUTHORIZATION[:6]) != 'basic ': return None
    [name,password] = string.splitfields(
	    base64.decodestring(
		split(HTTP_AUTHORIZATION)[-1]), ':')

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
	if d.has_key(name) and d[name]==password: return name

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
    try:
	response=Response(stdout=stdout, stderr=stderr)
	publisher = ModulePublisher(stdin=stdin, stdout=stdout, stderr=stderr,
				    environ=environ)
	response = publisher.response
	response = publisher.publish(module_name,after_list,debug=debug)
    except SystemExit:
	must_die=1
	response.exception(must_die)
    except ImportError, v:
	if type(v)==types.TupleType and len(v)==3:
	    sys.exc_type, sys.exc_value, sys.exc_traceback = v
	must_die=1
	response.exception(must_die)
    except:
	status=response.getStatus()
	response.exception()
    if response:
	response=str(response)
    if response: stdout.write(response)

    # The module defined a post-access function, call it
    if after_list[0] is not None: after_list[0]()

    if must_die:
	raise sys.exc_type, sys.exc_value, sys.exc_traceback
    sys.exc_type, sys.exc_value, sys.exc_traceback = None, None, None
    return status

#
# $Log: Publish.py,v $
# Revision 1.55  1997/09/26 19:15:47  jim
# Added url unquoting of form field names.
#
# Revision 1.54  1997/09/24 18:47:18  jim
# Fixed bug in handling of case with body and no form data.
#
# Revision 1.53  1997/09/23 10:32:57  jim
# Added machinery to compute AUTHENTICATION_PATH, which is used, with
# AUTHENTICATED_USER to label transactions.
#
# Revision 1.52  1997/09/11 21:27:45  jim
# *** empty log message ***
#
# Revision 1.51  1997/09/09 23:00:55  brian
# Fixed cookie error: cookies should not be appended to explicit form
# values (thus possibly changing the expected type and causing havoc).
# Form values now override cookie-based values.
#
# Revision 1.50  1997/09/09 20:56:12  jim
# *** empty log message ***
#
# Revision 1.49  1997/09/09 20:25:21  jim
# Hopefully fixed cookie parsing.
#
# Revision 1.48  1997/09/08 14:47:11  jim
# Got cookies out of request str.
#
# Revision 1.47  1997/09/02 21:18:53  jim
# Implemented new authorization model.
# No longer use Realm module.
#
# Revision 1.46  1997/07/28 22:01:58  jim
# Tries to get rid of base ref.
#
# Revision 1.45  1997/07/28 21:46:17  jim
# Added roles.
# Tries to get rid of base ref.
# Added check for groups function that doesn't return dict.
#
# Revision 1.44  1997/06/13 16:02:10  jim
# Fixed bug in computation of transaction info that made user
# authentication required.
#
# Revision 1.43  1997/05/14 15:07:22  jim
# Added session domain to user id, for generating session info.
#
# Revision 1.42  1997/04/23 20:04:46  brian
# Fixed change that got around HTTP_CGI_AUTHORIZATION hack.
#
# Revision 1.41  1997/04/11 22:46:26  jim
# Several changes related to traversal.
#
# Revision 1.40  1997/04/09 21:06:20  jim
# Changed the way allow groups are composed to avoid unnecessary
# composition.
#
# Added a little value caching in requests.
#
# Changed the way cookies are parsed to support quoted cookie values.
#
# Revision 1.39  1997/04/04 15:32:11  jim
# *Major* changes to:
#
#   - Improve speed,
#   - Reduce stuttering,
#   - Add request meta-data to transactions.
#
# Revision 1.38  1997/03/26 22:11:52  jim
# Added support for OM's HTTP_HOST variable to get base ref.  This seems
# to make authentication slightly less annoying.
#
# Revision 1.37  1997/03/26 19:05:56  jim
# Added fix to avoid circular references through parents with
# acquisition.
#
# Revision 1.36  1997/03/20 22:31:46  jim
# Added logic to requote URL components as I re-build URL path.
#
# Revision 1.35  1997/02/14 21:53:34  jim
# Added logic to make REQUEST and RESPONSE available for acquisition
# by published objects.
#
# Revision 1.34  1997/02/07 18:42:34  jim
# Changed to use standard cgi module. Yey!!!
# This incorprates fixed binary data handling and get's rid of newcgi.
# Note that we need a new fix for windows. :-(
#
# Revision 1.33  1997/02/07 16:00:46  jim
# Made "method" check more general by trying to get im_func rather than
# by testing for type.MethodType. Du.
#
# Revision 1.32  1997/02/07 14:41:32  jim
# Fixed bug in 'lines' conversion and fixed documentation for
# 'required'.
#
# Revision 1.31  1997/01/30 00:50:18  jim
# Added has_key method to Request
#
# Revision 1.30  1997/01/28 23:04:10  jim
# *** empty log message ***
#
# Revision 1.29  1997/01/28 23:02:49  jim
# Moved log.
# Added new data type conversion options.
#
# Revision 1.28  1997/01/08 23:22:45  jim
# Added code to overcome Python 1.3 bug in string conversion functions.
#
# Revision 1.27  1996/12/30 14:36:12  jim
# Fixed a spelling error.
#
# Revision 1.26  1996/11/26 22:06:18  jim
# Added support for __bobo_before__ and __bobo_after__.
#
# Revision 1.25  1996/11/06 14:27:09  jim
# Added logic to return status code from publish method.
# This is needed by the Bobo server.
#
# Revision 1.24  1996/10/29 19:21:43  jim
# Changed rule (and terminology) for acquiring authorization data
# so that a subobject can aquire data from a container even if an
# intervening object does not use named groups.
#
# Added better string formating of requests.
#
# Revision 1.23  1996/10/28 22:13:45  jim
# Fixed bug in last fix.
#
# Revision 1.22  1996/10/25 19:34:27  jim
# Fixed bug in handling of import errors.
#
# Revision 1.21  1996/10/15 15:45:35  jim
# Added tuple argument type and enhances error handling.
#
# Revision 1.20  1996/09/16 14:43:27  jim
# Changes to make shutdown methods work properly.  Now shutdown methods
# can simply sys.exit(0).
#
# Added on-line documentation and debugging support to bobo.
#
# Revision 1.19  1996/09/13 22:51:35  jim
# *** empty log message ***
#
# Revision 1.18  1996/08/30 23:40:40  jfulton
# Fixed bug in argument marshalling!!!
#
# Revision 1.17  1996/08/30 17:08:53  jfulton
# Disallowed index_html/index_html.
#
# Revision 1.16  1996/08/29 22:20:26  jfulton
# *** empty log message ***
#
# Revision 1.15  1996/08/07 19:37:54  jfulton
# Added:
#
#   - Regex, regex input types,
#   - New rule for acquiring allow groups,
#   - Support for index_html attribute,
#   - Support for relative base refs
#   - Added URL as magic variable
#   - Added error checking of typed fields
#
# Revision 1.14  1996/08/05 11:33:54  jfulton
# Added first cut at group composition.
#
# Revision 1.13  1996/07/25 16:42:48  jfulton
# - Added FileUpload objects.
# - Added logic to check for non-file fields in forms with file upload.
# - Added new type conversion types: string (esp for use with file-upload)
#   and date.
#
# Revision 1.12  1996/07/25 12:39:09  jfulton
# Added support for __allow_groups__ method.
# Made auto-generation of realms smarter about realm names.
#
# Revision 1.11  1996/07/23 20:56:40  jfulton
# Updated the documentation.
#
# Revision 1.10  1996/07/23 20:48:55  jfulton
# Changed authorization model so that sub-object allow_groups override,
# rather than augment (tighten) parent groups.
#
# Note that now a valid group is None, which makes a subobject public,
# even a parent is protected.
#
# Revision 1.9  1996/07/23 19:59:29  jfulton
# Fixed bugs:
#
#   - object[entryname] can fail with attribute as well as type error
#   - flatten didn't work with multiple values\
#   - inserted base was not absolute
#
# Added transaction support.
#
# Revision 1.8  1996/07/18 14:59:54  jfulton
# Fixed bug in getting web_objects.
#
# Revision 1.7  1996/07/11 19:39:07  jfulton
# Fixed bug in new feature: 'AUTHENTICATED_USER'
#
# Revision 1.6  1996/07/10 22:53:54  jfulton
# Fixed bug in use of default realm.
#
# If authentication is performed, then the name of the authenticated
# user is saved in the request with the name 'AUTHENTICATED_USER', and
# will be passed to called objects through the argument name
# 'AUTHENTICATED_USER'.
#
# Revision 1.5  1996/07/08 20:34:11  jfulton
# Many changes, including:
#
#   - Better realm management
#   - Automatic type conversion
#   - Improved documentation
#   - ...
#
# Revision 1.4  1996/07/04 22:57:20  jfulton
# Added lots of documentation.  A few documented features have yet to be
# implemented.  The module needs to be retested after adding some new
# features.
#
#
# 
