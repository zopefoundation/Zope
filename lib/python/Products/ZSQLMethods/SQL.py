#!/bin/env python
############################################################################## 
#
#     Copyright 
#
#       Copyright 1996 Digital Creations, L.C., 910 Princess Anne
#       Street, Suite 300, Fredericksburg, Virginia 22401 U.S.A. All
#       rights reserved.
#
############################################################################## 
__doc__='''SQL Methods


$Id: SQL.py,v 1.6 1998/12/02 12:11:49 jim Exp $'''
__version__='$Revision: 1.6 $'[11:-2]

import Shared.DC.ZRDB.DA
from Globals import HTMLFile

def SQLConnectionIDs(self):
    """Find SQL database connections in the current folder and above

    This function return a list of ids.
    """
    ids={}
    have_id=ids.has_key
    StringType=type('')

    while self is not None:
	if hasattr(self, 'objectValues'):
	    for o in self.objectValues():
		if (hasattr(o,'_isAnSQLConnection') and o._isAnSQLConnection
		    and hasattr(o,'id')):
		    id=o.id
		    if type(id) is not StringType: id=id()
		    if not have_id(id):
			if hasattr(o,'title_and_id'): o=o.title_and_id()
			else: o=id
			ids[id]=id
	if hasattr(self, 'aq_parent'): self=self.aq_parent
	else: self=None

    ids=map(lambda item: (item[1], item[0]), ids.items())
    ids.sort()
    return ids

manage_addZSQLMethodForm=HTMLFile('add', globals())
def manage_addZSQLMethod(self, id, title,
				connection_id, arguments, template,
				REQUEST=None):
    """Add an SQL Method

    The 'connection_id' argument is the id of a database connection
    that resides in the current folder or in a folder above the
    current folder.  The database should understand SQL.

    The 'arguments' argument is a string containing an arguments
    specification, as would be given in the SQL method cration form.

    The 'template' argument is a string containing the source for the
    SQL Template.
    """
    self._setObject(id, SQL(id, title, connection_id, arguments, template))
    if REQUEST is not None: return self.manage_main(self,REQUEST)

class SQL(Shared.DC.ZRDB.DA.DA):
    """SQL Database methods

    SQL Database methods are used to access external SQL databases.

    They support three important Principia abstractions:

      - Method

        SQL Methods behave like methods of the folders they are
	accessed in.  In particular, they can be used from other
	methods, like Documents, ExternalMethods, and even other SQL
	Methods.

      - Searchability

        Database methods support the Principia Searchable Object
        Interface.  Search interface wizards can be used to build user
        interfaces to them.  They can be used in joins and
        unions. They provide meta-data about their input parameters
        and result data.

	For more information, see the searchable-object interface
	specification. 

      - Containment

        Database methods support URL traversal to access and invoke
        methods on individual record objects. For example, suppose you
        had an 'employees' database method that took a single argument
        'employee_id'.  Suppose that employees had a 'service_record'
        method (defined in a record class or acquired from a
        folder). The 'service_record' method could be accessed with a
        URL like::

	   employees/employee_id/1234/service_record

    """
    meta_type='Z SQL Database Method'
    icon='misc_/ZSQLMethods/icon'
		
    manage_main=HTMLFile('edit', globals())

