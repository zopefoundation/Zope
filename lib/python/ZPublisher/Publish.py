#! /usr/local/bin/python

import sys, os, string, types, newcgi, CGIResponse, regex

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

    def validate(self,object,module,response):
	if hasattr(object,'__allow_groups__'):
	    groups=object.__allow_groups__
	    try: realm=module.__realm__
	    except: self.forbiddenError()
	    try:
		user=realm.user(self.env("HTTP_AUTHORIZATION"))
		if type(groups) is type({}):
		    groups=map(lambda k,d=groups: d[k], groups.keys())
		for g in groups:
		    if g.has_key(user): return None
		realm.deny()
	    except:
		try:
		    t,v,tb=sys.exc_type, sys.exc_value,sys.exc_traceback
		    auth,v=v
		except: pass
		if t == 'Unauthorized':
		    response['WWW-authenticate']=auth
		    raise 'Unauthorized', v
	    self.forbiddenError()

    def publish(self, module_name, response, published='web_objects',
		imported_modules={}, module_dicts={}):

	if module_name[-4:]=='.cgi': module_name=module_name[:-4]
	self.module_name=module_name
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
    
	path=(string.strip(self.env('PATH_INFO')) or '/')[1:]
	path=string.splitfields(path,'/')
	while path and not path[0]: path = path[1:]
    
	if not path: path = ['help']
	try: function,path=dict[path[0]], path[1:]
	except KeyError: self.notFoundError()

	if not (published or function.__doc__): self.forbiddenError()
	self.validate(function,theModule,response)
    
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
		function=f
		if not (p=='__doc__' or function.__doc__):
		    raise 'Forbidden',function
		self.validate(function,theModule,response)
    
	f=function
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
    
	query=self.get_data()
	query['RESPONSE']=response

	last_name=len(names) - (len(defaults or []))
	for name in names[:last_name]:
	    if not query.has_key(name):
		self.badRequestError(name)

	args={}
	for name in names:
	    if query.has_key(name):
		q=query[name]
		if type(q) is type([]) and len(q) == 1: q=q[0]
		args[name]=q
    
	if args: result=apply(function,(),args)
	else:    result=function()

	if result and result is not response: response.setBody(result)

	return response




class CGIModulePublisher(ModulePublisher):

    def __init__(self,
		 stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr,
		 environ=os.environ):
	self.environ=environ
	self.stdin=stdin
	self.stdout=stdout
	self.stderr=stderr
	b=string.strip(self.environ['SCRIPT_NAME'])
	if b[-1]=='/': b=b[:-1]
	p = string.rfind(b,'/')
	if p >= 0: self.base=b[:p+1]
	else: self.base=''

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

    def get_data(self):
	query=newcgi.parse(fp=self.stdin, environ=self.environ) or {}
	environ=self.environ
	for key in environ.keys():
	    if self.special_names.has_key(key) or key[:5] == 'HTTP_':
		query[key]=[environ[key]]

	for cookie in string.split(self.env('HTTP_COOKIE'),';'):
	    try:
		[key,value]=map(string.strip, string.split(cookie,'='))
		if key and not query.has_key(key): query[key]=value
	    except: pass

	return query
    
def publish_module(module_name, published='web_objects',
		   stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr,
		   environ=os.environ):
    response=CGIResponse.Response(stdout=stdout, stderr=stderr)
    try:
	publisher=CGIModulePublisher(stdin=stdout, stdin=stdout, stderr=stderr,
				     environ=environ)
	response = publisher.publish(module_name, response, published)
    except:
	response.exception()
    if response: response=str(response)
    if response: stdout.write(response)


