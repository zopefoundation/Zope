
"""Global definitions"""

__version__='$Revision: 1.3 $'[11:-2]

from SingleThreadedTransaction import PickleDictionary, Persistent
from SingleThreadedTransaction import PersistentMapping
import STPDocumentTemplate
from App.Dialogs import MessageDialog

HTML     = STPDocumentTemplate.HTML

class HTMLFile(STPDocumentTemplate.HTMLFile):
    """ """

    def __init__(self,name='',*args,**kw):
	args=(self, '%s/lib/python/%s.dtml' % (SOFTWARE_HOME,name),) + args
	apply(baseHTMLFile.__init__,args,kw)

try:
    home=CUSTOMER_HOME, SOFTWARE_HOME, SOFTWARE_URL
    CUSTOMER_HOME, SOFTWARE_HOME, SOFTWARE_URL = home
except:
    CUSTOMER_HOME='../../customer/private'
    SOFTWARE_HOME='../..'
    SOFTWARE_URL=''

data_dir     = CUSTOMER_HOME+'/var'
BobobaseName = '%s/Data.bbb' % data_dir

HTML.shared_globals['SOFTWARE_URL']=SOFTWARE_URL

##########################################################################
#
# Log
#
# $Log: Globals.py,v $
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


