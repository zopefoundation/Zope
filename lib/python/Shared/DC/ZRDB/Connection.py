############################################################################## 
#
#     Copyright 
#
#       Copyright 1996 Digital Creations, L.C., 910 Princess Anne
#       Street, Suite 300, Fredericksburg, Virginia 22401 U.S.A. All
#       rights reserved.
#
############################################################################## 
__doc__='''Generic Database Connection Support


$Id: Connection.py,v 1.1 1997/12/02 17:22:02 jim Exp $'''
__version__='$Revision: 1.1 $'[11:-2]

import Globals, OFS.SimpleItem, AccessControl.Role, Persistence, Acquisition
from DateTime import DateTime

connection_page=Globals.HTMLFile('AqueductDA/connection')

def addForm(self, REQUEST, database_type):
    return connection_page(
	self, REQUEST,
	action='manage_addAqueduct%sConnection' % database_type,
	database_type=database_type,
	connection_string='',
	connected='')

def add(self,class_,connection_string,check,REQUEST):
    """Add a new Folder object"""
    i=class_()
    i.connection_string=connection_string
    if check: i.connect(connection_string)
    self._setObject(i.id,i)
    return self.manage_main(self,REQUEST)

class Connection(
    Persistence.Persistent,
    AccessControl.Role.RoleManager,
    OFS.SimpleItem.Item,
    Acquisition.Implicit,
    ):    
    icon     ='AqueductDA/DBAdapterFolder_icon.gif'
    meta_type='Aqueduct Database Adapter Folder'
    _v_connected=''
    connection_string=''

    def manage(self, REQUEST):
	"Change the database connection string"
	return connection_page(self, REQUEST, action='manage_connection',
			       database_type=self.database_type)

    def connected(self): return self._v_connected
    
    def manage_connection(self,value,check=None,action='',REQUEST=None):
	'change database connection data'
	if check: self.connect(value)
	else: self.manage_close_connection(REQUEST)
	self.connection_string=value
	return 'This needs to be changed'

    def manage_close_connection(self, REQUEST):
	" "
	try: self._v_database_connection.close()
	except: pass
	self._v_connected=''
	return 'This needs to be changed'

    def __call__(self, v=None):
	try: return self._v_database_connection
	except AttributeError:
	    s=self.connection_string
	    if s: return self.connect(s)
	    raise 'Database Not Connected',(
		'''The database connection is not connected''')

    def connect(self,s):
	try: self._v_database_connection.close()
	except: pass
	self._v_connected=''
	DB=self.factory()
	try: self._v_database_connection=DB(s)
	except:
	    raise 'BadRequest', (
		'<strong>Invalid connection string:</strong><br>'
		+ s)
	self._v_connected=DateTime()

	return self
	
############################################################################## 
#
# $Log: Connection.py,v $
# Revision 1.1  1997/12/02 17:22:02  jim
# initial
#
#
