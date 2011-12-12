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
"""SecurityInfo objects and access control constants.

   SecurityInfo objects are used in class definitions to allow
   a declarative style of associating access control information
   with class attributes.

   More information on using SecurityInfo and guide to Zope security
   for developers can be found in the dev.zope.org "Declarative Security"
   project:

   http://dev.zope.org/Wikis/DevSite/Projects/DeclarativeSecurity

   While SecurityInfo objects largely remove the need for Python
   programmers to care about the underlying implementation, there
   are several constants defined that should be used by code that
   must set __roles__ attributes directly. (the constants are also
   accessible from the AccessControl namespace). The defined access
   control constants and their meanings are:

   ACCESS_PUBLIC:  accessible from restricted code and possibly
                   through the web (if object has a docstring)

   ACCESS_PRIVATE: accessible only from python code

   ACCESS_NONE:    no access

"""

import sys
from logging import getLogger

from App.class_init import InitializeClass
from AccessControl.ImplPython import _what_not_even_god_should_do
from Acquisition import Implicit
from Persistence import Persistent

# always patch Persistent before ClassSecurityInfo is used
Persistent.__class_init__ = InitializeClass

LOG = getLogger('SecurityInfo')


# Security constants - these are imported into the AccessControl
# namespace and can be referenced as AccessControl.PUBLIC etc.

ACCESS_NONE    = _what_not_even_god_should_do
ACCESS_PRIVATE = ()
ACCESS_PUBLIC  = None

_marker = []

class SecurityInfo(Implicit):
    """Encapsulate security information."""

    __security_info__ = 1

    __roles__ = ACCESS_PRIVATE

    def __init__(self):
        self.names = {}
        self.roles = {}

    def _setaccess(self, names, access):
        for name in names:
            if self.names.get(name, access) != access:
                LOG.warn('Conflicting security declarations for "%s"' % name)
                self._warnings = 1
            self.names[name] = access

    declarePublic__roles__=ACCESS_PRIVATE
    def declarePublic(self, name, *names):
        """Declare names to be publicly accessible."""
        self._setaccess((name,) + names, ACCESS_PUBLIC)

    declarePrivate__roles__=ACCESS_PRIVATE
    def declarePrivate(self, name, *names):
        """Declare names to be inaccessible to restricted code."""
        self._setaccess((name,) + names, ACCESS_PRIVATE)

    declareProtected__roles__=ACCESS_PRIVATE
    def declareProtected(self, permission_name, name, *names):
        """Declare names to be associated with a permission."""
        self._setaccess((name,) + names, permission_name)

    declareObjectPublic__roles__=ACCESS_PRIVATE
    def declareObjectPublic(self):
        """Declare the object to be publicly accessible."""
        self._setaccess(('',), ACCESS_PUBLIC)

    declareObjectPrivate__roles__=ACCESS_PRIVATE
    def declareObjectPrivate(self):
        """Declare the object to be inaccessible to restricted code."""
        self._setaccess(('',), ACCESS_PRIVATE)

    declareObjectProtected__roles__=ACCESS_PRIVATE
    def declareObjectProtected(self, permission_name):
        """Declare the object to be associated with a permission."""
        self._setaccess(('',), permission_name)

    setPermissionDefault__roles__=ACCESS_PRIVATE
    def setPermissionDefault(self, permission_name, roles):
        """Declare default roles for a permission"""
        rdict = {}
        for role in roles:
            rdict[role] = 1
        if self.roles.get(permission_name, rdict) != rdict:
            LOG.warn('Conflicting default role'
                'declarations for permission "%s"' % permission_name)
            self._warnings = 1
        self.roles[permission_name] = rdict

    setDefaultAccess__roles__=ACCESS_PRIVATE
    def setDefaultAccess(self, access):
        """Declare default attribute access policy.

        This should be a boolean value, a map of attribute names to
        booleans, or a callable (name, value) -> boolean.
        """
        if isinstance(access, str):
            access = access.lower()
            if access == 'allow':
                access = 1
            elif access == 'deny':
                access = 0
            else:
                raise ValueError, "'allow' or 'deny' expected"
        self.access = access


