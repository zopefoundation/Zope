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


$Id: Undo.py,v 1.7 1998/01/12 16:50:32 jim Exp $'''
__version__='$Revision: 1.7 $'[11:-2]

import Globals
from DateTime import DateTime
from string import atof, find, atoi, split, rfind

class UndoSupport:

    manage_UndoForm=Globals.HTMLFile('undo', globals(),
				     batch_size=20, first_transaction=0,
				     last_transaction=20)

    def undoable_transactions(self, AUTHENTICATION_PATH=None,
			      first_transaction=None,
			      last_transaction=None,
			      batch_size=20):

	if AUTHENTICATION_PATH is None:
	    path=self.REQUEST['AUTHENTICATION_PATH']
	else: path=AUTHENTICATION_PATH

	if first_transaction is None:
	    try: first_transaction=self.REQUEST['first_transaction']
	    except: first_transaction=0
	if last_transaction is None:
	    try: last_transaction=self.REQUEST['last_transaction']
	    except: last_transaction=first_transaction+batch_size

	db=self._p_jar.db

	r=[]
	add=r.append
	h=['','']
	try:    trans_info=db.transaction_info(first_transaction,
					       last_transaction,path)
        except: trans_info=[]

	for info in trans_info:
	    while len(info) < 4: info.append('')
  	    [path, user] = (split(info[2],' ')+h)[:2]
	    t=info[1]
	    l=find(t,' ')
	    if l >= 0: t=t[l:]
	    add(
		{'pos': info[0],
		 'time': DateTime(atof(t)),
		 'id': info[1],
		 'identity': info[2],
		 'user': user,
		 'path': path,
		 'desc': info[3],
		 })
	return r or []
    
    def manage_undo_transactions(self, transaction_info, REQUEST=None):
	"""
	"""
	info=[]
	jar=self._p_jar
	db=jar.db
	for i in transaction_info:
	    l=rfind(i,' ')
	    oids=db.Toops( (i[:l],), atoi(i[l:]))
	    jar.reload_oids(oids)

	if REQUEST is None: return

	RESPONSE=REQUEST['RESPONSE']
	RESPONSE.setStatus(302)
	RESPONSE['Location']="%s/manage_main" % REQUEST['URL1']
	return ''
		 
Globals.default__class_init__(UndoSupport)		 


############################################################################## 
#
# $Log: Undo.py,v $
# Revision 1.7  1998/01/12 16:50:32  jim
# Made some changes to enhance batch processing.
# Batch size is also now a parameter.
#
# Revision 1.6  1998/01/09 21:32:22  brian
# Added __class_init__
#
# Revision 1.5  1997/12/18 16:45:30  jeffrey
# changeover to new ImageFile and HTMLFile handling
#
# Revision 1.4  1997/11/07 17:06:28  jim
# Added session support.
#
# Revision 1.3  1997/10/23 17:43:27  jim
# Added fix to cover certain unusual situations.
#
# Revision 1.2  1997/09/25 21:03:50  brian
# Fixed bug
#
# Revision 1.1  1997/09/23 00:08:43  jim
# *** empty log message ***
#
#
