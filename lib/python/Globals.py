
"""Global definitions"""

__version__='$Revision: 1.24 $'[11:-2]

import sys, os
from DateTime import DateTime
from string import atof, rfind
import Acquisition
DevelopmentMode=None

try:
    home=CUSTOMER_HOME,SOFTWARE_HOME,SOFTWARE_URL
    CUSTOMER_HOME,SOFTWARE_HOME,SOFTWARE_URL=home
except:
    # Debugger support
    try: home=os.environ['SOFTWARE_HOME']
    except:
	home=os.getcwd()
        if home[-4:]=='/bin': home=home[:-4]
    CUSTOMER_HOME=sys.modules['__builtin__'].CUSTOMER_HOME=home
    SOFTWARE_HOME=sys.modules['__builtin__'].SOFTWARE_HOME=home
    SOFTWARE_URL=sys.modules['__builtin__'].SOFTWARE_URL=''


from BoboPOS import Persistent, PickleDictionary
import BoboPOS.PersistentMapping
sys.modules['PersistentMapping']=BoboPOS.PersistentMapping # hack for bw comp
from BoboPOS.PersistentMapping import PersistentMapping

import DocumentTemplate, MethodObject
from AccessControl.PermissionRole import PermissionRole

class ApplicationDefaultPermissions:
    _View_Permission='Manager', 'Anonymous'
    
def default__class_init__(self):
    dict=self.__dict__
    have=dict.has_key
    ft=type(default__class_init__)
    for name, v in dict.items():
	if hasattr(v,'_need__name__') and v._need__name__:
	    v.__dict__['__name__']=name
	    if name=='manage' or name[:7]=='manage_':
		name=name+'__roles__'
		if not have(name): dict[name]='Manager',
	elif name=='manage' or name[:7]=='manage_' and type(v) is ft:
	    name=name+'__roles__'
	    if not have(name): dict[name]='Manager',

    if hasattr(self, '__ac_permissions__'):
	for acp in self.__ac_permissions__:
	    pname, mnames = acp[:2]
	    pr=PermissionRole(pname)
	    for mname in mnames:
		try: getattr(self, mname).__roles__=pr
		except: dict[mname+'__roles__']=pr
	    pname=pr._p
	    if not hasattr(ApplicationDefaultPermissions, pname):
		if len(acp) > 2:
		    setattr(ApplicationDefaultPermissions, pname, acp[2])
		else:
		    setattr(ApplicationDefaultPermissions, pname, ('Manager',))

Persistent.__dict__['__class_init__']=default__class_init__

class PersistentUtil:

    def bobobase_modification_time(self):
	try:
	    t=self._p_mtime
	    if t is None: return DateTime()
	except: t=0
	return DateTime(t)

    def locked_in_session(self):
	oid=self._p_oid
	return (oid and SessionBase.locks.has_key(oid)
		and SessionBase.verify_lock(oid))

    def modified_in_session(self):
	jar=self._p_jar
	if jar is None:
	    if hasattr(self,'aq_parent') and hasattr(self.aq_parent, '_p_jar'):
		jar=self.aq_parent._p_jar
	    if jar is None: return 0
	if not jar.name: return 0
	try: jar.db[self._p_oid]
	except: return 0
	return 1

for k, v in PersistentUtil.__dict__.items(): Persistent.__dict__[k]=v
    



class HTML(DocumentTemplate.HTML,Persistent,):
    "Persistent HTML Document Templates"

class HTMLDefault(DocumentTemplate.HTMLDefault,Persistent,):
    "Persistent Default HTML Document Templates"

class HTMLFile(DocumentTemplate.HTMLFile,MethodObject.Method,):
    "Persistent HTML Document Templates read from files"

    class func_code: pass
    func_code=func_code()
    func_code.co_varnames='trueself', 'self', 'REQUEST'
    func_code.co_argcount=3
    _need__name__=1
    _v_last_read=0

    def __init__(self,name,_prefix=None, **kw):
	if _prefix is None: _prefix=SOFTWARE_HOME+'/lib/python'
	elif type(_prefix) is not type(''): _prefix=package_home(_prefix)

	args=(self, '%s/%s.dtml' % (_prefix,name))
	apply(HTMLFile.inheritedAttribute('__init__'),args,kw)

    def __call__(self, *args, **kw):
        if DevelopmentMode:
            t=os.stat(self.raw)
            if t != self._v_last_read:
                self.cook()
                self._v_last_read=t
	return apply(HTMLFile.inheritedAttribute('__call__'),
		     (self,)+args[1:],kw)

data_dir     = CUSTOMER_HOME+'/var'
BobobaseName = '%s/Data.bbb' % data_dir

HTML.shared_globals['SOFTWARE_URL']=SOFTWARE_URL

from App.Dialogs import MessageDialog

SessionNameName='Principia-Session'

def package_home(globals_dict):
    __name__=globals_dict['__name__']
    m=sys.modules[__name__]
    if hasattr(m,'__path__'): return m.__path__[0]
    return sys.modules[__name__[:rfind(__name__,'.')]].__path__[0]
    
# utility stuff

def attrget(o,name,default):
    if hasattr(o,name): return getattr(o,name)
    return default

class Selector:
    def __init__(self, key):
        self._k=key
    def __call__(self, o):
        return o[key]

class MultipleSelector:
    def __init__(self, keys):
        self._k=keys
    def __call__(self, o):
        r=[]
        a=r.append
        for key in self._k: a(o[key])
        return r
    

def getitems(o,names):
    r=[]
    for name in names:
        v=o[name]
	r.append(v)
    return r
        
