"""Access control package"""

__version__='$Revision: 1.52 $'[11:-2]

import Globals, App.Undo, socket, regex
from PersistentMapping import PersistentMapping
from Persistence import Persistent
from Globals import HTMLFile, MessageDialog
from string import join,strip,split,lower
from App.Management import Navigation, Tabs
from Acquisition import Implicit
from OFS.SimpleItem import Item
from base64 import decodestring
from ImageFile import ImageFile
from Role import RoleManager
from string import split, join

ListType=type([])




class User(Implicit, Persistent):

    # For backward compatibility
    domains=[]

    def __init__(self,name,password,roles,domains):
	self.name   =name
	self.roles  =roles
	self.__     =password
        self.domains=domains

    def authenticate(self, password, request):
        if self.domains:
            return (password==self.__) and \
                   domainSpecMatch(self.domains, request)
	return password==self.__

    def _shared_roles(self, parent):
        r=[]
        while 1:
            if hasattr(parent,'__roles__'):
                roles=parent.__roles__
                if roles is None: return 'Anonymous',
                if 'Shared' in roles:
                    roles=list(roles)
                    roles.remove('Shared')
                    r=r+roles
                else:
                    try: return r+list(roles)
                    except: return r
            if hasattr(parent, 'aq_parent'):
                while hasattr(parent.aq_self,'aq_self'):
                    parent=parent.aq_self
                parent=parent.aq_parent
            else: return r

    def allowed(self,parent,roles=None):
	usr_roles=self.roles

        if roles is None or 'Anonymous' in roles: return 1

	for role in roles:
	    if role in usr_roles:
                if (hasattr(self,'aq_parent') and
                    hasattr(self.aq_parent,'aq_parent')):
                    if (not hasattr(parent, 'aq_inContextOf') and
                        hasattr(parent, 'im_self')):
                        # This is a method, grab it's self.
                        parent=parent.im_self
                    if not parent.aq_inContextOf(self.aq_parent.aq_parent,1):
                        if 'Shared' in roles:
                            # Damn, old role setting. Waaa
                            roles=self._shared_roles(parent)
                            if 'Anonymous' in roles: return 1
                        return None
                return 1

        if 'Shared' in roles:
            # Damn, old role setting. Waaa
            roles=self._shared_roles(parent)
            if roles is None or 'Anonymous' in roles: return 1
            while 'Shared' in roles: roles.remove('Shared')
            return self.allowed(parent,roles)
            
	return None

    hasRole=allowed

    def has_role(self, roles):
	if type(roles)==type('s'):
	    roles=[roles]
	user_roles=self.roles
	for role in roles:
	    if role in user_roles:
		return 1
	return 0

    def __len__(self): return 1
    def __str__(self): return self.name
    __repr__=__str__

_remote_user_mode=0
try:
    f=open('%s/access' % SOFTWARE_HOME, 'r')
    data=split(strip(f.readline()),':')
    f.close()
    _remote_user_mode=not data[1]
    try:    ds=split(data[2], ' ')
    except: ds=[]
    super=User(data[0],data[1],('manage',), ds)
    del data
except:
    super=User('superuser','123',('manage',),[])
super.allowed=lambda parent, roles=None: 1
super.has_role=lambda roles=None: 1
super.hasRole=super.allowed

nobody=User('Anonymous User','',('Anonymous',), [])



