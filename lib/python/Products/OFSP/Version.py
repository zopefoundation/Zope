"""Session object"""

__version__='$Revision: 1.23 $'[11:-2]

import Globals, time
from AccessControl.Role import RoleManager
from Globals import MessageDialog
from Globals import Persistent
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
