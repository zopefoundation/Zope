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


$Id: SQL.py,v 1.1 1998/01/07 16:29:29 jim Exp $'''
__version__='$Revision: 1.1 $'[11:-2]

import AqueductDA.DA
from Globals import HTMLFile

def SQLConnectionIDs(self):
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

addForm=HTMLFile('add', globals())
def add(self, id, title, connection_id, arguments, template, REQUEST=None):
    """Add a SQL Method to a folder"""
    self._setObject(id, SQL(id, title, connection_id, arguments, template))
    if REQUEST is not None: return self.manage_main(self,REQUEST)

class SQL(AqueductDA.DA.DA):
    meta_type='Aqueduct SQL Database Method'
    icon='misc_/AqueductSQLMethods/icon'
		
    manage_main=HTMLFile('edit', globals())



############################################################################## 
#
# $Log: SQL.py,v $
# Revision 1.1  1998/01/07 16:29:29  jim
# Split out Database Methods
#
#
