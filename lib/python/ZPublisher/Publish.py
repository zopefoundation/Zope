#!/usr/local/bin/python 
# $What$

__doc__="""\
Publish python objects on web servers using CGI

Introduction

  The python object publisher provides a simple mechanism for publishing a
  collection of python objects as World-Wide-Web (Web) resources without any
  plumbing (e.g. CGI) specific code.

Published objects

  Objects are published by including them in a published module.
  When a module is published, any objects that:

    - can be found in the module's global name space,

    - That do not have names starting with an underscore, 

    - that have non-empty doc strings, and 

    - that are not modules

  are published  Alternatively, a module variable, named
  'web_objects' can be defined.  If this variable is defined, it should
  be bound to a mapping object that maps published names to published
  objects.

  Sub-objects (or sub-sub objects, ...) of published objects are
  also published, as long as the sub-objects:
   
    - have non-empty doc strings,

    - have names that do not begin with an underscore, and

    - are not modules.

  Note that object methods are considered to be subobjects.

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
  used is "module_name.server_name", where "module_name" is the
  name of the module containing the published objects, and
  server_name is the name of the web server.      

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
    called function must be prepared to convert string arguments to
    other data types, such as numbers.
    
    If file upload is used, however, then file objects will be
    passed instead.

Published objects that are not functions, methods, or classes

  If a published object that is not a function, method, or class
  is accessed, then the object itself will be returned.

Return types

  A published object, or the returned value of a called published
  object can be of any python type.  The returned value will be
  converted to a string and examined to see if it appears to be an
  HTML document.  If it appears to be an HTML document, then the
  response content-type will be set to text/html.  Otherwise the
  content-type will be set to text/plain.

  A special case is when the returned object is a two-element tuple.
  If the return value is a two-element tuple, then the first element
  will be converted to a string and treated as an HTML title, and
  the second element will be converted to a string and treated as
  the contents of an HTML body. An HTML document is created and
  returned (with type text/html) by adding necessary html, head,
  title, and body tags.
      
Exception handling

  Unhandled exceptions are caught by the object publisher
  and are translated automatically to nicely formatted HTTP output.
  Traceback information will be included in a comment in the output.

Redirection

  Automatic redirection may be performed by a published object
  by raising an exception with a type and value of "Redirect" and
  a string containing an absolute URI.

Examples

  Consider the following examples:
  
	_called=0
	def called():
	    "Report how many times I've been called"
	    global _called
	    _called=_called+1
	    return _called
	
	def hi():
	    "say hello"
	    return '<html><head><base href=spam></head>hi'
	
	def add(x,y):
	    "add two numbers"
	    from string import atof
	    return atof(x)+atof(y)
	
	# Note that doc is not published
	def doc(m):
	  d={}
	  exec 'import ' + m in d
	  return d[m].__doc__
	
	class spam:
	    "spam is good"
	
	    __allow_groups__=[{'jim':1, 'super':1}]
	
	    def hi(self):
	      return self.__doc__
	
	    __super_group=[{'super':1}]

	    # Note that eat requires "super" access.
	    eat__allow_groups__=__super_group
	    def eat(self,module_name):
		"document a module"
		if not module_name:
		    raise 'BadRequest', 'The module name is blank'
		return doc(module_name)

	    # Here we have a stream output example.
	    # Note that only jim and super can use this.
    	    def list(self, RESPONSE):
		"list some elements"
		RESPONSE.setCookie('spam','eggs',path='/')
		RESPONSE.write('<html><head><title>A list</title></head>')
		RESPONSE.write('list: \\n')
		for i in range(10): RESPONSE.write('\\telement %d' % i)
		RESPONSE.write('\\n')
	
	
	aSpam=spam()
	
	# We create another spam that paul can use,
	# but he still can't eat.
	moreSpam=spam()
	moreSpam.__dict__['__allow_groups__']=[{'paul':1}]
	
	
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
      (compiled in) python search path.

    o Copy the file cgi-module-publisher to the directory containing the
      module to be published.

    o Create a symbolic link from cgi-module-publisher (in the directory
      containing the module to be published) to the module name in the
      cgi-bin directory.

Publishing a module using Fast CGI

    o Copy the files: cgi_module_publisher.pyc and CGIResponse.pyc,
      Realm.pyc, and newcgi.pyc, to the directory containing the
      module to be published, or to a directory in the standard
      (compiled in) python search path.

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
      (compiled in) python search path.

    o Copy the file ilu-module-publisher to the directory containing the
      module to be published.

    o Create a symbolic link from ilu-module-publisher (in the directory
      containing the module to be published) to the module name
      (perhaps in a different directory). 
	
    o Start the module server process by running the symbolically
      linked file, giving the server name as an argument.

    o Configure the web server to call module_name@server with
      the requestor.

$Id: Publish.py,v 1.4 1996/07/04 22:57:20 jfulton Exp $"""
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
# Revision 1.4  1996/07/04 22:57:20  jfulton
# Added lots of documentation.  A few documented features have yet to be
# implemented.  The module needs to be retested after adding some new
# features.
#
#
# 
__version__='$Revision: 1.4 $'[11:-2]


def main():
    # The "main" program for this module
    pass


if __name__ == "__main__": main()

