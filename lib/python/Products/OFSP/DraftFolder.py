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

$Id: DraftFolder.py,v 1.9 1998/01/02 17:41:19 brian Exp $'''
__version__='$Revision: 1.9 $'[11:-2]


import Globals, Session, time
from AccessControl.Role import RoleManager
from AccessControl.User import UserFolder
from App.Management import Management
from Persistence import Persistent
from Acquisition import Implicit
from OFS.SimpleItem import Item
from Session import Session
from Globals import HTMLFile
from string import rfind




addForm=HTMLFile('draftFolderAdd', globals())

def add(self,id,baseid,title='',REQUEST=None):
    """ """
    self._setObject(id, DraftFolder(id, baseid, title, self, REQUEST))
    if REQUEST: return self.manage_main(self,REQUEST)


class DraftFolder(Persistent,Implicit,RoleManager,Management,Item):
    """ """
    meta_type='Draft Folder'
    icon='misc_/OFSP/DraftFolderIcon'
    isPrincipiaFolderish=1

    manage_options=(
    {'label':'Contents', 'action':'manage_main',
     'target':'manage_main'},
    {'label':'Properties', 'action':'manage_propertiesForm',
     'target':'manage_main'},
    {'label':'Security', 'action':'manage_access',
     'target':'manage_main'},
    {'label':'Undo', 'action':'manage_UndoForm',
     'target':'manage_main'},
    {'label':'Supervise', 'action':'manage_Supervise',
     'target':'manage_main'},
    )

    def __init__(self, id, baseid, title, parent, REQUEST):
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


    def title_and_id(self):
	r=DraftFolder.inheritedAttribute('title_and_id')(self)
	r='%s *' % r
	try:    base=getattr(self.aq_parent, self.baseid)
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

	if not cookie:
	    # Just set cookie here, rather than redirect!
	    cookie=self.cookie
	    cookie_name=self.cookie_name
	    REQUEST['RESPONSE'].setCookie(cookie_name, cookie,
					 expires="Mon, 27-Dec-99 23:59:59 GMT",
					 path=REQUEST['SCRIPT_NAME']+cookie,)
	    REQUEST[cookie_name]=cookie


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

    def manage_supervisor(self): return self.__allow_groups__
    
    def parentObject(self):
	try:    return (self.aq_parent,)
	except: return ()


class Supervisor(UserFolder, Session):
    manage=manage_main=HTMLFile('DraftFolderSupervisor', globals())
    manage_options=()

    def __init__(self):
	UserFolder.__init__(self)
    
    
    

############################################################################## 
#
# $Log: DraftFolder.py,v $
# Revision 1.9  1998/01/02 17:41:19  brian
# Made undo available only in folders
#
# Revision 1.8  1997/12/31 19:27:10  jim
# *** empty log message ***
#
# Revision 1.7  1997/12/31 17:17:04  brian
# Security update
#
# Revision 1.6  1997/12/19 17:06:20  jim
# moved Sessions and Daft folders here.
#
# Revision 1.5  1997/12/18 16:45:40  jeffrey
# changeover to new ImageFile and HTMLFile handling
#
# Revision 1.4  1997/12/12 21:49:42  brian
# ui update
#
# Revision 1.3  1997/12/05 20:33:02  brian
# *** empty log message ***
#
# Revision 1.2  1997/11/11 21:25:28  brian
# Added copy/paste support, restricted unpickling, fixed DraftFolder bug
#
# Revision 1.1  1997/11/11 21:05:44  jim
# Draft Folders
#
#
