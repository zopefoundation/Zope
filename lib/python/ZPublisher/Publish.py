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
  attribute '__realm__', the object publisher will first try to
  evaluate 'foo.bar.spam.__realm__', and then try to evaluate:
  'foo.bar["spam"+"__realm__"]'. 

Access Control

  Access to an object (and it's sub-objects) may be further
  restricted by specifying an object attribute named:
  '__allow_groups__'.  If set, then this attribute should
  contain a dictionary or sequence.  Each of the
  items in the attribute must be dictionaries that use names
  as keys (i.e. sets of names).  The values in these dictionaries
  may contain passwords for authenticating each of the names.
  Alternatively, passwords may be provided in separate "realm"
  objects.  If no realm is provided, then basic authentication
  will be used and the object publisher will attempt to
  authenticate the access to the object using one of the supplied
  name and password pairs.  The basic authentication realm name
  used is 'module_name.server_name', where 'module_name' is the
  name of the module containing the published objects, and
  server_name is the name of the web server.      

  The module used to publish an object may contain it's own
  '__allow_groups__' attribute, thereby limiting access to all of the
  objects in a module.

  If multiple objects in the URI path have '__allow_groups__'
  attributes, then the effect will be that of intersecting all of the
  groups.

  Realms

      Realms provide a mechanism for separating authentication and
	authorization.  

	An object may have an attribute '__realm__', which should be
	either a realm object, or a mapping object mapping names to
	passwords.

	If a mapping object is provided, then it will be used for
	basic authentication using a realm name of
	"module_name.server_name", where "module_name" is the name of
	the module containing the published objects, and server_name
	is the name of the web server.
	
	If a realm object is used, then it will use an application
	supplied realm name and password mapping object, and may use
	other than basic authentication.  If a realm is provided that
	does not include it's own name to password mapping, then the
	name to password mappings contained in an object's
	'__allow_groups__' attribute will be used.

	An object may "inherit" a realm from one of it's parent
	objects in the URI path to the object, including the module
	used to publish the object.

  Fixed-attribute objects

      For some interesting objects, such as functions, and methods,
      it may not be possible for applications to set
      '__allow_groups__' or '__realm__' attributes.  In these cases, the
      object's parent object may contain attributes
      'object_name__allow_groups__' or 'object_name__realm__', which
      will be used as surrogates for the object's '__allow_groups__'
      and '__realm__' attributes.

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
    
    If file upload is used, however, then file objects will be
    passed instead.

    If field names in form data are of the form: name:type, then an
    attempt will be to convert data from from strings to the indicated
    type.  The data types currently supported are: float, int, and
    long.  For example, if the name of a field in an input form is
    age:int, then the field value will be passed in argument, age, and
    an attempt will be made to convert the argument value to an
    integer. 

Published objects that are not functions, methods, or classes

  If a published object that is not a function, method, or class
  is accessed, then the object itself will be returned.

Return types

  A published object, or the returned value of a called published
  object can be of any Python type.  The returned value will be
  converted to a string and examined to see if it appears to be an
  HTML document.  If it appears to be an HTML document, then the
  response content-type will be set to 'text/html'.  Otherwise the
  content-type will be set to 'text/plain'.

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


	# Here's out "password" database.
	from Realm import Realm
	__realm__=Realm('spam.digicool.com',
			{'jim':'spam', 'paul':'eggs'})

Publishing a module using CGI

    o Do not copy the module to be published to the cgi-bin
      directory.

    o Copy the files: cgi_module_publisher.pyc and CGIResponse.pyc,
      Realm.pyc, and newcgi.pyc, to the directory containing the
      module to be published, or to a directory in the standard
      (compiled in) Python search path.

    o Copy the file cgi-module-publisher to the directory containing the
      module to be published.

    o Create a symbolic link from cgi-module-publisher (in the directory
      containing the module to be published) to the module name in the
      cgi-bin directory.

Publishing a module using Fast CGI

    o Copy the files: cgi_module_publisher.pyc and CGIResponse.pyc,
      Realm.pyc, and newcgi.pyc, to the directory containing the
      module to be published, or to a directory in the standard
      (compiled in) Python search path.

    o Copy the file fcgi-module-publisher to the directory containing the
      module to be published.

    o Create a symbolic link from fcgi-module-publisher (in the directory
      containing the module to be published) to the module name in some
      directory accessable to the Fast CGI-enabeled web server.
	
    o Configure the Fast CGI-enabled web server to execute this
      file.

Publishing a module using the ILU Requestor (future)

    o Copy the files: cgi_module_publisher.pyc and CGIResponse.pyc,
      Realm.pyc, and newcgi.pyc, to the directory containing the
      module to be published, or to a directory in the standard
      (compiled in) Python search path.

    o Copy the file ilu-module-publisher to the directory containing the
      module to be published.

    o Create a symbolic link from ilu-module-publisher (in the directory
      containing the module to be published) to the module name
      (perhaps in a different directory). 
	
    o Start the module server process by running the symbolically
      linked file, giving the server name as an argument.

    o Configure the web server to call module_name@server_name with
      the requestor.

$Id: Publish.py,v 1.9 1996/07/23 19:59:29 jfulton Exp $"""
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
# $Log: Publish.py,v $
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
#   - Butter realm management
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
__version__='$Revision: 1.9 $'[11:-2]


def main():
    # The "main" program for this module
    pass


if __name__ == "__main__": main()

import sys, os, string, types, newcgi, regex
from CGIResponse import Response
from Realm import Realm

from newcgi import FieldStorage


class ModulePublisher:

    def html(self,title,body):
	return ("<html>\n"
		"<head>\n<title>%s</title>\n</head>\n"
		"<body>\n%s\n</body>\n"
		"</html>\n" % (title,body))

    def notFoundError(self):
	raise 'NotFound',self.html(
	    "Resource not found",
	    "Sorry, the requested document does not exist.")

    forbiddenError=notFoundError  # If a resource is forbidden,
                                  # why reveal that it exists?

    def badRequestError(self,name):
	if regex.match('^[A-Z_0-9]+$',name) >= 0:
	    raise 'InternalError', self.html(
		"Internal Error",
		"Sorry, an internal error occurred in this resource.")

	raise 'BadRequest',self.html(
	    "Invalid request",
	    "The parameter, %s, was ommitted from the request." % name)

    def forbiddenError(self):
	raise 'NotFound',self.html(
	    "Resource not found",
	    "Sorry, the requested document does not exist.")
    
    def env(self,key):
	try: return self.environ[key]
	except: return ''


    def validate(self,groups,realm=None):
	if not realm:
	    try: realm=self.realm
	    except:
		realm=Realm("%s.%s" %
				(self.module_name,self.request.SERVER_NAME))
		self.realm=realm
	    
	try:
	    user=realm.validate(self.env("HTTP_AUTHORIZATION"),groups)
	    self.request['AUTHENTICATED_USER']=user
	    return user
	except:
	    try:
		t,v,tb=sys.exc_type, sys.exc_value,sys.exc_traceback
		auth,v=v
	    except: pass
	    if t == 'Unauthorized':
		self.response['WWW-authenticate']=auth
		raise 'Unauthorized', v
	self.forbiddenError()

    def publish(self, module_name, published='web_objects',
		imported_modules={}, module_dicts={}):

	if module_name[-4:]=='.cgi': module_name=module_name[:-4]
	self.module_name=module_name
	response=self.response
	response.setBase(self.base)

	dict=imported_modules
	try:
	    theModule, object, published = module_dicts[module_name]
	except:
	    exec 'import %s' % module_name in dict
	    theModule=object=dict[module_name]
	    if hasattr(theModule,published):
		object=getattr(theModule,published)
	    else:
		object=theModule
		published=None
	    module_dicts[module_name] = theModule, object, published

	self.module=theModule

	# Try to get realm from module
	try: realm=theModule.__realm__
	except: realm=None

	# Do authorization check, if need be:
	try:
	    groups=theModule.__allow_groups__
	    if groups: self.validate(groups,realm)	
	except: groups=None

	# Get a nice clean path list:
	path=(string.strip(self.env('PATH_INFO')) or '/')[1:]
	path=string.splitfields(path,'/')
	while path and not path[0]: path = path[1:]
 
	# Get default doc:
	try: doc=object.__doc__
	except:
	    try: doc=object['__doc__']
	    except: doc=None

	# Get default object if no path was specified:
	if not path:
	    for entry_name in 'index_html', 'index.html':
		try:
		    if hasattr(object,entry_name):
			path=[entry_name]
			break
		except: pass
		try:
		    if object.has_key(entry_name):
			path=[entry_name]
			break
		except: pass
	    if not path: path = ['help']
    
	while path:
	    entry_name,path,groups=path[0], path[1:], None
	    if entry_name:
		try:
		    subobject=getattr(object,entry_name)
		    try: groups=subobject.__allow_groups__
		    except:
			try: groups=getattr(object,
					    entry_name+'__allow_groups__')
			except: pass
		    try: doc=subobject.__doc__
		    except:
			try: doc=getattr(object,entry_name+'__doc__')
			except: doc=None
		    try: realm=subobject.__realm__
		    except:
			try: realm=getattr(object,entry_name+'__realm__')
			except: pass
		except AttributeError:
		    try:
			subobject=object[entry_name]
			try: groups=subobject.__allow_groups__
			except:
			    try: groups=object[entry_name+'__allow_groups__']
			    except: pass
			try: doc=subobject.__doc__
			except:
			    try: doc=object[entry_name+'__doc__']
			    except: doc=None
			try: realm=subobject.__realm__
			except:
			    try: realm=object[entry_name+'__realm__']
			    except: pass
		    except (TypeError,AttributeError):
			if not path and entry_name=='help' and doc:
			    object=doc
			    entry_name, subobject = (
				'__doc__', self.html
				('Documentation for ' +
				 ((self.env('PATH_INFO') or
				   ('/'+self.module_name))[1:]),
				 '<pre>\n%s\n</pre>' % doc)
				)
			else:
			    self.notFoundError()
		if published:
		    # Bypass simple checks the first time
		    published=None
		else:
		    # Perform simple checks
		    if (type(subobject)==types.ModuleType or
			entry_name != '__doc__' and
			(not doc or entry_name[0]=='_')
			):
			raise 'Forbidden',object

		# Do authorization checks
		if groups: self.validate(groups, realm)

		# Promote subobject to object
		object=subobject

	object_as_function=object	
	if type(object_as_function) is types.ClassType:
	    if hasattr(object_as_function,'__init__'):
		object_as_function=object_as_function.__init__
	    else:
		def function_with_empty_signature(): pass
		object_as_function=function_with_empty_signature
		
	if type(object_as_function) is types.MethodType:
	    defaults=object_as_function.im_func.func_defaults
	    argument_names=(
		object_as_function.im_func.
		func_code.co_varnames[
		    1:object_as_function.im_func.func_code.co_argcount])
	elif type(object_as_function) is types.FunctionType:
	    defaults=object_as_function.func_defaults
	    argument_names=object_as_function.func_code.co_varnames[
		:object_as_function.func_code.co_argcount]
	else:
	    return response.setBody(object)
    
	query=self.request
	query['RESPONSE']=response

	args=[]
	nrequired=len(argument_names) - (len(defaults or []))
	for name_index in range(len(argument_names)):
	    argument_name=argument_names[name_index]
	    try:
		v=query[argument_name]
		args.append(v)
	    except:
		if name_index < nrequired:
		    self.badRequestError(argument_name)


	# Attempt to start a transaction:
	try:
	    transaction=get_transaction()
	    transaction.begin()
	except: transaction=None

	if args: result=apply(object,tuple(args))
	else:    result=object()

	if transaction: transaction.commit()

	if result and result is not response: response.setBody(result)

	return response

def str_field(v):
    if type(v) is types.ListType:
	return map(str_field,v)

    if type(v) is types.InstanceType and v.__class__ is newcgi.MiniFieldStorage:
        v=v.value
    elif type(v) is not types.StringType:
	try:
	    if v.file:
		v=v.file
	    else:
		v=v.value
	except: pass
    return v

def flatten_field(v,converter=None):
    if type(v) is types.ListType:
	if len(v) > 1: return map(flatten_field,v)
	v=v[0]

    try:
	if v.file:
	    v=v.file
	else:
	    v=v.value
    except: pass
    
    if converter: v=converter(v)
    return v

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

    The request object has three attributes: "environ", "form",
    "cookies", and "other" that are dictionaries containing this data.

    The form attribute of a request is actually a Field Storage
    object.  When file uploads are used, this provides a richer and
    more complex interface than is provided by accessing form data as
    items of the request.  See the FieldStorage class documentation
    for more details.

    The request object may be used as a mapping object, in which case
    values will be looked up in the order: environment variables,
    other variables, form data, and then cookies.  Dot notation may be
    used in addition to indexing notation for variables with names
    other than "environ", "form", "cookies", and "other".
    """

    def __init__(self,environ,form,stdin):
	self.environ=environ
	self.form=form
	self.stdin=stdin
	self.other={}

    def __setitem__(self,key,value):
	"""Set application variables

	This method is used to set a variable in the requests "other"
	category.
	"""
	
	self.other[key]=value


    __type_converters = {'float':string.atof, 'int': string.atoi, 'long':string.atol}

    __http_colon=regex.compile("\(:\|\(%3[aA]\)\)")

    def __getitem__(self,key):
	"""Get a variable value

	Return a value for the required variable name.
	The value will be looked up from one of the request data
	categories. The search order is environment variables,
	other variables, form data, and then cookies. 
	
	""" #"
	try:
	    v= self.environ[key]
	    if self.special_names.has_key(key) or key[:5] == 'HTTP_':
		return v
	except: pass

	try: return self.other[key]
	except: pass

	if key=='REQUEST': return self

	if key!='cookies':
	    try:
		converter=None
		try:
		    v=self.form[key]
		except:
		    # Hm, maybe someone used a form with a name like: name:type
		    try: tf=self.__dict__['___typed_form']
		    except:
			tf=self.__dict__['___typed_form']={}
			form=self.form
			colon=self.__http_colon
			search=colon.search
			group=colon.group
			for k in form.keys():
			    l = search(k)
			    if l > 0: 
				tf[k[:l]]=form[k],k[l+len(group(1)):]

		    v,t=tf[key]
		    try:
			converter=self.__type_converters[t]
		    except: pass
		v=flatten_field(v,converter)
		return v
	    except: pass

	if not self.__dict__.has_key('cookies'):
	    cookies=self.cookies={}
	    if self.environ.has_key('HTTP_COOKIE'):
		for cookie in string.split(self.environ['HTTP_COOKIE'],';'):
		    try:
			[k,v]=map(string.strip,string.split(cookie,'='))
			cookies[k]=v
		    except: pass
	
	if key=='cookies': return self.cookies

	try: return self.cookies[key]
	except: raise AttributeError, key

    __getattr__=__getitem__

    special_names = {
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
	}
		

class CGIModulePublisher(ModulePublisher):

    def __init__(self,
		 stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr,
		 environ=os.environ):
	self.environ=environ
	fp=None
	try:
	    if environ['REQUEST_METHOD'] != 'GET': fp=stdin
	except: pass
	
	form=newcgi.FieldStorage(fp=fp,environ=environ,keep_blank_values=1)
        self.request=Request(environ,form,stdin)
	self.response=Response(stdout=stdout, stderr=stderr)
	self.stdin=stdin
	self.stdout=stdout
	self.stderr=stderr
	b=string.strip(self.environ['SCRIPT_NAME'])
	while b and b[-1]=='/': b=b[:-1]
	p = string.rfind(b,'/')
	if p >= 0: b=b[:p+1]
	else: b=''
	while b and b[0]=='/': b=b[1:]
	try:    server_url=          string.strip(self.environ['SERVER_URL' ])
	except: server_url='http://'+string.strip(self.environ['SERVER_NAME'])
	self.base="%s/%s" % (server_url,b)
	

def publish_module(module_name,
		   stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr,
		   environ=os.environ):
    try:
	publisher = CGIModulePublisher(stdin=stdin, stdout=stdout,
				       stderr=stderr,
				       environ=environ)
	response = publisher.response
	response = publisher.publish(module_name)
    except:
	response.exception()
    if response: response=str(response)
    if response: stdout.write(response)


