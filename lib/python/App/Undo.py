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
__doc__='''short description


$Id: Undo.py,v 1.1 1997/09/23 00:08:43 jim Exp $'''
__version__='$Revision: 1.1 $'[11:-2]

import Globals
from DateTime import DateTime
from string import atof, find, atoi, split

class UndoSupport:

    manage_UndoForm=Globals.HTMLFile('App/undo')

    def undoable_transactions(self, AUTHENTICATION_PATH=None,
			      first_transaction=None,
			      last_transaction=None):

	if AUTHENTICATION_PATH is None:
	    path=self.REQUEST['AUTHENTICATION_PATH']
	else: path=AUTHENTICATION_PATH

	if first_transaction is None:
	    try: first_transaction=self.REQUEST['first_transaction']
	    except: first_transaction=0
	if last_transaction is None:
	    try: last_transaction=self.REQUEST['last_transaction']
	    except: last_transaction=first_transaction+20

	db=Globals.Bobobase._jar.db

	r=[]
	add=r.append
	h=['','']
	for info in db.transaction_info(first_transaction, last_transaction,
					path):
  	    [path, user] = (split(info[2],' ')+h)[:2]
	    add(
		{'pos': info[0],
		 'time': DateTime(atof(info[1])),
		 'id': info[1],
		 'identity': info[2],
		 'user': user,
		 'path': path,
		 'desc': info[3],
		 })

	return r
    
    def manage_undo_transactions(self, transaction_info, REQUEST):
	"""
	"""
	info=[]
	jar=Globals.Bobobase._jar
	db=jar.db
	for i in transaction_info:
	    l=find(i,' ')
	    oids=db.Toops( (i[:l],), atoi(i[l:]))
	    jar.reload_oids(oids)

	if REQUEST: return self.manage_main(self, REQUEST)
		 
		 


############################################################################## 
#
# $Log: Undo.py,v $
# Revision 1.1  1997/09/23 00:08:43  jim
# *** empty log message ***
#
#
