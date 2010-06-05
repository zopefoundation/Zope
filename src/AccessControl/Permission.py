##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Permissions
"""

import string

from Acquisition import aq_base

name_trans=filter(lambda c, an=string.letters+string.digits+'_': c not in an,
                  map(chr, range(256)))
name_trans=string.maketrans(''.join(name_trans), '_'*len(name_trans))


def pname(name, translate=string.translate, name_trans=name_trans):
    return '_'+translate(name, name_trans) + "_Permission"

_marker=[]


class Permission:
    # A Permission maps a named logical permission to a set
    # of attribute names. Attribute names which appear in a
    # permission may not appear in any other permission defined
    # by the object.

    def __init__(self, name, data, obj, default=None):
        self.name = name
        self._p = '_' + string.translate(name, name_trans) + "_Permission"
        self.data = data
        self.obj = aq_base(obj)
        self.default = default

    def getRoles(self, default=_marker):
        # Return the list of role names which have been given
        # this permission for the object in question. To do
        # this, we try to get __roles__ from all of the object
        # attributes that this permission represents.
        obj = self.obj
        name = self._p
        if hasattr(obj, name):
            return getattr(obj, name)
        roles = default
        for name in self.data:
            if name:
                if hasattr(obj, name):
                    attr = getattr(obj, name)
                    if hasattr(attr, 'im_self'):
                        attr = attr.im_self
                        if hasattr(attr, '__dict__'):
                            attr = attr.__dict__
                            name = name + '__roles__'
                            if name in attr:
                                roles = attr[name]
                                break
            elif hasattr(obj, '__dict__'):
                attr = obj.__dict__
                if '__roles__' in attr:
                    roles = attr['__roles__']
                    break

        if roles:
            try:
                if 'Shared' not in roles:
                    return tuple(roles)
                roles = list(roles)
                roles.remove('Shared')
                return roles
            except:
                return []

        if roles is None:
            return ['Manager', 'Anonymous']
        if roles is _marker:
            return ['Manager']

        return roles

    def setRoles(self, roles):
        obj = self.obj

        if isinstance(roles, list) and not roles:
            if hasattr(obj, self._p):
                delattr(obj, self._p)
        else:
            setattr(obj, self._p, roles)

        for name in self.data:
            if name=='':
                attr = obj
            else:
                attr = getattr(obj, name)
            try:
                del attr.__roles__
            except:
                pass
            try:
                delattr(obj, name + '__roles__')
            except:
                pass

    def setRole(self, role, present):
        roles = self.getRoles()
        if role in roles:
            if present:
                return
            if isinstance(roles, list):
                roles.remove(role)
            else:
                roles = list(roles)
                roles.remove(role)
                roles = tuple(roles)
        elif not present:
            return
        else:
            if isinstance(roles, list):
                roles.append(role)
            else:
                roles=roles + (role, )
        self.setRoles(roles)

    def __len__(self):
        return 1

    def __str__(self):
        return self.name


_registeredPermissions = {}
_ac_permissions = ()


def getPermissions():
    return _ac_permissions


def addPermission(perm, default_roles=('Manager', )):
    if perm in _registeredPermissions:
        return

    entry = ((perm, (), default_roles), )
    global _ac_permissions
    _ac_permissions = _ac_permissions + entry
    _registeredPermissions[perm] = 1
    mangled = pname(perm) # get mangled permission name
    if not hasattr(ApplicationDefaultPermissions, mangled):
        setattr(ApplicationDefaultPermissions, mangled, default_roles)


def registerPermissions(permissions, defaultDefault=('Manager', )):
    """Register an __ac_permissions__ sequence.
    """
    for setting in permissions:
        if setting[0] in _registeredPermissions:
            continue
        if len(setting)==2:
            perm, methods = setting
            default = defaultDefault
        else:
            perm, methods, default = setting
        addPermission(perm, default)


class ApplicationDefaultPermissions:
    _View_Permission = ('Manager', 'Anonymous')
    _Access_contents_information_Permission = ('Manager', 'Anonymous')
