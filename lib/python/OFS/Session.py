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
__doc__='''A drop-in object that represents a session.



$Id: Session.py,v 1.3 1997/11/07 18:51:13 jim Exp $'''

import time, SimpleItem, AccessControl.Role, Persistence, Acquisition, Globals
from string import rfind

_addForm=Globals.HTMLFile('OFS/sessionAdd')
def addForm(realself, self, REQUEST, **ignored):
    return _addForm(self, REQUEST,
		    selectedRoles=map(
			lambda i:
			('<OPTION VALUE="%s"%s>%s' %
			 (i, i=='manage' and ' SELECTED' or '', i))
			, self.validRoles()),
		    aclEChecked=' CHECKED', aclAChecked='', aclPChecked=''
		    )

def add(self, id, title, acl_type='A',acl_roles=[], REQUEST=None):
    'Add a session'
    i=Session()
    i._init(id, title, REQUEST)
    i._setRoles(acl_type,acl_roles)
    self._setObject(id,i)
    return self.manage_main(self,REQUEST)


class Session(Persistence.Persistent,
	      AccessControl.Role.RoleManager,
	      SimpleItem.Item,
	      Acquisition.Implicit):

    '''Model sessions as drop-in objects
    '''

    meta_type='Session'
    icon='OFS/session.gif'

    def _init(self, id, title, REQUEST):
	self.id=id
	self.title=title
	cookie=REQUEST['PATH_INFO']
	l=rfind(cookie,'/')
	if l >= 0: cookie=cookie[:l]
	self.cookie="%s/%s" % (cookie, id)

    manage=Globals.HTMLFile('OFS/sessionEdit')
    index_html=Globals.HTMLFile('OFS/session')

    def manage_edit(self, title, acl_type='A',acl_roles=[], REQUEST=None):
	'Modify a session'
	self._setRoles(acl_type,acl_roles)
	self.title=title
	
	if REQUEST is not None: return self.manage_editedDialog(REQUEST)

    def enter(self, REQUEST, RESPONSE):
	'Begin working in a session'
	RESPONSE.setCookie(
	    Globals.SessionNameName, self.cookie,
	    expires="Mon, 27-Dec-99 23:59:59 GMT",
	    path=REQUEST['SCRIPT_NAME'],
	    )
	REQUEST[Globals.SessionNameName]=self.cookie
	return self.index_html(self, REQUEST)
	
    def leave(self, REQUEST, RESPONSE):
	'Temporarily stop working in a session'
	RESPONSE.setCookie(
	    Globals.SessionNameName,'No longer active',
	    expires="Mon, 27-Aug-84 23:59:59 GMT",
	    path=REQUEST['SCRIPT_NAME'],
	    )
	REQUEST[Globals.SessionNameName]=''
	return self.index_html(self, REQUEST)
	
    def leave_another(self, REQUEST, RESPONSE):
	'Leave a session that may not be the current session'
	self.leave(REQUEST, RESPONSE)
	RESPONSE.setStatus(302)
	RESPONSE['Location']=REQUEST['URL2']+'/manage_main'
	
    def save(self, remark, REQUEST):
	'Make session changes permanent'
	Globals.SessionBase[self.cookie].commit(remark)
	if REQUEST is not None: return self.index_html(self, REQUEST)
    
    def discard(self, REQUEST):
	'Discard changes made during the session'
	Globals.SessionBase[self.cookie].abort()
	if REQUEST is not None: return self.index_html(self, REQUEST)
	
    def nonempty(self): return Globals.SessionBase[self.cookie].nonempty()

__version__='$Revision: 1.3 $'[11:-2]




############################################################################## 
#
# $Log: Session.py,v $
# Revision 1.3  1997/11/07 18:51:13  jim
# Made an implicit acquirer.
#
# Revision 1.2  1997/11/07 17:43:19  jim
# Added a feature to exit another session.
#
# Revision 1.1  1997/11/07 16:13:15  jim
# *** empty log message ***
#
#
