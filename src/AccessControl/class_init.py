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
"""Class initialization.

$Id$
"""

import logging

from AccessControl.Permission import ApplicationDefaultPermissions # BBB

def InitializeClass(self):
    from AccessControl.Permission import registerPermissions
    from AccessControl.PermissionRole import PermissionRole
    dict=self.__dict__
    have=dict.has_key
    ft=type(InitializeClass)
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
                    logging.getLogger("Init").warning(
                        'Ambiguous name for method of %s: %r != %r',
                        classname, d['__name__'], name)
            else:
                # Supply a name implicitly so that the method can
                # find the security assertions on its container.
                v._implicit__name__ = 1
                v.__name__ = name
            if name=='manage' or name[:7]=='manage_':
                name=name+'__roles__'
                if not have(name):
                    setattr(self, name, ('Manager',))
        elif name=='manage' or name[:7]=='manage_' and type(v) is ft:
            name=name+'__roles__'
            if not have(name):
                setattr(self, name, ('Manager',))
                
    # Look for a SecurityInfo object on the class. If found, call its
    # apply() method to generate __ac_permissions__ for the class. We
    # delete the SecurityInfo from the class dict after it has been
    # applied out of paranoia.
    for key, value in dict_items:
        if hasattr(value, '__security_info__'):
            security_info=value
            security_info.apply(self)
            delattr(self, key)
            break

    if self.__dict__.has_key('__ac_permissions__'):
        registerPermissions(self.__ac_permissions__)
        for acp in self.__ac_permissions__:
            pname, mnames = acp[:2]
            if len(acp) > 2:
                roles = acp[2]
                pr = PermissionRole(pname, roles)
            else:
                pr = PermissionRole(pname)
            for mname in mnames:
                setattr(self, mname+'__roles__', pr)
                if (mname and mname not in ('context', 'request') and
                    not hasattr(self, mname)):
                    # don't complain about context or request, as they are
                    # frequently not available as class attributes
                    logging.getLogger("Init").warning(
                        "Class %s.%s has a security declaration for "
                        "nonexistent method %r", self.__module__,
                        self.__name__, mname)

default__class_init__ = InitializeClass # BBB: old name