class UserFolder(Implicit, Persistent, Navigation, Tabs, RoleManager,
		 Item, App.Undo.UndoSupport):
    """ """

    meta_type='User Folder'
    id       ='acl_users'
    title    ='User Folder'
    icon     ='p_/UserFolder'

    isPrincipiaFolderish=1
    isAUserFolder=1


    manage_options=(
    {'label':'Contents', 'action':'manage_main'},
    {'label':'Security', 'action':'manage_access'},
    {'label':'Undo',     'action':'manage_UndoForm'},
    )

    __ac_permissions__=(
    ('View management screens',
     ['manage_menu','manage_main','manage_copyright', 'manage_tabs',
      'manage_UndoForm']),
    ('Undo changes',       ['manage_undo_transactions']),
    ('Change permissions', ['manage_access']),
    ('Manage users',       ['manage_users']),
    )


    def __init__(self):
	self.data=PersistentMapping()

    def __len__(self):
	return len(self.data.keys())

    def _isTop(self):
        try: self=self.aq_parent
        except: return 1
        return self.isTopLevelPrincipiaApplicationObject
	
    def user_names(self):
	keys=self.data.keys()
	keys.sort()
	return keys

    def validate(self,request,auth='',roles=None):
	parent=request['PARENTS'][0]

	# If no authorization, only a user with a
        # domain spec and no passwd or nobody can
        # match
	if not auth:
            for ob in self.data.values():
                if ob.domains:
                    if ob.authenticate('', request):
                        if ob.allowed(parent, roles):
                            ob=ob.__of__(self)
                            return ob
            if self._isTop() and nobody.allowed(parent, roles):
                ob=nobody.__of__(self)
                return ob
            return None

	# Only do basic authentication
	if lower(auth[:6])!='basic ':
	    return None
	name,password=tuple(split(decodestring(split(auth)[-1]), ':'))

	# Check for superuser
	if self._isTop() and (name==super.name) and \
	super.authenticate(password, request):
	    return super

	# Try to get user
	try:    user=self.data[name]
	except: return None

	# Try to authenticate user
	if not user.authenticate(password, request):
	    return None

        # We need the user to be able to acquire!
        user=user.__of__(self)

	# Try to authorize user
	if user.allowed(parent, roles):
	    return user
	return None

    _mainUser=HTMLFile('mainUser', globals())
    _add_User=HTMLFile('addUser', globals(),
		       remote_user_mode__=_remote_user_mode)
    _editUser=HTMLFile('editUser', globals(),
		       remote_user_mode__=_remote_user_mode)

    manage=manage_main=_mainUser

    def _addUser(self,name,password,confirm,roles,domains,REQUEST=None):
        if not name:
            return MessageDialog(
		   title  ='Illegal value', 
                   message='A username must be specified',
                   action ='manage_main')
	if not password or not confirm:
            if not domains:
                return MessageDialog(
                   title  ='Illegal value', 
                   message='Password and confirmation must be specified',
                   action ='manage_main')
	if self.data.has_key(name) or (name==super.name):
            return MessageDialog(
		   title  ='Illegal value', 
                   message='A user with the specified name already exists',
                   action ='manage_main')
        if (password or confirm) and (password != confirm):
            return MessageDialog(
		   title  ='Illegal value', 
                   message='Password and confirmation do not match',
                   action ='manage_main')
        
	if not roles: roles=[]
        if not domains: domains=[]

        if domains and not domainSpecValidate(domains):
            return MessageDialog(
		   title  ='Illegal value', 
                   message='Illegal domain specification',
                   action ='manage_main')
            
        self.data[name]=User(name,password,roles,domains)
        
	if REQUEST: return self._mainUser(self, REQUEST)


    def _changeUser(self,name,password,confirm,roles,domains,REQUEST=None):
        if not name:
            return MessageDialog(
		   title  ='Illegal value', 
                   message='A username must be specified',
                   action ='manage_main')
	if not password or not confirm:
            if not domains:
                return MessageDialog(
                   title  ='Illegal value', 
                   message='Password and confirmation must be specified',
                   action ='manage_main')
	if not self.data.has_key(name):
            return MessageDialog(
		   title  ='Illegal value', 
                   message='Unknown user',
                   action ='manage_main')
        if (password or confirm) and (password != confirm):
            return MessageDialog(
		   title  ='Illegal value', 
                   message='Password and confirmation do not match',
                   action ='manage_main')

	if not roles: roles=[]
        if not domains: domains=[]

        if domains and not domainSpecValidate(domains):
            return MessageDialog(
		   title  ='Illegal value', 
                   message='Illegal domain specification',
                   action ='manage_main')
        
	user=self.data[name]
	user.__=password
	user.roles=roles
        user.domains=domains
        
	if REQUEST: return self._mainUser(self, REQUEST)

    def _delUsers(self,names,REQUEST=None):
	if not names:
            return MessageDialog(
		   title  ='Illegal value', 
                   message='No users specified',
                   action ='manage_main')

	if 0 in map(self.data.has_key, names):
            return MessageDialog(
		   title  ='Illegal value',
                   message='One or more items specified do not exist',
                   action ='manage_main')
	for name in names:
            del self.data[name]
        if REQUEST: return self._mainUser(self, REQUEST)

    def manage_users(self,submit=None,REQUEST=None,RESPONSE=None):
	""" """
	if submit=='Add...':
	    return self._add_User(self, REQUEST)

	if submit=='Edit':
	    try:    user=self.data[reqattr(REQUEST, 'name')]
	    except: return MessageDialog(
		    title  ='Illegal value',
                    message='The specified user does not exist',
                    action ='manage_main')
	    return self._editUser(self,REQUEST,user=user,password=user.__)

	if submit=='Add':
 	    name    =reqattr(REQUEST, 'name')
 	    password=reqattr(REQUEST, 'password')
 	    confirm =reqattr(REQUEST, 'confirm')
 	    roles   =reqattr(REQUEST, 'roles')
            domains =reqattr(REQUEST, 'domains')
	    return self._addUser(name,password,confirm,roles,domains,REQUEST)

	if submit=='Change':
 	    name    =reqattr(REQUEST, 'name')
 	    password=reqattr(REQUEST, 'password')
 	    confirm =reqattr(REQUEST, 'confirm')
 	    roles   =reqattr(REQUEST, 'roles')
            domains =reqattr(REQUEST, 'domains')
 	    return self._changeUser(name,password,confirm,roles,
                                    domains,REQUEST)

	if submit=='Delete':
	    names=reqattr(REQUEST, 'names')
	    return self._delUsers(names,REQUEST)

	return self._mainUser(self, REQUEST)


    # Copy/Paste support

    def _getCopy(self, container):
        obj=container
        if hasattr(obj, 'aq_base'): obj=obj.aq_base
	if hasattr(obj,'acl_users'):
	    raise ('Copy Error',
		   '<EM>This object already contains a UserFolder</EM>')
	return loads(dumps(self))

    def _postCopy(self, container):
	container.__allow_groups__=container.acl_users

    def _setId(self, clip_id):
	if clip_id != self.id:
	     raise ('Copy Error',
		    '<EM>Cannot change the id of a UserFolder</EM>')

