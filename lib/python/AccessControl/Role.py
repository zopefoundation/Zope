"""Access control support"""

__version__='$Revision: 1.12 $'[11:-2]


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
   
    __ac_types__=(('Full Access', map(lambda x: x[0], __ac_permissions__)),
		 )

    __ac_roles__=('Manager', 'Anonymous', 'Shared')

    def access_info(self):
	# Return access summary info
	data={}
	for t in self.access_types():
	    name=t.name
	    for role in t.getRoles():
		data[role]=name
	keys=data.keys()
	for i in range(len(keys)):
	    key=keys[i]
	    keys[i]={'name': key, 'value': data[key]}
	return keys

    def access_defaults(self):
	data=[]
	for p in self.access_permissions():
	    if not p.getRoles():
		data.append(p)
	return data

    def access_types(self):
	# Return list of access type objects
	list=[]
	for name,value in self.__ac_types__:
	    list.append(AccessType(name,value,self))
	return list

    def access_types_dict(self):
	# Return dict of access type objects
	dict={}
	for name,value in self.__ac_types__:
	    dict[name]=AccessType(name,value,self)
	return dict

    def access_types_gc(self, dict):
	# Remove unused types of access
	static=map(lambda x: x[0], self.__class__.__ac_types__)

	data=list(self.__ac_types__)
	flag=0
	for name, type in dict.items():
	    roles=type.getRoles()
	    if not roles and name not in static:
		try:
		    data.remove((name, type.data))
		    flag=1
		except:
		    pass
	if flag: self.__ac_types__=tuple(data)

    def access_type_for(self, role):
	for type in self.access_types():
	    if role in type.getRoles():
		return type
	return None

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
    _listAccess=HTMLFile('listAccess', globals())
    _editAccess=HTMLFile('editAccess', globals())
    _specAccess=HTMLFile('specAccess', globals())
    _add_Access=HTMLFile('addAccess', globals())

    def manage_access(self,SUBMIT=None,REQUEST=None):
	""" """
	if SUBMIT=='Add...':
	    return self._add_Access(self, REQUEST)

	if SUBMIT=='Edit':
	    return self._editAccess(self, REQUEST)

	if SUBMIT=='Add':
	    roles =reqattr(REQUEST, 'roles')
	    access=reqattr(REQUEST, 'access')
	    return self._addAccess(roles, access, REQUEST)

	if SUBMIT=='List':
	    return self._listAccess(self, REQUEST)

	if SUBMIT=='Change':
	    role  =reqattr(REQUEST, 'role')
	    access=reqattr(REQUEST, 'access')
	    return self._changeAccess(role, access, REQUEST)

	if SUBMIT=='Remove':
	    roles=reqattr(REQUEST, 'roles')
	    return self._delAccess(roles, REQUEST)

	if SUBMIT=='OK':
	    permissions=reqattr(REQUEST, 'permissions')
	    access=reqattr(REQUEST, 'access')
	    roles =reqattr(REQUEST, 'roles')
	    return self._specialAccess(roles,access,permissions,REQUEST)

	if SUBMIT=='Add Role':
	    role=reqattr(REQUEST, 'role')
	    return self._addRole(role, REQUEST)

	if SUBMIT=='Delete Role':
	    roles=reqattr(REQUEST, 'roles')
	    return self._delRoles(roles, REQUEST)

	return self._mainAccess(self,REQUEST)

    def _addAccess(self, roles, access, REQUEST):
	if not roles or not access:
	    return MessageDialog(
		   title  ='Incomplete',
		   message='You must specify roles and a type of access',
		   action ='manage_access')
	if not self.validate_roles(roles):
	    return MessageDialog(
		   title  ='Undefined Role',
		   message='An undefined role was specified',
		   action ='manage_access')
	if access=='Special Access...':
	    return self._specAccess(self, REQUEST)
	types=self.access_types_dict()
	for type in types.values():
	    type.delRoles(roles)
	types[access].setRoles(roles)
	return self._mainAccess(self, REQUEST)

    def _changeAccess(self, role, access, REQUEST=None):
	if not access or not role:
	    return MessageDialog(
		   title  ='Incomplete',
		   message='You must specify a type of access',
		   action ='manage_access')
	if not self.validate_roles([role,]):
	    return MessageDialog(
		   title  ='Undefined Role',
		   message='An undefined role was specified',
		   action ='manage_access')
	if access=='Special Access...':
	    REQUEST['roles']=[role,]
	    return self._specAccess(self, REQUEST)
	types=self.access_types_dict()
	for type in types.values():
	    type.delRoles([role,])
	types[access].setRoles([role,])
	self.access_types_gc(types)
	return self._mainAccess(self, REQUEST)

    def _specialAccess(self, roles, access, permissions, REQUEST=None):
	if not roles or not access:
	    return MessageDialog(
		   title  ='Incomplete',
		   message='You must specify roles and a type of access',
		   action ='manage_access')
	if not self.validate_roles(roles):
	    return MessageDialog(
		   title  ='Undefined Role',
		   message='An undefined role was specified',
		   action ='manage_access')

	if not permissions: permissions=[]

	dict=self.access_permissions_dict()
	if 0 in map(dict.has_key, permissions):
	    return MessageDialog(
		   title  ='Unknown permission',
		   message='An unknown permission was specified',
		   action ='manage_changeAccess')
	dict=self.access_types_dict()
	if dict.has_key(access):
	    return MessageDialog(
		   title  ='Name in use',
		   message='The name specified is already in use',
		   action ='manage_access')

	# Check for duplicate access types
	permissions.sort()
	for key, value in dict.items():
	    names=value.data[:]
	    names.sort()
	    if permissions==names:
		return MessageDialog(
		       title  ='Already defined',
		       message='Another access type (%s) is already defined '\
		               'with the selected permissions' % key,
		       action ='manage_access')

	self.__ac_types__=self.__ac_types__+((access,permissions),)
	types=self.access_types_dict()
	for type in types.values():
	    type.delRoles(roles)
	types[access].setRoles(roles)
	return self._mainAccess(self, REQUEST)

    def _delAccess(self, roles, REQUEST=None):
	if not roles:
	    return MessageDialog(
		   title  ='Incomplete',
		   message='You must specify roles to remove',
		   action ='manage_access')
	types=self.access_types_dict()
	for type in types.values():
	    type.delRoles(roles)
	self.access_types_gc(types)
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
	return []

    def setRoles(self, roles):
	# Add the given list of role names to the appropriate
	# subobjects for this permission. To do this, we add
	# the given roles to the __roles__ of each attribute
	# that this permission represents.
	for name in self.data:
	    if name=='': attr=self.obj
	    else: attr=getattr(self.obj, name)
	    if hasattr(attr,'aq_self'):
		attr=attr.aq_self
	    if hasattr(attr, '__roles__'):
		data=attr.__roles__
	    else: data=[]
	    if data is None:
		data=[]
	    data=list(data)
	    for role in roles:
		data.append(role)
	    attr.__roles__=data

    def delRoles(self, roles):
	# Remove the given list of role names from the appropriate
	# subobjects for this permission. To do this, we remove
	# the given roles from the __roles__ of each attribute
	# that this permission represents. If the __roles__ of any
	# attribute is thus left empty, it is deleted.
	for name in self.data:
	    if name=='': attr=self.obj
	    else: attr=getattr(self.obj, name)
	    if hasattr(attr,'aq_self'):
		attr=attr.aq_self
	    if not hasattr(attr, '__roles__'):
		return
	    data=attr.__roles__
	    if data is None: data=[]
	    data=list(data)
	    for role in roles:
		if role in data:
		    data.remove(role)
	    if data: attr.__roles__=data
	    else:
		# The hasattr above will find __roles__ defined
		# in the class, but we wont be able to delete it.
		try:    del attr.__roles__
		except: pass

    def __len__(self): return 1
    def __str__(self): return self.name



