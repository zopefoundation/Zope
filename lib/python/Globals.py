
"""Global definitions"""

__version__='$Revision: 1.16 $'[11:-2]

import sys, os
from DateTime import DateTime
from string import atof, rfind
import Acquisition

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



from SingleThreadedTransaction import PickleDictionary, Persistent
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

    def __init__(self,name,_prefix=None, **kw):
	if _prefix is None: _prefix=SOFTWARE_HOME+'/lib/python'
	elif type(_prefix) is not type(''): _prefix=package_home(_prefix)

	args=(self, '%s/%s.dtml' % (_prefix,name))
	apply(HTMLFile.inheritedAttribute('__init__'),args,kw)

    def __call__(self, *args, **kw):
	return apply(HTMLFile.inheritedAttribute('__call__'),
		     (self,)+args[1:],kw)

data_dir     = CUSTOMER_HOME+'/var'
BobobaseName = '%s/Data.bbb' % data_dir

HTML.shared_globals['SOFTWARE_URL']=SOFTWARE_URL

from App.Dialogs import MessageDialog

SessionNameName='Principia-Session'

if atof(sys.version[:3]) >= 1.5:
    def package_home(globals_dict):
	__name__=globals_dict['__name__']
	return sys.modules[__name__[:rfind(__name__,'.')]].__path__[0]
else:
    # ni
    def package_home(globals_dict):
	return globals_dict['__'].__path__[0]
    

##########################################################################
#
# Log
#
# $Log: Globals.py,v $
# Revision 1.16  1998/09/29 19:22:03  jim
# Added Acquisition
#
# Revision 1.15  1998/05/26 22:28:14  jim
# Fixed stupid bug in bobobase_modification_time
#
# Revision 1.14  1998/05/22 22:25:42  jim
# Moved some DB-related methods from ObjectManager and SimpleItem and stuffed them
# right into Persistent here.
#
# Revision 1.13  1998/05/08 14:52:20  jim
# Modified default class init to work with new permission machinery.
#
# Revision 1.12  1998/01/08 17:38:03  jim
# Added class initialization machinery to:
#
#   - Make sure HTMLFile instances got a __name__ that matched the name
#     they were assigned to in the class, and
#
#   - Give HTMLFile and Python methods whos names are 'manage' or
#     begin with 'manage_' a __roles__ of ('Manager',)
#
# Revision 1.11  1997/12/23 15:08:20  jim
# Changed HTMLFile to use method protocol rather than acquisition
# protocol.
#
# Revision 1.10  1997/12/17 16:36:50  jim
# Changed HTML file to support passing in globals()
#
# Revision 1.9  1997/11/21 19:33:45  brian
# Fixed out-of-date debugger support to add correct SH, CH, SU
#
# Revision 1.8  1997/11/07 17:12:15  jim
# Added SesionNameName.
#
# Revision 1.7  1997/09/15 17:03:53  jim
# Got rid of private.
#
# Revision 1.6  1997/09/02 21:39:43  jim
# Moved MessageDialog to end to deal with recursion in module imports.
#
# Revision 1.5  1997/08/28 19:32:36  jim
# Jim told Paul to do it
#
# Revision 1.4  1997/08/13 22:14:04  jim
# *** empty log message ***
#
# Revision 1.3  1997/08/13 21:42:45  jim
# Added back specialized HTMLFile
#
# Revision 1.2  1997/08/13 19:04:00  jim
# *** empty log message ***
#
# Revision 1.1  1997/08/13 18:58:39  jim
# initial
#
#


