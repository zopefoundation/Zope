"""Global definitions"""

__version__='$Revision: 1.1 $'[11:-2]

from SingleThreadedTransaction import PickleDictionary, Persistent
from SingleThreadedTransaction import PersistentMapping
import STPDocumentTemplate
from App.Dialogs import MessageDialog

HTML     = STPDocumentTemplate.HTML
HTMLFile = STPDocumentTemplate.HTMLFile

try:
    home=CUSTOMER_HOME, SOFTWARE_HOME, SOFTWARE_URL
    CUSTOMER_HOME, SOFTWARE_HOME, SOFTWARE_URL = home
except:
    CUSTOMER_HOME='../../customer/private'
    SOFTWARE_HOME='../..'
    SOFTWARE_URL=''

data_dir     = CUSTOMER_HOME+'/var'
BobobaseName = '%s/Data.bbb' % data_dir

HTML.shared_globals=['SOFTWARE_URL']=SOFTWARE_URL

##########################################################################
#
# Log
#
# $Log: Globals.py,v $
# Revision 1.1  1997/08/13 18:58:39  jim
# initial
#
#
