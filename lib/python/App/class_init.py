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

from AccessControl.PermissionRole import PermissionRole
import AccessControl.Permission

class ApplicationDefaultPermissions:
    _View_Permission='Manager', 'Anonymous'
    _Access_contents_information_Permission='Manager', 'Anonymous'


def default__class_init__(self):
    dict=self.__dict__
    have=dict.has_key
    ft=type(default__class_init__)
    dict_items=dict.items()

    for name, v in dict_items:
        if getattr(v, '_need__name__', 0):
            d = v.__dict__
            oldname = d.get('__name__', '')
            if d.get('_implicit__name__', 0):
                # Already supplied a name.
                if name != oldname:
                    # Tried to implicitly assign a different name!
                    try: classname = '%s.%s' % (
                        self.__module__, self.__name__)
                    except AttributeError: classname = `self`
                    from zLOG import LOG, WARNING
                    LOG('Init', WARNING, 'Ambiguous name for method of %s: '
                        '"%s" != "%s"' % (classname, d['__name__'], name))
            else:
                # Supply a name implicitly so that the method can
                # find the security assertions on its container.
                d['_implicit__name__'] = 1
                d['__name__']=name
            if name=='manage' or name[:7]=='manage_':
                name=name+'__roles__'
                if not have(name): dict[name]=('Manager',)
        elif name=='manage' or name[:7]=='manage_' and type(v) is ft:
            name=name+'__roles__'
            if not have(name): dict[name]='Manager',

    # Look for a SecurityInfo object on the class. If found, call its
    # apply() method to generate __ac_permissions__ for the class. We
    # delete the SecurityInfo from the class dict after it has been
    # applied out of paranoia.
    for key, value in dict_items:
        if hasattr(value, '__security_info__'):
            security_info=value
            security_info.apply(self)
            del dict[key]
            break

    if self.__dict__.has_key('__ac_permissions__'):
        AccessControl.Permission.registerPermissions(self.__ac_permissions__)
        for acp in self.__ac_permissions__:
            pname, mnames = acp[:2]
            if len(acp) > 2:
                roles = acp[2]
                pr = PermissionRole(pname, roles)
            else:
                pr=PermissionRole(pname)
            for mname in mnames:
                dict[mname+'__roles__']=pr