import sys, os, string, types, newcgi, regex
from CGIResponse import Response
from Realm import Realm

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

    
    def document(self,o,response):
	if type(o) is not types.StringType: o=o.__doc__
	response.setBody(
	    self.html('Documentation for' +
		      ((self.env('PATH_INFO') or
			('/'+self.module_name))[1:]),
		      '<pre>\n%s\n</pre>' % o)
	    )
	return response

    def validate(self,object,parent=None,object_name='_'):
	if type(object) is types.ModuleType: self.forbiddenError()
	if (hasattr(object,'__allow_groups__') or
	    parent and hasattr(parent,object_name+'__allow_groups__')
	    ):
  	    if hasattr(object,'__allow_groups__'):
		groups=object.__allow_groups__
	    else:
		groups=getattr(parent,object_name+'__allow_groups__')
	    try: realm=self.realm
	    except:
		try:
		    realm=self.module.__realm__
		    if not hasattr(realm,'validate'):
			# Hm.  The realm must really be just a mapping
			# object, so we will convert it to a proper
			# realm using basic authentication
			import Realm
			realm=Realm("%s.%s" %
				    (self.module_name,self.request.SERVER_NAME),
				    realm)
			self.module.__realm__=realm
		except:
		    import Realm
		    realm=Realm("%s.%s" %
				(self.module_name,self.request.SERVER_NAME))
		self.realm=realm
	    try:
		return realm.validate(self.env("HTTP_AUTHORIZATION"),groups)
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
	    theModule, dict, published = module_dicts[module_name]
	except:
	    exec 'import %s' % module_name in dict
	    theModule=dict=dict[module_name]
	    if hasattr(dict,published):
		dict=getattr(dict,published)
	    else:
		dict=dict.__dict__
		published=None
	    module_dicts[module_name] = theModule, dict, published
	self.module=theModule

	# Get a nice clean path list:
	path=(string.strip(self.env('PATH_INFO')) or '/')[1:]
	path=string.splitfields(path,'/')
	while path and not path[0]: path = path[1:]
    
	# Make help the default, if nothing is specified:
	if not path: path = ['help']

	# Try to look up the first one:
	try: function, p, path = dict[path[0]], path[0], path[1:]
	except KeyError: self.notFoundError()

	# Do top-level object first-step authentication
	if not (published or function.__doc__): self.forbiddenError()
	self.validate(function)
    
	p=''
	while path:
	    p,path=path[0], path[1:]
	    if p:
		try: f=getattr(function,p)
		except AttributeError:
		    try: f=function[p]
		    except TypeError:
			if not path and p=='help':
			    p, f = '__doc__', self.document(function,response)
			else:
			    self.notFoundError()
		if not (p=='__doc__' or f.__doc__) or p[0]=='_':
		    raise 'Forbidden',function
		self.validate(f,function,p)
		function=f
    
	if type(f) is types.ClassType:
	    if hasattr(f,'__init__'):
		f=f.__init__
	    else:
		def ff(): pass
		f=ff
	if type(f) is types.MethodType:
	    defaults=f.im_func.func_defaults
	    names=(f.im_func.
		   func_code.co_varnames[1:f.im_func.func_code.co_argcount])
	elif type(f) is types.FunctionType:
	    defaults=f.func_defaults
	    names=f.func_code.co_varnames[:f.func_code.co_argcount]
	else:
	    return response.setBody(function)
    
	query=self.request
	query['RESPONSE']=response

	args=[]
	nrequired=len(names) - (len(defaults or []))
	for name_index in range(len(names)):
	    name=names[name_index]
	    try:
		v=query[name]
		args.append(v)
	    except:
		if name_index < nrequired:
		    self.badRequestError(name)

    
	if args: result=apply(function,tuple(args))
	else:    result=function()

	if result and result is not response: response.setBody(result)

	return response

def str_field(v):
    if type(v) is types.InstanceType and v.__class__ is newcgi.MiniFieldStorage:
        v=v.value
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
        the <a href="http://hoohoo.ncsa.uiuc.edu/cgi/interface.html">CGI specification</a>

      - Form data

        These are data extracted either a URL-encoded query string or
        body, if present.

      - Cookies

        These are the cookie data, if present.

      - Other

        Data that may be set by an application object.

    The request object has three attributes: "environ", "form",
    "cookies", and "other" that are dictionaries containing this data.

    The request object may be used as a mapping object, in which case
    values will be looked up in the order: environment variables,
    other variables, form data, and then cookies.  Dot notation may be
    used in addition to indexing notation for variables with names
    other than "environ", "form", "cookies", and "other".
    """

    def __init__(self,environ,form):
	self.environ=environ
	self.form=form
	self.other={}

    def __setitem__(self,key,value):
	"""Set application variables

	This method is used to set a variable in the requests "other"
	category.
	"""
	
	self.other[key]=value

    def __getitem__(self,key):
	"""Get a variable value

	Return a value for the required variable name.
	The value will be looked up from one of the request data
	categories. The search order is environment variables,
	other variables, form data, and then cookies. 
	
	"""
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
		v=self.form[key]
		if type(v) is types.ListType:
		    v=map(str_field, v)
		    if len(v) == 1: v=v[0]
		else: v=str_field(v)
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
        self.request=Request(environ,form)
	self.response=Response(stdout=stdout, stderr=stderr)
	self.stdin=stdin
	self.stdout=stdout
	self.stderr=stderr
	b=string.strip(self.environ['SCRIPT_NAME'])
	if b[-1]=='/': b=b[:-1]
	p = string.rfind(b,'/')
	if p >= 0: self.base=b[:p+1]
	else: self.base=''

def publish_module(module_name,
		   stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr,
		   environ=os.environ):
    try:
	publisher=CGIModulePublisher(stdin=stdout, stdin=stdout, stderr=stderr,
				     environ=environ)
	response = publisher.publish(module_name)
    except:
	response.exception()
    if response: response=str(response)
    if response: stdout.write(response)


