
"""External Method Product

This product provides support for external methods, which allow
domain-specific customization of web environments.
"""

from Acquisition import Implicit
	    
brain_dir=SOFTWARE_HOME+'/Extensions'    
modules={}

def add(self, id, title, roles, external_name, REQUEST=None):
    """Add an external method to a folder"""
    names=split(external_name,'.')
    module, function = join(names[:-1],'.'), names[-1]
    i=ExternalMethod(id,title,roles,module,function)
    self._setObject(name,i)
    return self.manage_main(self,REQUEST)

class ExternalMethod:
    """An external method is a web-callable function that encapsulates
    an external function."""

    meta_type='External Method'

    def __init__(self, id='', title='', roles='', module='', function=''):
	if id:
	    self.id=id
	    self.title=title
	    self.roles=roles
	    self._module=module
	    self._function=function
	    self.getFunction()
        self._p_atime=1

    def getFunction(self):

	module=self._module
	
	try: m=modules[module]
	except:
	    m={}
	    exec open("%s/%s.py" % (braindir, module)) in m
	    modules[module]=m

	f=m[self._function]
	if self.func_defaults != f.func_defaults:
	   self.func_defaults  = f.func_defaults
	    
	func_code=FuncCode(f)
	if func_code != self.func_code: self.func_code=func_code
    
	self._v_f=f

	return f

    def __call__(self, *args):
	try: f=self._v_f
	except: f=self.getFunction()

	return apply(f,args)

    
class FuncCode:

    def __init__(self, f):
	self.co_varnames=f.func_code.co_varnames
	self.co_argcount=f.func_code.co_argcount

    def __cmp__(self,other):
	return cmp((self.co_argcount, self.co_varnames),
		   (othr.co_argcount, othr.co_varnames))
