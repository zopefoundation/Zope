"""Access control support"""

__version__='$Revision: 1.18 $'[11:-2]


from Globals import HTMLFile, MessageDialog
from string import join, strip, split, find
from Acquisition import Implicit
import Globals
from Permission import Permission

ListType=type([])

class RoleManager:

    __ac_permissions__=(('View management screens', []),
			('Change permissions', []),
			('Add objects', []),
			('Delete objects', []),
			('Add properties', []),
			('Change properties', []),
			('Delete properties', []),
		       )
   
    __ac_roles__=('Manager', 'Anonymous')

    #------------------------------------------------------------

    def permission_settings(self):
	result=[]
	valid=self.valid_roles()
	indexes=range(len(valid))
	ip=0
	for p in self.__ac_permissions__:
	    name, value = p[:2]
	    p=Permission(name,value,self)
	    roles=p.getRoles()
	    d={'name': name,
	       'acquire': type(roles) is ListType and 'CHECKED' or '',
	       'roles': map(
		   lambda ir, roles=roles, valid=valid, ip=ip:
		   {
		       'name': "p%dr%d" % (ip,ir),
		       'checked': (valid[ir] in roles) and 'CHECKED' or '',
		       },
		   indexes)
	       }
	    ip=ip+1
	    result.append(d)

	return result

    manage_roleForm=HTMLFile('roleEdit', globals())
    def manage_role(self, role_to_manage, permissions=[], REQUEST=None):
	"Change the permissions given to the given role"
	for p in self.__ac_permissions__:
	    name, value = p[:2]
	    p=Permission(name,value,self)
	    p.setRole(role_to_manage, name in permissions)

	if REQUEST is not None: return self.manage_access(self,REQUEST)

    manage_permissionForm=HTMLFile('permissionEdit', globals())
    def manage_permission(self, permission_to_manage,
			  roles=[], acquire=0, REQUEST=None):
        "Change the settings for the given permission"
	for p in self.__ac_permissions__:
	    name, value = p[:2]
	    if name==permission_to_manage:
		p=Permission(name,value,self)
		if acquire: roles=list(roles)
		else: roles=tuple(roles)
		p.setRoles(roles)
		if REQUEST is not None: return self.manage_access(self,REQUEST)
		return

	raise 'Invalid Permission', (
	    "The permission <em>%s</em> is invalid." % permission_to_manage)
	
    manage_access=HTMLFile('access', globals())
    def manage_changePermissions(self, REQUEST):
	" "
	valid_roles=self.valid_roles()
	indexes=range(len(valid_roles))
	have=REQUEST.has_key
	permissions=self.__ac_permissions__
	for ip in range(len(permissions)):
	    roles=[]
	    for ir in indexes:
		if have("p%dr%d" % (ip,ir)): roles.append(valid_roles[ir])
	    name, value = permissions[ip][:2]
	    p=Permission(name,value,self)
	    if not have('a%d' % ip): roles=tuple(roles)
	    p.setRoles(roles)

	return MessageDialog(
	    title  ='Success!',
	    message='Your changes have been saved',
	    action ='manage_access')


    def permissionsOfRole(self, role):
	r=[]
	for p in self.__ac_permissions__:
	    name, value = p[:2]
	    p=Permission(name,value,self)
	    roles=p.getRoles()
	    r.append({'name': name,
		      'selected': role in roles and 'SELECTED' or '',
		      })
	return r

    def rolesOfPermission(self, permission):
	valid_roles=self.valid_roles()
	for p in self.__ac_permissions__:
	    name, value = p[:2]
	    if name==permission:
		p=Permission(name,value,self)
		roles=p.getRoles()
		return map(
		    lambda role, roles=roles:
		    {'name': role,
		     'selected': role in roles and 'SELECTED' or '',
		     },
		    valid_roles)
	
	raise 'Invalid Permission', (
	    "The permission <em>%s</em> is invalid." % permission)

    def acquiredRolesAreUsedBy(self, permission):
	for p in self.__ac_permissions__:
	    name, value = p[:2]
	    if name==permission:
		p=Permission(name,value,self)
		roles=p.getRoles()
		return type(roles) is ListType and 'CHECKED' or ''
	
	raise 'Invalid Permission', (
	    "The permission <em>%s</em> is invalid." % permission)


    #------------------------------------------------------------

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


    def manage_defined_roles(self,submit=None,REQUEST=None):
	""" """

	if submit=='Add Role':
	    role=reqattr(REQUEST, 'role')
	    return self._addRole(role, REQUEST)

	if submit=='Delete Role':
	    roles=reqattr(REQUEST, 'roles')
	    return self._delRoles(roles, REQUEST)

	return self.manage_access(self,REQUEST)

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
	return self.manage_access(self, REQUEST)

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
	return self.manage_access(self, REQUEST)


    # Compatibility names only!!

    smallRolesWidget=selectedRoles=aclAChecked=aclPChecked=aclEChecked=''
    validRoles=valid_roles
    #manage_rolesForm=manage_access

    def manage_editRoles(self,REQUEST,acl_type='A',acl_roles=[]):
	pass

    def _setRoles(self,acl_type,acl_roles):
	pass

Globals.default__class_init__(RoleManager)


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
