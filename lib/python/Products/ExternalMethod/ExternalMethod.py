
"""External Method Product

This product provides support for external methods, which allow
domain-specific customization of web environments.
"""

from Acquisition import Implicit
from Globals import Persistent, HTMLFile, MessageDialog
import OFS.SimpleItem
from string import split, join
import AccessControl.Role
	    
braindir=SOFTWARE_HOME+'/Extensions'    
modules={}

addForm=HTMLFile('ExternalMethod/methodAdd')

def add(self, id, title, external_name, acl_type='A',acl_roles=[], REQUEST=None):
    """Add an external method to a folder"""
    names=split(external_name,'.')
    module, function = join(names[:-1],'.'), names[-1]
    i=ExternalMethod(id,title,module,function)
    i._setRoles(acl_type,acl_roles)
    self._setObject(id,i)
    return self.manage_main(self,REQUEST)

class ExternalMethod(OFS.SimpleItem.Item, Persistent, AccessControl.Role.RoleManager):
    """An external method is a web-callable function that encapsulates
    an external function."""

    meta_type='External Method'
    icon='misc_/ExternalMethod/function_icon'
    func_defaults=()
    func_code=None

    def __init__(self, id='', title='', module='', function=''):
	if id:
	    self.id=id
	    self.title=title
	    self._module=module
	    self._function=function
	    self.getFunction()
        self._p_atime=1

    manage=HTMLFile('ExternalMethod/methodEdit')
    def manage_edit(self, title, external_name, acl_type='A', acl_roles=[],
		    REQUEST=None):
	"Change the external method"
	self.title=title
	names=split(external_name,'.')
	module, function = join(names[:-1],'.'), names[-1]
	self._module=module
	self._function=function
	self.getFunction()
	self._setRoles(acl_type,acl_roles)
	if REQUEST: return MessageDialog(
	    title  ='Changed %s' % self.id,
	    message='%s has been updated' % self.id,
	    action =REQUEST['URL2']+'/manage_main',
	    target ='manage_main')

    def external_name(self): return "%s.%s" % (self._module, self._function)

    def getFunction(self):

	module=self._module
	
	try: m=modules[module]
	except:
	    d,n = os.path.split(module)
	    if d: raise ValueError, (
	    'The file name, %s, should be a simple file name' % module)
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

    def __init__(self, f=None):
	if f is not None:
	    self.co_varnames=f.func_code.co_varnames
	    self.co_argcount=f.func_code.co_argcount

    def __cmp__(self,other):
	return cmp((self.co_argcount, self.co_varnames),
		   (othr.co_argcount, othr.co_varnames))
