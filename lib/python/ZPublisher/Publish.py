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
	if type(object) is types.ModuleType: self.forbiddenError()
	if hasattr(object,'__allow_groups__'):
	    groups=object.__allow_groups__
	    try: realm=module.__realm__
	    except: self.forbiddenError()
	    try:
		user=realm.user(self.env("HTTP_AUTHORIZATION"))
		if type(groups) is types.DictType:
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
		if not (p=='__doc__' or function.__doc__) or p[0]=='_':
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

    def __init__(self,environ,form):
	self.environ=environ
	self.form=form
	self.other={}

    def __setitem__(self,key,value): self.other[key]=value

    def __getitem__(self,key):
	try:
	    v= self.environ[key]
	    if self.special_names.has_key(key) or key[:5] == 'HTTP_':
		return v
	except: pass

	try: return self.other[key]
	except: pass

	if key=='REQUEST': return self

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
	self.stdin=stdin
	self.stdout=stdout
	self.stderr=stderr
	b=string.strip(self.environ['SCRIPT_NAME'])
	if b[-1]=='/': b=b[:-1]
	p = string.rfind(b,'/')
	if p >= 0: self.base=b[:p+1]
	else: self.base=''

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


