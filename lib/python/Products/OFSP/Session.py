"""Session object"""

__version__='$Revision: 1.14 $'[11:-2]

import Globals, time
from AccessControl.Role import RoleManager
from Globals import MessageDialog
from Persistence import Persistent
from Acquisition import Implicit
from OFS.SimpleItem import Item
from string import rfind


manage_addSessionForm=Globals.HTMLFile('sessionAdd', globals())

def manage_addSession(self, id, title, REQUEST=None):
    """ """
    self._setObject(id, Session(id,title,REQUEST))
    return self.manage_main(self,REQUEST)


class Session(Persistent,Implicit,RoleManager,Item):
    """ """
    meta_type='Session'
    icon     ='misc_/OFSP/session'

    manage_options=({'label':'Join/Leave', 'action':'manage_main',
		     'target':'manage_main',
		    },
		    {'label':'Properties', 'action':'manage_editForm',
		     'target':'manage_main',
	            },
		    {'label':'Security', 'action':'manage_access',
		     'target':'manage_main',
		    },
		   )

    __ac_permissions__=(
    ('View management screens', ['manage','manage_tabs','manage_editForm',
				 'index_html']),
    ('Change permissions', ['manage_access']),
    ('Edit session', ['manage_edit']),
    ('Join/leave session', ['enter','leave','leave_another']),
    ('Save/discard session', ['save','discard']),
    )
   
    __ac_types__=(('Full Access', map(lambda x: x[0], __ac_permissions__)),
		 )

    def __init__(self, id, title, REQUEST):
	self.id=id
	self.title=title
	cookie=REQUEST['PATH_INFO']
	l=rfind(cookie,'/')
	if l >= 0: cookie=cookie[:l]
	self.cookie="%s/%s" % (cookie, id)

    manage=manage_main=Globals.HTMLFile('session', globals())
    manage_editForm   =Globals.HTMLFile('sessionEdit', globals())

    def title_and_id(self):
	r=Session.inheritedAttribute('title_and_id')(self)
	if Globals.SessionBase[self.cookie].nonempty(): return '%s *' % r
	return r

    def manage_edit(self, title, REQUEST=None):
	""" """
	self.title=title
	if REQUEST: return MessageDialog(
		    title  ='Success!',
		    message='Your changes have been saved',
		    action ='manage_main')

    def enter(self, REQUEST, RESPONSE):
	"""Begin working in a session"""
	RESPONSE.setCookie(
	    Globals.SessionNameName, self.cookie,
	    #expires="Mon, 27-Dec-99 23:59:59 GMT",
	    path=REQUEST['SCRIPT_NAME'],
	    )
	return RESPONSE.redirect(REQUEST['URL1']+'/manage_main')
	
    def leave(self, REQUEST, RESPONSE):
	"""Temporarily stop working in a session"""
	RESPONSE.setCookie(
	    Globals.SessionNameName,'No longer active',
	    expires="Mon, 27-Aug-84 23:59:59 GMT",
	    path=REQUEST['SCRIPT_NAME'],
	    )
	return RESPONSE.redirect(REQUEST['URL1']+'/manage_main')
	
    def leave_another(self, REQUEST, RESPONSE):
	"""Leave a session that may not be the current session"""
	return self.leave(REQUEST, RESPONSE)

    def save(self, remark, REQUEST=None):
	"""Make session changes permanent"""
	Globals.SessionBase[self.cookie].commit(remark)
	if REQUEST: return self.manage_main(self, REQUEST)
    
    def discard(self, REQUEST=None):
	'Discard changes made during the session'
	Globals.SessionBase[self.cookie].abort()
	if REQUEST: return self.manage_main(self, REQUEST)
	
    def nonempty(self): return Globals.SessionBase[self.cookie].nonempty()






############################################################################## 
#
# $Log: Session.py,v $
# Revision 1.14  1998/02/10 18:40:38  jim
# Changed creation method names for latest security scheme.
#
# Revision 1.13  1998/01/02 17:41:19  brian
# Made undo available only in folders
#
# Revision 1.12  1997/12/31 20:34:05  brian
# Fix bad ref to SimpleItem caused by moving
#
# Revision 1.11  1997/12/31 19:34:57  jim
# Brians changes.
#
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
