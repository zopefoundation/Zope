#! /usr/local/bin/python

import sys, os, string, types, cgi

from CGIResponse import Response, ExceptionResponse

class output_file:
    '''Generic output abstraction output for CGI resource output.

    This may be a thin layer around stdout, or it may be something
    very different.'''

    called=None
    
    def write(self,s):
        self.called=1
        self.write=sys.stdout.write
        if string.lower(string.strip(s)[:6]) == '<html>':
            print 'content-type: text/html\n'
        elif string.lower(s)[:13]!='content-type:':
            print 'content-type: text/plain\n'
        self.write(s)
       

def _publish_module(module_name, published='web_objects'):

    dict={}
    exec 'import %s' % module_name in dict
    theModule=dict=dict[module_name]
    if hasattr(dict,published):
	dict=getattr(dict,published)
    else:
	dict=dict.__dict__
	published=None

    def env(key,d=os.environ):
	try: return d[key]
	except: return ''

    query=cgi.parse() or {}
    
    path=(string.strip(env('PATH_INFO')) or '/')[1:]
    path=string.splitfields(path,'/')
    while path and not path[0]: path = path[1:]

    if not path and dict['__doc__']: function=theModule
    else:
	if not path: path = ['main']
	function,path=dict[path[0]], path[1:]   

    if not (published or function.__doc__):
	raise 'Forbidden',function

    p=''
    while path:
	p,path=path[0], path[1:]
	if p:
  	    try: f=getattr(function,p)
	    except:
	        f=function[p]
	    function=f
	    if not (p=='__doc__' or function.__doc__):
		raise 'Forbidden',function

    def document(o,env=env):
	if type(o) is not types.StringType: o=o.__doc__
    	return Response(('Documentation for' +
			 ((env('PATH_INFO') or '/main')[1:]),
			 '<pre>\n%s\n</pre>' % o))
	
    if(p=='__doc__' or env('METHOD_NAME') == 'HEAD'):
	return document(function)

    f=function
    if type(f) is types.ClassType:
	if hasattr(f,'__init__'):
	    f=f.__init__.im_func
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
	return document(function)

    environ=os.environ
    for key in environ.keys():
        query[key]=[environ[key]]
    out=output_file()        
    query['OUTPUT_FILE']=[out]
    last_name=len(names) - (len(defaults or []))
    for name in names[:last_name]:
	if not query.has_key(name): raise 'BadRequest', query
    args={}
    for name in names:
	if query.has_key(name):
	    q=query[name]
	    if len(q) == 1: q=q[0]
	    args[name]=q

    if args: result=apply(function,(),args)
    else:    result=function()
    if out.called:  # The function wrote output
    	if result: result=str(result)
    	else: result=''
	return result
    
    if type(result) is types.InstanceType and result.__class__ is Response:
	return result

    return Response(result)

def publish_module(module_name, published='web_objects'):
    try:
	response =  _publish_module(module_name, published)
	if response: print response
    except:
	print ExceptionResponse()


