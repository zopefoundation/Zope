##############################################################################
# 
# Zope Public License (ZPL) Version 1.0
# -------------------------------------
# 
# Copyright (c) Digital Creations.  All rights reserved.
# 
# This license has been certified as Open Source(tm).
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
# 
# 1. Redistributions in source code must retain the above copyright
#    notice, this list of conditions, and the following disclaimer.
# 
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions, and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
# 
# 3. Digital Creations requests that attribution be given to Zope
#    in any manner possible. Zope includes a "Powered by Zope"
#    button that is installed by default. While it is not a license
#    violation to remove this button, it is requested that the
#    attribution remain. A significant investment has been put
#    into Zope, and this effort will continue if the Zope community
#    continues to grow. This is one way to assure that growth.
# 
# 4. All advertising materials and documentation mentioning
#    features derived from or use of this software must display
#    the following acknowledgement:
# 
#      "This product includes software developed by Digital Creations
#      for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
#    In the event that the product being advertised includes an
#    intact Zope distribution (with copyright and license included)
#    then this clause is waived.
# 
# 5. Names associated with Zope or Digital Creations must not be used to
#    endorse or promote products derived from this software without
#    prior written permission from Digital Creations.
# 
# 6. Modified redistributions of any form whatsoever must retain
#    the following acknowledgment:
# 
#      "This product includes software developed by Digital Creations
#      for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
#    Intact (re-)distributions of any official Zope release do not
#    require an external acknowledgement.
# 
# 7. Modifications are encouraged but must be packaged separately as
#    patches to official Zope releases.  Distributions that do not
#    clearly separate the patches from the original work must be clearly
#    labeled as unofficial distributions.  Modifications which do not
#    carry the name Zope may be packaged in any form, as long as they
#    conform to all of the clauses above.
# 
# 
# Disclaimer
# 
#   THIS SOFTWARE IS PROVIDED BY DIGITAL CREATIONS ``AS IS'' AND ANY
#   EXPRESSED OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
#   IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
#   PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL DIGITAL CREATIONS OR ITS
#   CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
#   SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
#   LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF
#   USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#   ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
#   OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT
#   OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
#   SUCH DAMAGE.
# 
# 
# This software consists of contributions made by Digital Creations and
# many individuals on behalf of Digital Creations.  Specific
# attributions are listed in the accompanying credits file.
# 
##############################################################################
"""Access control support"""

__version__='$Revision: 1.23 $'[11:-2]


from Globals import HTMLFile, MessageDialog, Dictionary
from string import join, strip, split, find
from Acquisition import Implicit
import Globals
from Permission import Permission

ListType=type([])

class RoleManager:
    """An obect that has configurable permissions"""

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
        """Return user-role permission settings
        """
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
        self._isBeingUsedAsAMethod(REQUEST, 0)
        for p in self.__ac_permissions__:
            name, value = p[:2]
            p=Permission(name,value,self)
            p.setRole(role_to_manage, name in permissions)

        if REQUEST is not None: return self.manage_access(self,REQUEST)

    manage_acquiredForm=HTMLFile('acquiredEdit', globals())
    def manage_acquiredPermissions(self, permissions=[], REQUEST=None):
        "Change the permissions that acquire"
        self._isBeingUsedAsAMethod(REQUEST, 0)
        for p in self.__ac_permissions__:
            name, value = p[:2]
            p=Permission(name,value,self)
            roles=p.getRoles()
            if roles is None: continue
            if name in permissions: p.setRoles(list(roles))
            else:                   p.setRoles(tuple(roles))

        if REQUEST is not None: return self.manage_access(self,REQUEST)
        

    manage_permissionForm=HTMLFile('permissionEdit', globals())
    def manage_permission(self, permission_to_manage,
                          roles=[], acquire=0, REQUEST=None):
        "Change the settings for the given permission"
        self._isBeingUsedAsAMethod(REQUEST, 0)
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
        
    
    def manage_access(
        trueself, self, REQUEST,
        _normal_manage_access=HTMLFile('access', globals()),
        _method_manage_access=HTMLFile('methodAccess', globals()),
        **kw):
        "Return an interface for making permissions settings"
        if self._isBeingUsedAsAMethod():
            return apply(_method_manage_access,(trueself, self, REQUEST), kw)
        else:
            return apply(_normal_manage_access,(trueself, self, REQUEST), kw)
    
    def manage_changePermissions(self, REQUEST):
        "Change all permissions settings, called by management screen"
        self._isBeingUsedAsAMethod(REQUEST, 0)
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
        "used by management screen"
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
        "used by management screen"
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
        "used by management screen"
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
        "Return debug info"
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
        "Return list of valid roles"
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
        "Return true if all given roles are valid"
        valid=self.valid_roles()
        for role in roles:
            if role not in valid:
                return 0
        return 1

    def userdefined_roles(self):
        "Return list of user-defined roles"
        roles=list(self.__ac_roles__)
        for role in classattr(self.__class__,'__ac_roles__'):
            try:    roles.remove(role)
            except: pass
        return roles


    def manage_defined_roles(self,submit=None,REQUEST=None):
        """Called by management screen."""

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
