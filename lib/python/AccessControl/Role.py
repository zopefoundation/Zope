##############################################################################
#
# Copyright (c) 2001 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
"""Access control support

$Id$
"""
from cgi import escape

from Globals import DTMLFile, MessageDialog, Dictionary
from Acquisition import Implicit, Acquired, aq_get
import Globals, ExtensionClass, PermissionMapping, Products
from App.Common import aq_base

from Permission import Permission
from requestmethod import postonly


DEFAULTMAXLISTUSERS=250

def _isBeingUsedAsAMethod(self):
    return aq_get(self, '_isBeingUsedAsAMethod_', 0)

def _isNotBeingUsedAsAMethod(self):
    return not aq_get(self, '_isBeingUsedAsAMethod_', 0)


class RoleManager(ExtensionClass.Base, PermissionMapping.RoleManager):

    """An object that has configurable permissions"""

    __ac_permissions__=(
        ('Change permissions',
         ('manage_access', 'permission_settings',
          'ac_inherited_permissions',
          'manage_roleForm', 'manage_role',
          'manage_acquiredForm', 'manage_acquiredPermissions',
          'manage_permissionForm', 'manage_permission',
          'manage_changePermissions', 'permissionsOfRole',
          'rolesOfPermission', 'acquiredRolesAreUsedBy',
          'manage_defined_roles', 'userdefined_roles',
          'manage_listLocalRoles', 'manage_editLocalRoles',
          'manage_setLocalRoles', 'manage_addLocalRoles',
          'manage_delLocalRoles'
          )),
        )

    manage_options=(
        {'label':'Security', 'action':'manage_access',
         'help':('OFSP','Security.stx'),
         'filter': _isNotBeingUsedAsAMethod,
         },
        {'label':'Define Permissions', 'action':'manage_access',
         'help':('OFSP','Security_Define-Permissions.stx'),
         'filter': _isBeingUsedAsAMethod,
         },
        )

    __ac_roles__=('Manager', 'Owner', 'Anonymous', 'Authenticated')

    permissionMappingPossibleValues=Acquired

    #------------------------------------------------------------

    def ac_inherited_permissions(self, all=0):
        # Get all permissions not defined in ourself that are inherited
        # This will be a sequence of tuples with a name as the first item and
        # an empty tuple as the second.
        d={}
        perms=self.__ac_permissions__
        for p in perms: d[p[0]]=None

        r=gather_permissions(self.__class__, [], d)
        if all:
            if hasattr(self, '_subobject_permissions'):
                for p in self._subobject_permissions():
                    pname=p[0]
                    if not d.has_key(pname):
                        d[pname]=1
                        r.append(p)

            r=list(perms)+r
            r.sort()

        return tuple(r)

    def permission_settings(self, permission=None):
        """Return user-role permission settings.

        If 'permission' is passed to the method then only the settings for
        'permission' is returned.
        """
        result=[]
        valid=self.valid_roles()
        indexes=range(len(valid))
        ip=0

        permissions = self.ac_inherited_permissions(1)
        # Filter permissions
        if permission:
            permissions = [p for p in permissions if p[0] == permission]

        for p in permissions:
            name, value = p[:2]
            p=Permission(name,value,self)
            roles=p.getRoles(default=[])
            d={'name': name,
               'acquire': isinstance(roles, list) and 'CHECKED' or '',
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

    manage_roleForm=DTMLFile('dtml/roleEdit', globals(),
                             management_view='Security',
                             help_topic='Security_Manage-Role.stx',
                             help_product='OFSP')

    def manage_role(self, role_to_manage, permissions=[], REQUEST=None):
        """Change the permissions given to the given role.
        """
        self._isBeingUsedAsAMethod(REQUEST, 0)
        for p in self.ac_inherited_permissions(1):
            name, value = p[:2]
            p=Permission(name,value,self)
            p.setRole(role_to_manage, name in permissions)

        if REQUEST is not None: return self.manage_access(REQUEST)
    manage_role = postonly(manage_role)

    manage_acquiredForm=DTMLFile('dtml/acquiredEdit', globals(),
                                 management_view='Security',
                                 help_topic='Security_Manage-Acquisition.stx',
                                 help_product='OFSP')

    def manage_acquiredPermissions(self, permissions=[], REQUEST=None):
        """Change the permissions that acquire.
        """
        self._isBeingUsedAsAMethod(REQUEST, 0)
        for p in self.ac_inherited_permissions(1):
            name, value = p[:2]
            p=Permission(name,value,self)
            roles=p.getRoles()
            if roles is None: continue
            if name in permissions: p.setRoles(list(roles))
            else:                   p.setRoles(tuple(roles))

        if REQUEST is not None: return self.manage_access(REQUEST)
    manage_acquiredPermissions = postonly(manage_acquiredPermissions)

    manage_permissionForm=DTMLFile('dtml/permissionEdit', globals(),
                                   management_view='Security',
                                   help_topic='Security_Manage-Permission.stx',
                                   help_product='OFSP')

    def manage_permission(self, permission_to_manage,
                          roles=[], acquire=0, REQUEST=None):
        """Change the settings for the given permission.

        If optional arg acquire is true, then the roles for the permission
        are acquired, in addition to the ones specified, otherwise the
        permissions are restricted to only the designated roles.
        """
        self._isBeingUsedAsAMethod(REQUEST, 0)
        for p in self.ac_inherited_permissions(1):
            name, value = p[:2]
            if name==permission_to_manage:
                p=Permission(name,value,self)
                if acquire: roles=list(roles)
                else: roles=tuple(roles)
                p.setRoles(roles)
                if REQUEST is not None: return self.manage_access(REQUEST)
                return

        raise ValueError, (
            "The permission <em>%s</em> is invalid." %
                escape(permission_to_manage))
    manage_permission = postonly(manage_permission)

    _normal_manage_access=DTMLFile('dtml/access', globals())

    _method_manage_access=DTMLFile('dtml/methodAccess', globals())

    def manage_access(self, REQUEST, **kw):
        """Return an interface for making permissions settings.
        """
        if hasattr(self, '_isBeingUsedAsAMethod') and \
           self._isBeingUsedAsAMethod():
            return apply(self._method_manage_access,(), kw)
        else:
            return apply(self._normal_manage_access,(), kw)

    def manage_changePermissions(self, REQUEST):
        """Change all permissions settings, called by management screen.
        """
        self._isBeingUsedAsAMethod(REQUEST, 0)
        valid_roles=self.valid_roles()
        indexes=range(len(valid_roles))
        have=REQUEST.has_key
        permissions=self.ac_inherited_permissions(1)
        fails = []
        for ip in range(len(permissions)):
            roles=[]
            for ir in indexes:
                if have("p%dr%d" % (ip,ir)): roles.append(valid_roles[ir])
            name, value = permissions[ip][:2]
            try:
                p=Permission(name,value,self)
                if not have('a%d' % ip): roles=tuple(roles)
                p.setRoles(roles)
            except:
                fails.append(name)

        if fails:
            return MessageDialog(title="Warning!",
                                 message="Some permissions had errors: "
                                   + escape(', '.join(fails)),
                                 action='manage_access')
        return MessageDialog(
            title  ='Success!',
            message='Your changes have been saved',
            action ='manage_access')
    manage_changePermissions = postonly(manage_changePermissions)

    def permissionsOfRole(self, role):
        """Used by management screen.
        """
        r=[]
        for p in self.ac_inherited_permissions(1):
            name, value = p[:2]
            p=Permission(name,value,self)
            roles=p.getRoles()
            r.append({'name': name,
                      'selected': role in roles and 'SELECTED' or '',
                      })
        return r

    def rolesOfPermission(self, permission):
        """Used by management screen.
        """
        valid_roles=self.valid_roles()
        for p in self.ac_inherited_permissions(1):
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

        raise ValueError, (
            "The permission <em>%s</em> is invalid." % escape(permission))

    def acquiredRolesAreUsedBy(self, permission):
        """Used by management screen.
        """
        for p in self.ac_inherited_permissions(1):
            name, value = p[:2]
            if name==permission:
                p=Permission(name,value,self)
                roles=p.getRoles()
                return isinstance(roles, list) and 'CHECKED' or ''

        raise ValueError, (
            "The permission <em>%s</em> is invalid." % escape(permission))


    # Local roles support
    # -------------------
    #
    # Local roles allow a user to be given extra roles in the context
    # of a particular object (and its children). When a user is given
    # extra roles in a particular object, an entry for that user is made
    # in the __ac_local_roles__ dict containing the extra roles.

    __ac_local_roles__=None

    manage_listLocalRoles=DTMLFile('dtml/listLocalRoles', globals(),
                                   management_view='Security',
                                   help_topic='Security_Local-Roles.stx',
                                   help_product='OFSP')

    manage_editLocalRoles=DTMLFile('dtml/editLocalRoles', globals(),
                                   management_view='Security',
                                   help_topic='Security_User-Local-Roles.stx',
                                   help_product='OFSP')

    def has_local_roles(self):
        dict=self.__ac_local_roles__ or {}
        return len(dict)

    def get_local_roles(self):
        dict=self.__ac_local_roles__ or {}
        keys=dict.keys()
        keys.sort()
        info=[]
        for key in keys:
            value=tuple(dict[key])
            info.append((key, value))
        return tuple(info)

    def users_with_local_role(self, role):
        got = {}
        for user, roles in self.get_local_roles():
            if role in roles:
                got[user] = 1
        return got.keys()

    def get_valid_userids(self):
        item=self
        dict={}
        _notfound = []
        while 1:
            aclu = getattr(aq_base(item), '__allow_groups__', _notfound)
            if aclu is not _notfound:
                mlu = getattr(aclu, 'maxlistusers', _notfound)
                if not isinstance(mlu, int): mlu = DEFAULTMAXLISTUSERS
                if mlu < 0: raise OverflowError
                un = getattr(aclu, 'user_names', _notfound)
                if un is not _notfound:
                    unl = un()
                    # maxlistusers of 0 is list all
                    if len(unl) > mlu and mlu != 0:
                        raise OverflowError
                    for name in un():
                        dict[name]=1
            item = getattr(item, 'aq_parent', _notfound)
            if item is _notfound:
                break
        keys=dict.keys()
        keys.sort()
        return tuple(keys)

    def get_local_roles_for_userid(self, userid):
        dict=self.__ac_local_roles__ or {}
        return tuple(dict.get(userid, []))

    def manage_addLocalRoles(self, userid, roles, REQUEST=None):
        """Set local roles for a user."""
        if not roles:
            raise ValueError, 'One or more roles must be given!'
        dict=self.__ac_local_roles__
        if dict is None:
            self.__ac_local_roles__ = dict = {}
        local_roles = list(dict.get(userid, []))
        for r in roles:
            if r not in local_roles:
                local_roles.append(r)
        dict[userid] = local_roles
        self._p_changed=True
        if REQUEST is not None:
            stat='Your changes have been saved.'
            return self.manage_listLocalRoles(self, REQUEST, stat=stat)
    manage_addLocalRoles = postonly(manage_addLocalRoles)

    def manage_setLocalRoles(self, userid, roles, REQUEST=None):
        """Set local roles for a user."""
        if not roles:
            raise ValueError, 'One or more roles must be given!'
        dict=self.__ac_local_roles__
        if dict is None:
            self.__ac_local_roles__ = dict = {}
        dict[userid]=roles
        self._p_changed=True
        if REQUEST is not None:
            stat='Your changes have been saved.'
            return self.manage_listLocalRoles(self, REQUEST, stat=stat)
    manage_setLocalRoles = postonly(manage_setLocalRoles)

    def manage_delLocalRoles(self, userids, REQUEST=None):
        """Remove all local roles for a user."""
        dict=self.__ac_local_roles__
        if dict is None:
            self.__ac_local_roles__ = dict = {}
        for userid in userids:
            if dict.has_key(userid):
                del dict[userid]
        self._p_changed=True
        if REQUEST is not None:
            stat='Your changes have been saved.'
            return self.manage_listLocalRoles(self, REQUEST, stat=stat)
    manage_delLocalRoles = postonly(manage_delLocalRoles)

    #------------------------------------------------------------

    access_debug_info__roles__=()
    def access_debug_info(self):
        """Return debug info.
        """
        clas=class_attrs(self)
        inst=instance_attrs(self)
        data=[]
        _add=data.append
        for key, value in inst.items():
            if key.find('__roles__') >= 0:
                _add({'name': key, 'value': value, 'class': 0})
            if hasattr(value, '__roles__'):
                _add({'name': '%s.__roles__' % key, 'value': value.__roles__,
                      'class': 0})
        for key, value in clas.items():
            if key.find('__roles__') >= 0:
                _add({'name': key, 'value': value, 'class' : 1})
            if hasattr(value, '__roles__'):
                _add({'name': '%s.__roles__' % key, 'value': value.__roles__,
                      'class': 1})
        return data

    def valid_roles(self):
        """Return list of valid roles.
        """
        obj=self
        dict={}
        dup =dict.has_key
        x=0
        while x < 100:
            if hasattr(obj, '__ac_roles__'):
                roles=obj.__ac_roles__
                for role in roles:
                    if not dup(role):
                        dict[role]=1
            if not hasattr(obj, 'aq_parent'):
                break
            obj=obj.aq_parent
            x=x+1
        roles=dict.keys()
        roles.sort()
        return tuple(roles)

    def validate_roles(self, roles):
        """Return true if all given roles are valid.
        """
        valid=self.valid_roles()
        for role in roles:
            if role not in valid:
                return 0
        return 1

    def userdefined_roles(self):
        """Return list of user-defined roles.
        """
        roles=list(self.__ac_roles__)
        for role in classattr(self.__class__,'__ac_roles__'):
            try:    roles.remove(role)
            except: pass
        return tuple(roles)

    def manage_defined_roles(self, submit=None, REQUEST=None):
        """Called by management screen.
        """

        if submit=='Add Role':
            role=reqattr(REQUEST, 'role')
            return self._addRole(role, REQUEST)

        if submit=='Delete Role':
            roles=reqattr(REQUEST, 'roles')
            return self._delRoles(roles, REQUEST)

        return self.manage_access(REQUEST)

    def _addRole(self, role, REQUEST=None):
        if not role:
            return MessageDialog(
                   title  ='Incomplete',
                   message='You must specify a role name',
                   action ='manage_access')
        if role in self.__ac_roles__:
            return MessageDialog(
                   title  ='Role Exists',
                   message='The given role is already defined',
                   action ='manage_access')
        data=list(self.__ac_roles__)
        data.append(role)
        self.__ac_roles__=tuple(data)
        if REQUEST is not None:
            return self.manage_access(REQUEST)
    _addRole = postonly(_addRole)

    def _delRoles(self, roles, REQUEST=None):
        if not roles:
            return MessageDialog(
                   title  ='Incomplete',
                   message='You must specify a role name',
                   action ='manage_access')
        data=list(self.__ac_roles__)
        for role in roles:
            try:    data.remove(role)
            except: pass
        self.__ac_roles__=tuple(data)
        if REQUEST is not None:
            return self.manage_access(REQUEST)
    _delRoles = postonly(_delRoles)

    def _has_user_defined_role(self, role):
        return role in self.__ac_roles__

    # Compatibility names only!!

    smallRolesWidget=selectedRoles=aclAChecked=aclPChecked=aclEChecked=''
    validRoles=valid_roles
    #manage_rolesForm=manage_access

    def manage_editRoles(self, REQUEST, acl_type='A', acl_roles=[]):
        pass

    def _setRoles(self, acl_type, acl_roles):
        pass

    def possible_permissions(self):
        d={}
        for p in Products.__ac_permissions__:
            d[p[0]]=1
        for p in self.aq_acquire('_getProductRegistryData')('ac_permissions'):
            d[p[0]]=1

        for p in self.ac_inherited_permissions(1):
            d[p[0]]=1

        d=d.keys()
        d.sort()

        return d

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

def gather_permissions(klass, result, seen):
    for base in klass.__bases__:
        if base.__dict__.has_key('__ac_permissions__'):
            for p in base.__ac_permissions__:
                name=p[0]
                if seen.has_key(name): continue
                result.append((name, ()))
                seen[name]=None
        gather_permissions(base, result, seen)
    return result
