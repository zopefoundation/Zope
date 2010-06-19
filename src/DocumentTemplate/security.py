##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
"""Add security system support to Document Templates
"""

# Setup RestrictedDTML

from AccessControl.ImplPython import guarded_getattr
from AccessControl.ZopeGuards import guarded_getitem

RestrictedDTML = None

class BaseRestrictedDTML:
    """A mix-in for derivatives of DT_String.String that adds Zope security."""

    def guarded_getattr(self, *args): # ob, name [, default]
        return guarded_getattr(*args)

    def guarded_getitem(self, ob, index):
        return guarded_getitem(ob, index)


# This does not respect the security policy as set by AccessControl. Instead
# it only deals with the C module being compiled or not.
try:
    from AccessControl.cAccessControl import RestrictedDTMLMixin
except ImportError:
    RestrictedDTML = BaseRestrictedDTML
else:
    class RestrictedDTML(RestrictedDTMLMixin, BaseRestrictedDTML):
        """C version of RestrictedDTML."""

# Add security testing capabilities

from AccessControl import SecurityManagement

class DTMLSecurityAPI:
    """API for performing security checks in DTML using '_' methods.
    """

    def SecurityValidate(md, inst, parent, name, value):
        """Validate access.

        Arguments:

        accessed -- the object that was being accessed

        container -- the object the value was found in

        name -- The name used to access the value

        value -- The value retrieved though the access.

        The arguments may be provided as keyword arguments. Some of these
        arguments may be ommitted, however, the policy may reject access
        in some cases when arguments are ommitted.  It is best to provide
        all the values possible.
        """
        return (SecurityManagement
                .getSecurityManager()
                .validate(inst, parent, name, value)
                )

    def SecurityCheckPermission(md, permission, object):
        """Check whether the security context allows the given permission on
        the given object.

        Arguments:

        permission -- A permission name

        object -- The object being accessed according to the permission
        """
        return (SecurityManagement
                .getSecurityManager()
                .checkPermission(permission, object)
                )

    def SecurityGetUser(md):
        """Gen the current authenticated user"""
        return (SecurityManagement
                .getSecurityManager()
                .getUser()
                )

    def SecurityCalledByExecutable(md):
        """Return a boolean value indicating if this context was called
        by an executable"""
        r = (SecurityManagement
             .getSecurityManager()
             .calledByExecutable()
             )
        if r > 0: return r-1
        return r


from DocumentTemplate import DT_Util

for name, v in DTMLSecurityAPI.__dict__.items():
    if name[0] != '_':
        setattr(DT_Util.TemplateDict, name, v)

from types import FunctionType
from AccessControl.ZopeGuards import safe_builtins

for name, v in safe_builtins.items():
    if type(v) is FunctionType:
        v = DT_Util.NotBindable(v)
    if name.startswith('__'):
        continue
    setattr(DT_Util.TemplateDict, name, v)


# Temporarily create a DictInstance so that we can mark its type as
# being a key in the ContainerAssertions.

from AccessControl.SimpleObjectPolicies import ContainerAssertions

class _dummy_class:
    pass

templateDict = DT_Util.TemplateDict()
try:
    dictInstance = templateDict(dummy=1)[0]
    if type(dictInstance) is not type(_dummy_class()):
        ContainerAssertions[type(dictInstance)]=1
except:
    # Hmm, this may cause _() and _.namespace() to fail.
    # What to do?
    pass