class ClassSecurityInfo(SecurityInfo):
    """Encapsulate security information for class objects."""

    __roles__ = ACCESS_PRIVATE

    apply__roles__ = ACCESS_PRIVATE
    def apply(self, classobj):
        """Apply security information to the given class object."""

        dict = classobj.__dict__

        # Check the class for an existing __ac_permissions__ and
        # incorporate that if present to support older classes or
        # classes that haven't fully switched to using SecurityInfo.
        if dict.has_key('__ac_permissions__'):
            for item in dict['__ac_permissions__']:
                permission_name = item[0]
                self._setaccess(item[1], permission_name)
                if len(item) > 2:
                    self.setPermissionDefault(permission_name, item[2])

        # Set __roles__ for attributes declared public or private.
        # Collect protected attribute names in ac_permissions.
        ac_permissions = {}
        for name, access in self.names.items():
            if access in (ACCESS_PRIVATE, ACCESS_PUBLIC, ACCESS_NONE):
                setattr(classobj, '%s__roles__' % name, access)
            else:
                if not ac_permissions.has_key(access):
                    ac_permissions[access] = []
                ac_permissions[access].append(name)

        # Now transform our nested dict structure into the nested tuple
        # structure expected of __ac_permissions__ attributes and set
        # it on the class object.
        getRoles = self.roles.get
        __ac_permissions__ = []
        permissions = ac_permissions.items()
        permissions.sort()
        for permission_name, names in permissions:
            roles = getRoles(permission_name, ())
            if len(roles):
                entry = (permission_name, tuple(names), tuple(roles.keys()))
            else:
                entry = (permission_name, tuple(names))
            __ac_permissions__.append(entry)
        for permission_name, roles in self.roles.items():
            if permission_name not in ac_permissions:
                entry = (permission_name, (), tuple(roles.keys()))
                __ac_permissions__.append(entry)
        setattr(classobj, '__ac_permissions__', tuple(__ac_permissions__))

        # Take care of default attribute access policy
        access = getattr(self, 'access', _marker)
        if access is not _marker:
            setattr(classobj, '__allow_access_to_unprotected_subobjects__',
                    access)

        if getattr(self, '_warnings', None):
            LOG.warn('Class "%s" had conflicting '
                'security declarations' % classobj.__name__)

class ClassSecurityInformation(ClassSecurityInfo):
    # Default policy is disallow
    access = 0

_moduleSecurity = {}
_appliedModuleSecurity = {}

def secureModule(mname, *imp):
    modsec = _moduleSecurity.get(mname, None)
    if modsec is None:
        return

    if imp:
        __import__(mname, *imp)
    del _moduleSecurity[mname]
    module = sys.modules[mname]
    modsec.apply(module.__dict__)
    _appliedModuleSecurity[mname] = modsec
    return module

def ModuleSecurityInfo(module_name=None):
    if module_name is not None:
        modsec = _moduleSecurity.get(module_name, None)
        if modsec is not None:
            return modsec
        modsec = _appliedModuleSecurity.get(module_name, None)
        if modsec is not None:
            # Move security info back to to-apply dict (needed for product
            # refresh). Also invoke this check for parent packages already
            # applied
            del _appliedModuleSecurity[module_name]
            _moduleSecurity[module_name] = modsec
            dot = module_name.rfind('.')
            if dot > 0:
                ModuleSecurityInfo(module_name[:dot])
            return modsec
        dot = module_name.rfind('.')
        if dot > 0:
            # If the module is in a package, recursively make sure
            # there are security declarations for the package steps
            # leading to the module
            modname = module_name[dot + 1:]
            pmodsec = ModuleSecurityInfo(module_name[:dot])
            if not pmodsec.names.has_key(modname):
                pmodsec.declarePublic(modname)
    return _ModuleSecurityInfo(module_name)

class _ModuleSecurityInfo(SecurityInfo):
    """Encapsulate security information for modules."""

    __roles__ = ACCESS_PRIVATE

    def __init__(self, module_name=None):
        self.names = {}
        if module_name is not None:
            global _moduleSecurity
            _moduleSecurity[module_name] = self

    __call____roles__ = ACCESS_PRIVATE
    def __call__(self, name, value):
        """Callback for __allow_access_to_unprotected_subobjects__ hook."""
        access = self.names.get(name, _marker)
        if access is not _marker:
            return access == ACCESS_PUBLIC

        return getattr(self, 'access', 0)

    apply__roles__ = ACCESS_PRIVATE
    def apply(self, dict):
        """Apply security information to the given module dict."""

        # Start with default attribute access policy
        access = getattr(self, 'access', _marker)
        if access is not _marker or len(self.names):
            dict['__allow_access_to_unprotected_subobjects__'] = self

        if getattr(self, '_warnings', None):
            LOG.warn('Module "%s" had conflicting '
                'security declarations' % dict['__name__'])

    declareProtected__roles__=ACCESS_PRIVATE
    def declareProtected(self, permission_name, *names):
        """Cannot declare module names protected."""
        pass

    declareObjectProtected__roles__=ACCESS_PRIVATE
    def declareObjectProtected(self, permission_name):
        """Cannot declare module protected."""
        pass

    setDefaultRoles__roles__=ACCESS_PRIVATE
    def setDefaultRoles(self, permission_name, roles):
        """Cannot set default roles for permissions in a module."""
        pass

# Handy little utility functions

def allow_module(module_name):
    """Allow a module and all its contents to be used from a
    restricted Script. The argument module_name may be a simple
    or dotted module or package name. Note that if a package
    path is given, all modules in the path will be available."""
    ModuleSecurityInfo(module_name).setDefaultAccess(1)
    dot = module_name.find('.')
    while dot > 0:
        ModuleSecurityInfo(module_name[:dot]).setDefaultAccess(1)
        dot = module_name.find('.', dot + 1)

def allow_class(Class):
    """Allow a class and all of its methods to be used from a
    restricted Script.  The argument Class must be a class."""
    Class._security = sec = ClassSecurityInfo()
    sec.declareObjectPublic()
    sec.setDefaultAccess(1)
    sec.apply(Class)
    InitializeClass(Class)
