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



$Id: Version.py,v 1.10 1997/12/31 17:17:04 brian Exp $'''

import time, OFS.SimpleItem, AccessControl.Role
import Persistence, Acquisition, Globals
from string import rfind

_addForm=Globals.HTMLFile('sessionAdd', globals())
def addForm(realself, self, REQUEST, **ignored):
    return _addForm(self, REQUEST)

def add(self, id, title, REQUEST=None):
    'Add a session'
    i=Session()
    i._init(id, title, REQUEST)
    self._setObject(id,i)
    return self.manage_main(self,REQUEST)


class Session(Persistence.Persistent,
	      AccessControl.Role.RoleManager,
	      OFS.SimpleItem.Item,
	      Acquisition.Implicit):

    '''Model sessions as drop-in objects
    '''

    meta_type='Session'
    icon='session'

    manage_options=({'icon':'', 'label':'Join/Leave',
		     'action':'manage_main', 'target':'manage_main',
		    },
		    {'icon':'', 'label':'Properties',
		     'action':'manage_propertiesForm', 'target':'manage_main',
	            },
		    {'icon':'', 'label':'Security',
		     'action':'manage_access', 'target':'manage_main',
		    },
		    {'icon':'', 'label':'Undo',
		     'action':'manage_UndoForm','target':'manage_main',
		    },
		   )

    __ac_permissions__=(
    ('View management screens', ['manage','manage_tabs','index_html']),
    ('Change permissions', ['manage_access']),
    ('Edit session', ['manage_edit']),
    ('Join/leave session', ['enter','leave','leave_another']),
    ('Save/discard session', ['save','discard']),
    )
   
    __ac_types__=(('Full Access', map(lambda x: x[0], __ac_permissions__)),
		 )

    def _init(self, id, title, REQUEST):
	self.id=id
	self.title=title
	cookie=REQUEST['PATH_INFO']
	l=rfind(cookie,'/')
	if l >= 0: cookie=cookie[:l]
	self.cookie="%s/%s" % (cookie, id)

    manage=manage_main=Globals.HTMLFile('sessionEdit', globals())
    index_html=Globals.HTMLFile('session', globals())

    def title_and_id(self):
	r=Session.inheritedAttribute('title_and_id')(self)
	if Globals.SessionBase[self.cookie].nonempty(): return '%s *' % r
	return r

    def manage_edit(self, title, REQUEST=None):
	'Modify a session'
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

__version__='$Revision: 1.10 $'[11:-2]




############################################################################## 
#
# $Log: Version.py,v $
# Revision 1.10  1997/12/31 17:17:04  brian
# Security update
#
# Revision 1.9  1997/12/19 17:06:20  jim
# moved Sessions and Daft folders here.
#
# Revision 1.8  1997/12/18 16:42:02  jeffrey
# *** empty log message ***
#
# Revision 1.7  1997/12/18 13:36:57  jim
# Rearranged management options to make the join/leave screen the
# default.
#
# Revision 1.6  1997/12/12 21:49:44  brian
# ui update
#
# Revision 1.5  1997/12/05 17:13:51  brian
# New UI
#
# Revision 1.4  1997/11/11 19:25:48  jim
# Changed title_and_id method to include a flag to indicate whether a
# session has unsaved changes.
#
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
