
"""Global definitions"""

__version__='$Revision: 1.11 $'[11:-2]

import sys, os
from string import atof, rfind

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