class AccessType:
    # An AccessType is a named subset of 0 or more of the
    # permissions defined by an object. AccessTypes may
    # have overlapping permissions, but two AccessTypes
    # cannot map to the exact same subset of permissions.

    def __init__(self,name,data,obj):
	self.name=name
	self.data=data
	if hasattr(obj, 'aq_self'):
	    obj=obj.aq_self
	self.obj=obj

    def getRoles(self):
	# Return the list of role names which have been given
	# this type of access for the object in question. To
	# determine this, we iterate through the permissions
	# that this access type represents, asking each for 
	# the list of roles which have that permission.
	# Role names which appear in all of the lists returned
	# by our set of permissions *and* in no other lists
	# are returned.
        dict ={}
	names=[]
	lists=[]
	roles=[]
	value=[]
	for p in self.obj.access_permissions():
	    dict[p.name]=p.getRoles()
	for p in self.data:
	    for role in dict[p]:
		if role not in names:
		    names.append(role)
	    lists.append(dict[p])
	for name in names:
	    for list in lists:
		if name not in list:
		    name=None
		    break
	    if name: roles.append(name)
	lists=[]
	for p in dict.keys():
	    if p not in self.data:
		lists.append(dict[p])
	for role in roles:
	    for list in lists:
		if role in list:
		    role=None
		    break
	    if role: value.append(role)
	return value

    def setRoles(self, roles):
	# Add the given list of role names to the appropriate 
	# subobjects for this type of access. To do this, we
	# just call the setRoles method for each permission
	# in the list of permissions represented by this type
	# of access.
	permissions={}
	for p in self.obj.access_permissions():
	    permissions[p.name]=p
	for p in self.data:
	    permissions[p].setRoles(roles)

    def delRoles(self, roles):
	# Remove the given list of role names from the appropriate
	# subobjects for this type of access. To do this, we call
	# the delRoles method for each permission in the list of
	# permissions represented by this type of access.
	permissions={}
	for p in self.obj.access_permissions():
	    permissions[p.name]=p
	for p in self.data:
	    permissions[p].delRoles(roles)

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



#     Folder
#     __ac_permissions__=(
#     ('View Management Screens',
#      ['manage','manage_menu','manage_main','manage_copyright',
#       'manage_tabs','manage_propertiesForm','manage_UndoForm']),
#     ('Undo Changes',       ['manage_undo_transactions']),
#     ('Change Permissions', ['manage_access']),
#     ('Add Objects',        ['manage_addObject']),
#     ('Delete Objects',     ['manage_delObjects']),
#     ('Add Properties',     ['manage_addProperty']),
#     ('Change Properties',  ['manage_editProperties']),
#     ('Delete Properties',  ['manage_delProperties']),
#     )
   
#     __ac_types__=(('Full Access', map(lambda x: x[0], __ac_permissions__)),
# 		 )
#     __ac_roles__=('Manager', 'Anonymous'
# 		 )



#     Document
#     __ac_permissions__=(
#     ('View Management Screens', ['manage','manage_tabs','manage_uploadForm']),
#     ('Change Permissions', ['manage_access']),
#     ('Change/Upload Data', ['manage_edit','manage_upload','PUT']),
#     ('View', ['',]),
#     )
   
#     __ac_types__=(('Full Access', map(lambda x: x[0], __ac_permissions__)),
# 		  ('View Access', ['View',]),
# 		 )

#     __ac_roles__=('Manager', 'Anonymous')
