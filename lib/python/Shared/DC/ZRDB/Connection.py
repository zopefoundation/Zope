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


$Id: Connection.py,v 1.2 1997/12/05 21:33:12 jim Exp $'''
__version__='$Revision: 1.2 $'[11:-2]

import Globals, OFS.SimpleItem, AccessControl.Role, Persistence, Acquisition
from DateTime import DateTime
from App.Dialogs import MessageDialog

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

    def __setstate__(self, state):
	Persistence.Persistent.__setstate__(self, state)
	if self.connection_string: self.connect(self.connection_string)

    def title_and_id(self):
	s=Connection.inheritedAttribute('title_and_id')(self)
	if hasattr(self, '_v_connected') and self._v_connected:
	    s="%s, which is connected" % s
	else: 
	    s="%s, which is <font color=red> not connected</font>" % s
	return s

    def title_or_id(self):
	s=Connection.inheritedAttribute('title_or_id')(self)
	if hasattr(self, '_v_connected') and self._v_connected:
	    s="%s (connected)" % s
	else: 
	    s="%s (<font color=red> not connected</font>)" % s
	return s

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
	if REQUEST: return MessageDialog(
	    title='Connection Modified',
	    message='The connection information has been changed',
	    action='manage',
	    )

    def manage_close_connection(self, REQUEST):
	" "
	try: self._v_database_connection.close()
	except: pass
	self._v_connected=''
	if REQUEST: return MessageDialog(
	    title='Connection Closed',
	    message='The connection has been closed',
	    action='manage',
	    )

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
# Revision 1.2  1997/12/05 21:33:12  jim
# major overhall to add record addressing, brains, and support for new interface
#
# Revision 1.1  1997/12/02 17:22:02  jim
# initial
#
#
