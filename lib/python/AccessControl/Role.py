"""Access control support"""

__version__='$Revision: 1.16 $'[11:-2]


from Globals import HTMLFile, MessageDialog
from string import join, strip, split, find
from Acquisition import Implicit
import Globals

class RoleManager:

    __ac_permissions__=(('View management screens', []),
			('Change permissions', []),
			('Add objects', []),
			('Delete objects', []),
			('Add properties', []),
			('Change properties', []),
			('Delete properties', []),
			('Shared permission',['']),
		       )
   
    __ac_roles__=('Manager', 'Anonymous', 'Shared')

    def access_permissions(self):
	# Return list of permission objects
	list=[]
	for name,value in self.__ac_permissions__:
	    list.append(Permission(name,value,self))
	return list

    def access_permissions_dict(self):
	# Return dict of access permission objects
	dict={}
	for name,value in self.__ac_permissions__:
	    dict[name]=Permission(name,value,self)
	return dict

    def access_debug_info(self):
	# Return debug info
	clas=class_attrs(self)
	inst=instance_attrs(self)
	data=[]
	_add=data.append
	for key, value in inst.items():
	    if find(key,'__roles__') >= 0:
		_add({'name': key, 'value': value, 'class': 0})
	    if hasattr(value, '__roles__'):
		_add({'name': '%s.__roles__' % key, 'value': value.__roles__, 
		      'class': 0})
	for key, value in clas.items():
	    if find(key,'__roles__') >= 0:
		_add({'name': key, 'value': value, 'class' : 1})
	    if hasattr(value, '__roles__'):
		_add({'name': '%s.__roles__' % key, 'value': value.__roles__, 
		      'class': 1})
	return data

    def valid_roles(self):
	# Return list of valid roles
        obj=self
	dict={}
	dup =dict.has_key
        x=0
        while x < 100:
	    try:    roles=obj.__ac_roles__
	    except: roles=()
	    for role in roles:
		if not dup(role):
		    dict[role]=1
	    try:    obj=obj.aq_parent
	    except: break
	    x=x+1
	roles=dict.keys()
	roles.sort()
	return roles

    def validate_roles(self, roles):
	# Return true if all given roles are valid
	valid=self.valid_roles()
	for role in roles:
	    if role not in valid:
		return 0
	return 1

    def userdefined_roles(self):
	# Return list of user-defined roles
	roles=list(self.__ac_roles__)
	for role in classattr(self.__class__,'__ac_roles__'):
	    try:    roles.remove(role)
	    except: pass
	return roles

    _mainAccess=HTMLFile('mainAccess', globals())
    _editAccess=HTMLFile('editAccess', globals())
    _add_Access=HTMLFile('addAccess', globals())
    _del_Access=HTMLFile('delAccess', globals())

    def manage_access(self,submit=None,REQUEST=None):
	""" """
	if submit=='Add...':
	    return self._add_Access(self, REQUEST)

	if submit=='Edit':
	    return self._editAccess(self, REQUEST)

	if submit=='Add':
	    roles =reqattr(REQUEST, 'roles')
	    permissions=reqattr(REQUEST, 'permissions')
	    return self._addAccess(roles, permissions, REQUEST)

	if submit=='Change':
	    role  =reqattr(REQUEST, 'role')
	    permissions=reqattr(REQUEST, 'permissions')
	    return self._changeAccess(role, permissions, REQUEST)

	if submit=='Remove...':
	    return self._del_Access(self, REQUEST)

	if submit=='Remove':
	    roles=reqattr(REQUEST, 'roles')
	    return self._delAccess(roles, REQUEST)

	if submit=='Add Role':
	    role=reqattr(REQUEST, 'role')
	    return self._addRole(role, REQUEST)

	if submit=='Delete Role':
	    roles=reqattr(REQUEST, 'roles')
	    return self._delRoles(roles, REQUEST)

	return self._mainAccess(self,REQUEST)

    def _addAccess(self, roles, permissions, REQUEST):
	if not roles or not permissions:
	    return MessageDialog(
		   title  ='Incomplete',
		   message='You must specify roles and permissions',
		   action ='manage_access')
	if not self.validate_roles(roles):
	    return MessageDialog(
		   title  ='Undefined Role',
		   message='An undefined role was specified',
		   action ='manage_access')
	dict=self.access_permissions_dict()
	if 0 in map(dict.has_key, permissions):
	    return MessageDialog(
		   title  ='Unknown permission',
		   message='An unknown permission was specified',
		   action ='manage_changeAccess')
	for p in dict.values():
	    p.delRoles(roles)
	for p in permissions:
	    dict[p].setRoles(roles)
	return self._mainAccess(self, REQUEST)

    def _changeAccess(self, role, permissions, REQUEST=None):
	if not role or not permissions:
	    return MessageDialog(
		   title  ='Incomplete',
		   message='You must specify roles and permissions',
		   action ='manage_access')
	if not self.validate_roles([role]):
	    return MessageDialog(
		   title  ='Undefined Role',
		   message='An undefined role was specified',
		   action ='manage_access')
	dict=self.access_permissions_dict()
	if 0 in map(dict.has_key, permissions):
	    return MessageDialog(
		   title  ='Unknown permission',
		   message='An unknown permission was specified',
		   action ='manage_changeAccess')
	for p in dict.values():
	    p.delRoles([role])
	for p in permissions:
	    dict[p].setRoles([role])
	return self._mainAccess(self, REQUEST)

    def _delAccess(self, roles, REQUEST=None):
	if not roles:
	    return MessageDialog(
		   title  ='Incomplete',
		   message='You must specify roles to remove',
		   action ='manage_access')
	dict=self.access_permissions_dict()
	for p in dict.values():
	    p.delRoles(roles)
	return self._mainAccess(self, REQUEST)

    def _addRole(self, role, REQUEST=None):
	if not role:
	    return MessageDialog(
		   title  ='Incomplete',
		   message='You must specify a role name',
		   action ='manage_changeAccess')
	if role in self.__ac_roles__:
	    return MessageDialog(
		   title  ='Role Exists',
		   message='The given role is already defined',
		   action ='manage_changeAccess')
	data=list(self.__ac_roles__)
	data.append(role)
	self.__ac_roles__=tuple(data)
	return self._mainAccess(self, REQUEST)

    def _delRoles(self, roles, REQUEST):
	if not roles:
	    return MessageDialog(
		   title  ='Incomplete',
		   message='You must specify a role name',
		   action ='manage_changeAccess')
	data=list(self.__ac_roles__)
	for role in roles:
	    try:    data.remove(role)
	    except: pass
	self.__ac_roles__=tuple(data)
	return self._mainAccess(self, REQUEST)


    # Compatibility names only!!

    smallRolesWidget=selectedRoles=aclAChecked=aclPChecked=aclEChecked=''
    validRoles=valid_roles
    manage_rolesForm=manage_access

    def manage_editRoles(self,REQUEST,acl_type='A',acl_roles=[]):
	pass

    def _setRoles(self,acl_type,acl_roles):
	pass

