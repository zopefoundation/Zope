"""Session object"""

__version__='$Revision: 1.21 $'[11:-2]

import Globals, time
from AccessControl.Role import RoleManager
from Globals import MessageDialog
from Persistence import Persistent
from Acquisition import Implicit
from OFS.SimpleItem import Item
from string import rfind
from Globals import HTML
from App.Dialogs import MessageDialog

manage_addSessionForm=Globals.HTMLFile('sessionAdd', globals())

def manage_addSession(self, id, title, REQUEST=None):
    """ """
    self._setObject(id, Session(id,title,REQUEST))
    return self.manage_main(self,REQUEST)


class Session(Persistent,Implicit,RoleManager,Item):
    """ """
    meta_type='Session'
    icon     ='misc_/OFSP/session'

    manage_options=({'label':'Join/Leave', 'action':'manage_main'},
		    {'label':'Properties', 'action':'manage_editForm'},
		    {'label':'Security', 'action':'manage_access'},
		   )

    __ac_permissions__=(
    ('View management screens', ['manage','manage_tabs','manage_editForm', '']),
    ('Change permissions', ['manage_access']),
    ('Change Sessions', ['manage_edit']),
    ('Join/leave Sessions', ['enter','leave','leave_another']),
    ('Save/discard Session changes', ['save','discard']),
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
        if (REQUEST.has_key('SERVER_SOFTWARE') and
            REQUEST['SERVER_SOFTWARE'][:9]=='Microsoft'):
            # IIS doesn't handle redirect headers correctly
            return MessageDialog(
                action=REQUEST['URL1']+'/manage_main',
                message=('If cookies are enabled by your browser, then '
                         'you should have joined session %s.'
                         % self.id)
                )
	return RESPONSE.redirect(REQUEST['URL1']+'/manage_main')
	
    def leave(self, REQUEST, RESPONSE):
	"""Temporarily stop working in a session"""
	RESPONSE.setCookie(
	    Globals.SessionNameName,'No longer active',
	    expires="Mon, 27-Aug-84 23:59:59 GMT",
	    path=REQUEST['SCRIPT_NAME'],
	    )
        if (REQUEST.has_key('SERVER_SOFTWARE') and
            REQUEST['SERVER_SOFTWARE'][:9]=='Microsoft'):
            # IIS doesn't handle redirect headers correctly
            return MessageDialog(
                action=REQUEST['URL1']+'/manage_main',
                message=('If cookies are enabled by your browser, then '
                         'you should have left session %s.'
                         % self.id)
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
    
    def _notifyOfCopyTo(self, container, isMove=0):
        if isMove and self.nonempty():
            raise 'Copy Error', (
                "You cannot copy a %s object with <b>unsaved</b> changes.\n"
                "You must <b>save</b> the changes first."
                % self.meta_type)


import __init__
__init__.need_license=1


############################################################################## 
#
# $Log: Version.py,v $
# Revision 1.21  1998/09/24 20:13:40  jim
# Added checks to prevent moving uncommitted sessions and drafts
#
# Revision 1.20  1998/09/24 19:21:52  jim
# added Draft objects
#
# Revision 1.19  1998/05/20 22:07:32  jim
# Updated permissions.
#
# Revision 1.18  1998/05/20 17:58:17  jim
# Got rid of ac_types.
#
# Revision 1.17  1998/05/20 17:57:40  jim
# Included '' in permission settings.
#
# Revision 1.16  1998/04/13 19:23:06  jim
# Added license flag
#
# Revision 1.15  1998/03/11 18:21:56  jim
# Fixed bug in permissions settings.
#
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
