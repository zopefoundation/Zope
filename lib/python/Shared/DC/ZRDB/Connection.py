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


$Id: Connection.py,v 1.5 1998/01/16 19:12:54 jim Exp $'''
__version__='$Revision: 1.5 $'[11:-2]

import Globals, OFS.SimpleItem, AccessControl.Role, Persistence, Acquisition
from DateTime import DateTime
from App.Dialogs import MessageDialog
from Globals import HTMLFile

class Connection(
    Persistence.Persistent,
    AccessControl.Role.RoleManager,
    OFS.SimpleItem.Item,
    Acquisition.Implicit,
    ):    

    # Specify definitions for tabs:
    manage_options=(
	{'label':'Status', 'action':'manage_main'},
	{'label':'Properties', 'action':'manage_properties'},
	{'label':'Security',   'action':'manage_access'},
	)
 
    # Specify how individual operations add up to "permissions":
    __ac_permissions__=(
	('View management screens', ('manage_tabs','manage_main',
				     'manage_properties')),
	('Change permissions',      ('manage_access',)            ),
	('Change',                  ('manage_edit',)              ),
	('Open/Close',              ('manage_open_connection',
				     'manage_close_connection')),
	)
   
    # Define pre-defined types of access:
    __ac_types__=(('Full Access', map(lambda x: x[0], __ac_permissions__)),
		  )

    _v_connected=''
    connection_string=''

    def __init__(self, id, title, connection_string, check=None):
	self.id=id
	self.edit(title, connection_string, check)

    def __setstate__(self, state):
	Persistence.Persistent.__setstate__(self, state)
	if self.connection_string:
	    try: self.connect(self.connection_string)
	    except: pass

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

    def connected(self): return self._v_connected

    def edit(self, title, connection_string, check=1):
	self.title=title
	self.connection_string=connection_string
	if check: self.connect(connection_string)
    
    manage_properties=HTMLFile('connectionEdit', globals())
    def manage_edit(self, title, connection_string, check=None, REQUEST=None):
	"""Change connection
	"""
	self.edit(title, connection_string, check)
	if REQUEST is not None:
	    return MessageDialog(
		title='Edited',
		message='<strong>%s</strong> has been edited.' % self.id,
		action ='./manage_main',
		)


    manage_main=HTMLFile('connectionStatus', globals())

    def manage_close_connection(self, REQUEST):
	" "
	try: self._v_database_connection.close()
	except: pass
	self._v_connected=''
	return self.manage_main(self, REQUEST)

    def manage_open_connection(self, REQUEST=None):
	" "
	self.connect(self.connection_string)
	return self.manage_main(self, REQUEST)

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
# Revision 1.5  1998/01/16 19:12:54  jim
# Changed so failure to connect to the database does not prevent
# activation.
#
# Revision 1.4  1998/01/07 16:27:15  jim
# Brought up to date with latest Principia models.
#
# Revision 1.3  1997/12/18 13:35:09  jim
# Added ImageFile usage.
#
# Revision 1.2  1997/12/05 21:33:12  jim
# major overhall to add record addressing, brains, and support for new interface
#
# Revision 1.1  1997/12/02 17:22:02  jim
# initial
#
#
