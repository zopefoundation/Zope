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
__doc__='''\
Provide an area where people can work without others seeing their changes.

A Draft folder is a surrogate for a folder.  It get\'s subobjects by
gettingthem from a session copy of a base folder.

$Id: DraftFolder.py,v 1.1 1997/11/11 21:05:44 jim Exp $'''
__version__='$Revision: 1.1 $'[11:-2]

import time, SimpleItem, AccessControl.Role, Persistence, Acquisition, Globals
import AccessControl.User, Session
from string import rfind
from App.Management import Management
from Globals import HTMLFile

addForm=HTMLFile('OFS/draftFolderAdd')

def add(self,id,baseid,title='',REQUEST=None):
    """Add a new Folder object"""
    i=DraftFolder()
    i._init(id, baseid, title, self,REQUEST)
    self._setObject(id,i)
    if REQUEST is not None: return self.manage_main(self,REQUEST)

class DraftFolder(Persistence.Persistent,
		  AccessControl.Role.RoleManager,
		  SimpleItem.Item,
		  Acquisition.Implicit,
		  Management,
		  ):

    meta_type='Draft Folder'
    icon='OFS/DraftFolder.gif'

    manage_options=(
    {'icon':icon, 'label':'Contents',
     'action':'manage_main',   'target':'manage_main'},
    {'icon':'OFS/Properties_icon.gif', 'label':'Properties',
     'action':'manage_propertiesForm',   'target':'manage_main'},
    {'icon':'AccessControl/AccessControl_icon.gif', 'label':'Access Control',
     'action':'manage_rolesForm',   'target':'manage_main'},
    {'icon':'App/undo_icon.gif', 'label':'Undo',
     'action':'manage_UndoForm',   'target':'manage_main'},
    {'icon':'OFS/DraftFolderControl.gif', 'label':'Supervise',
     'action':'manage_Supervise',   'target':'manage_main'},
    )

    def _init(self, id, baseid, title, parent, REQUEST):
	if hasattr(parent, 'aq_self'): parent=parent.aq_self
	if not hasattr(parent, baseid):
	    raise 'Input Error', (
		'The specified base folder, %s, does not exist'
		% baseid
		)
	self.id=id
	self.baseid=baseid
	self.title=title
	cookie=REQUEST['PATH_INFO']
	if cookie[:1] != '/': cookie='/'+cookie
	l=rfind(cookie,'/')
	if l >= 0: cookie=cookie[:l]
	self.cookie="%s/%s" % (cookie, id)
	self.cookie_name="%s-Draft-Folder-%s" % (id,baseid)

	self.__allow_groups__=Supervisor()
	self.__allow_groups__._init()

    def title_and_id(self):
	r=DraftFolder.inheritedAttribute('title_and_id')(self)
	r='%s *' % r
	try: base=getattr(self.aq_parent, self.baseid)
	except: base=None
	
	if base is not None:
	    r="%s Draft Folder: %s" % (base.title_or_id(), r)
	return r

    def _base(self, cookie):

	# Check for base object
	if hasattr(self, 'aq_parent'): parent=self.aq_parent
	else: parent=None
	if hasattr(parent, 'aq_self'): ps=parent.aq_self
	else: ps=parent
	baseid=self.baseid
	if not hasattr(ps, baseid):
	    raise 'Draft Folder Error', (
	    '''The base folder for the draft folder, <em>%s</em>,
	    does not exist.'''
	    % self.cookie
	    )

	base=getattr(parent, baseid)

	pd=Globals.SessionBase[cookie]
	oids=[base._p_oid]
	while hasattr(base, 'aq_parent'):
	    base=base.aq_parent
	    if hasattr(base, '_p_oid'): oids.append(base._p_oid)
	    else: break

	while oids:
	    oid=oids[-1]
	    del oids[-1]
	    base=pd.jar[oid].__of__(base)

	return base


    def __bobo_traverse__(self, REQUEST, name):
	
	cookie_name=self.cookie_name
	cookie=''
	if REQUEST.has_key(cookie_name):
	    if REQUEST[cookie_name] == self.cookie:
		cookie=self.cookie
	    else:
		# Oops, the cookie is broken, better erase it:
		RESPONSE=REQUEST['RESPONSE']
		RESPONSE.setCookie(
		    self.cookie_name,'No longer active',
		    expires="Mon, 27-Aug-84 23:59:59 GMT",
		    path=REQUEST['SCRIPT_NAME']+self.cookie,
		    )
		REQUEST[self.cookie_name]=''

	PATH_INFO=REQUEST['PATH_INFO']
	if PATH_INFO[:1] != '/': PATH_INFO='/'+PATH_INFO
	if PATH_INFO==self.cookie+'/manage':
	    if not cookie: return self.manage
	    return Management.manage
	if PATH_INFO==self.cookie+'/manage_menu': return self.manage_menu

	if name=='manage_Supervise': 
	    raise 'Redirect', (
		"%s/manage_draftFolder-%s/manage"
		% (REQUEST['URL2'], self.id))

	if not cookie: raise 'Redirect', (
	    REQUEST['URL1']+'/manage')



	__traceback_info__=PATH_INFO, cookie, self.cookie

	self=self._base(cookie)

	try:
	    v=getattr(self, name)
	    if hasattr(v, 'isDocTemp') and v.isDocTemp and (
		PATH_INFO=="%s/%s" % (cookie, name) or
		PATH_INFO==cookie and name=='index_html'
		):
		def v(REQUEST, _dt_=v, _self_=self):
		    "Damn, need this so template gets called with right thing"
		    return _dt_(_self_, REQUEST)
	    return v
	except AttributeError:
	    try: return self[name]
	    except KeyError:
		raise 'NotFound',(
		    "Sorry, the requested document does not exist.<p>"
		    "\n<!--\n%s\n%s\n-->" % (name,REQUEST['REQUEST_METHOD']))

    def manage(self, REQUEST):
	"Access management interface making sure that user gets a cookie"
	cookie=self.cookie
	cookie_name=self.cookie_name
	REQUEST['RESPONSE'].setCookie(
	    cookie_name, cookie,
	    expires="Mon, 27-Dec-99 23:59:59 GMT",
	    path=REQUEST['SCRIPT_NAME']+cookie,
	    )
	REQUEST[cookie_name]=cookie
	return Management.manage(self, REQUEST)

    def manage_supervisor(self): return self.__allow_groups__
    
class Supervisor(AccessControl.User.UserFolder, Session.Session):

    manage=manage_main=HTMLFile('OFS/DraftFolderSupervisor')
    manage_options=() # This is a simple item

    
    
    

############################################################################## 
#
# $Log: DraftFolder.py,v $
# Revision 1.1  1997/11/11 21:05:44  jim
# Draft Folders
#
#