Globals.default__class_init__(RoleManager)



ListType=type([])

class Permission:
    # A Permission maps a named logical permission to a set
    # of attribute names. Attribute names which appear in a
    # permission may not appear in any other permission defined
    # by the object.

    def __init__(self,name,data,obj):
	self.name=name
	self.data=data
	if hasattr(obj, 'aq_self'):
	    obj=obj.aq_self
	self.obj =obj

    def getRoles(self):
	# Return the list of role names which have been given
	# this permission for the object in question. To do
	# this, we try to get __roles__ from all of the object
	# attributes that this permission represents.
	name=self.data[0]
	if name=='': attr=self.obj
	else: attr=getattr(self.obj, name)
	if hasattr(attr,'aq_self'): attr=attr.aq_self
	if hasattr(attr, '__roles__'):
	    roles=attr.__roles__
	    if roles is None:
		return ['Manager','Anonymous']
	    return roles
	#return []
	return ['Shared']

    def setRoles(self, roles):
	# Add the given list of role names to the appropriate
	# subobjects for this permission. To do this, we add
	# the given roles to the __roles__ of each attribute
	# that this permission represents.
	first=1
	data=None
	for name in self.data:
	    if name=='': attr=self.obj
	    else: attr=getattr(self.obj, name)
	    if hasattr(attr,'aq_self'):
		attr=attr.aq_self

	    if first:
		if hasattr(attr, '__roles__'):
		    data=attr.__roles__
		    if data is None: data=[]
		    else: data=list(data)
		else: data=[]
		for role in roles: data.append(role)
		first=0

	    attr.__roles__=data

    def delRoles(self, roles):
	# Remove the given list of role names from the appropriate
	# subobjects for this permission. To do this, we remove
	# the given roles from the __roles__ of each attribute
	# that this permission represents. If the __roles__ of any
	# attribute is thus left empty, it is deleted.
	first=1
	data=None
	for name in self.data:
	    if name=='': attr=self.obj
	    else: attr=getattr(self.obj, name)
	    if hasattr(attr,'aq_self'):
		attr=attr.aq_self

	    if first:
		if hasattr(attr, '__roles__'):
		    data=attr.__roles__
		    if data is None: data=[]
		    else: data=list(data)
		else: data=['Shared']
		for role in roles:
		    if role in data: data.remove(role)
		first=0

	    attr.__roles__=data
		
    def __len__(self): return 1
    def __str__(self): return self.name





def absattr(attr):
    if callable(attr): return attr()
    return attr

def reqattr(request, attr):
    try:    return request[attr]
    except: return None

def classattr(cls, attr):
    if hasattr(cls, attr):
	return getattr(cls, attr)
    try:    bases=cls.__bases__
    except: bases=()
    for base in bases:
	if classattr(base, attr):
	    return attr
    return None

def instance_dict(inst):
    try:    return inst.__dict__
    except: return {}

def class_dict(_class):
    try:    return _class.__dict__
    except: return {}

def instance_attrs(inst):
    return instance_dict(inst)

def class_attrs(inst, _class=None, data=None):
    if _class is None:
	_class=inst.__class__
	data={}

    clas_dict=class_dict(_class)
    inst_dict=instance_dict(inst)
    inst_attr=inst_dict.has_key
    for key, value in clas_dict.items():
	if not inst_attr(key):
	    data[key]=value
    for base in _class.__bases__:
	data=class_attrs(inst, base, data)
    return data