if _remote_user_mode:

    class UserFolder(UserFolder):

	def validate(self,request,auth='',roles=None):
	    parent=request['PARENTS'][0]

	    e=request.environ
	    if e.has_key('REMOTE_USER'): name=e['REMOTE_USER']
	    else:
                for ob in self.data.values():
                    if ob.domains:
                        if ob.authenticate('', request):
                            if ob.allowed(parent, roles):
                                ob=ob.__of__(self)
                                return ob
                if self._isTop() and nobody.allowed(parent, roles):
                    ob=nobody.__of__(self)
                    return ob
                return None

	    # Check for superuser
	    if self._isTop() and (name==super.name):
		return super

	    # Try to get user
	    try:    user=self.data[name]
	    except: return None

            # We need the user to be able to acquire!
            user=user.__of__(self)

	    # Try to authorize user
	    if user.allowed(parent, roles):
		return user


def manage_addUserFolder(self,dtself=None,REQUEST=None,**ignored):
    """ """
    try:    self._setObject('acl_users', UserFolder())
    except: return MessageDialog(
                   title  ='Item Exists',
                   message='This object already contains a User Folder',
                   action ='%s/manage_main' % REQUEST['PARENT_URL'])
    self.__allow_groups__=self.acl_users
    if REQUEST: return self.manage_main(self,REQUEST,update_menu=1)





addr_match=regex.compile('[0-9\.\*]*').match
host_match=regex.compile('[A-Za-z0-9\.\*]*').match


def domainSpecValidate(spec):
    for ob in spec:
        sz=len(ob)
        if not ((addr_match(ob) == sz) or (host_match(ob) == sz)):
            return 0
    return 1


def domainSpecMatch(spec, request):

    if request.has_key('REMOTE_HOST'):
        host=request['REMOTE_HOST']
    else: host=''

    if request.has_key('REMOTE_ADDR'):
        addr=request['REMOTE_ADDR']
    else: addr=''

    if not host and not addr:
        return 0

    if not host:
        host=socket.gethostbyaddr(addr)[0]
    if not addr:
        addr=socket.gethostbyname(host)

    _host=split(host, '.')
    _addr=split(addr, '.')
    _hlen=len(_host)
    _alen=len(_addr)
    
    for ob in spec:
        sz=len(ob)
        _ob=split(ob, '.')
        _sz=len(_ob)

        if addr_match(ob)==sz:
            if _sz != _alen:
                continue
            fail=0
            for i in range(_sz):
                a=_addr[i]
                o=_ob[i]
                if (o != a) and (o != '*'):
                    fail=1
                    break
            if fail:
                continue
            return 1

        if host_match(ob)==sz:
            if _hlen < _sz:
                continue
            elif _hlen > _sz:
                _item=_host[-_sz:]
            else:
                _item=_host
            fail=0
            for i in range(_sz):
                h=_item[i]
                o=_ob[i]
                if (o != h) and (o != '*'):
                    fail=1
                    break
            if fail:
                continue
            return 1
    return 0


def absattr(attr):
    if callable(attr): return attr()
    return attr

def reqattr(request, attr):
    try:    return request[attr]
    except: return None
