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
"""SecurityInfo objects and access control constants.

   SecurityInfo objects are used in class definitions to allow
   a declarative style of associating access control information
   with class attributes.

   add example here

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

__version__='$Revision$'[11:-2]


import Acquisition, PermissionRole, sys
from zLOG import LOG, WARNING


# Security constants - these are imported into the AccessControl
# namespace and can be referenced as AccessControl.PUBLIC etc.

ACCESS_NONE    = PermissionRole._what_not_even_god_should_do
ACCESS_PRIVATE = ()
ACCESS_PUBLIC  = None

_marker = []

class SecurityInfo(Acquisition.Implicit):
    """Encapsulate security information."""

    __security_info__ = 1
    
    __roles__ = ACCESS_PRIVATE

    def __init__(self):
        self.names = {}
        self.roles = {}

    def _setaccess(self, names, access):
        # Empty names list sets access to the class itself, named ''
        if not len(names):
            names = ('',)
        for name in names:
            if self.names.get(name, access) != access:
                LOG('SecurityInfo', WARNING, 'Conflicting security '
                    'declarations for "%s"' % name)
                self._warnings = 1
            self.names[name] = access

    public__roles__=ACCESS_PRIVATE    
    def public(self, *names):
        """Declare names to be publicly accessible."""
        self._setaccess(names, ACCESS_PUBLIC)

    private__roles__=ACCESS_PRIVATE
    def private(self, *names):
        """Declare names to be inaccessible to restricted code."""
        self._setaccess(names, ACCESS_PRIVATE)

    protected__roles__=ACCESS_PRIVATE
    def protected(self, permission_name, *names):
        """Declare names to be associated with a permission."""
        self._setaccess(names, permission_name)

    setDefaultRoles__roles__=ACCESS_PRIVATE
    def setDefaultRoles(self, permission_name, roles):
        """Declare default roles for a permission"""
        rdict = {}
        for role in roles:
            rdict[role] = 1
        if self.roles.get(permission_name, rdict) != rdict:
            LOG('SecurityInfo', WARNING, 'Conflicting default role'
                'declarations for permission "%s"' % permission_name)
            self._warnings = 1
        self.roles[permission_name] = rdict

    setDefaultAccess__roles__=ACCESS_PRIVATE
    def setDefaultAccess(self, access):
        """Declare default attribute access policy.

        This should be a boolean value, a map of attribute names to
        booleans, or a callable (name, value) -> boolean.
        """
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
                    self.setDefaultRoles(permission_name, item[2])

        # Set __roles__ for attributes declared public or private.
        # Collect protected attribute names in ac_permissions.
        ac_permissions = {}
        for name, access in self.names.items():
            if access in (ACCESS_PRIVATE, ACCESS_PUBLIC):
                attr=getattr(classobj, name, None)
                try: attr.__roles__ = access
                except:
                    rname='%s__roles__' % name
                    dict[rname] = access
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
                entry = (permission_name, tuple(names), tuple(roles))
            else:
                entry = (permission_name, tuple(names))
            __ac_permissions__.append(entry)
        dict['__ac_permissions__'] = tuple(__ac_permissions__)

        # Take care of default attribute access policy
        access = getattr(self, 'access', _marker)
        if access is not _marker:
            dict['__allow_access_to_unprotected_subobjects__'] = access

        if getattr(self, '_warnings', None):
            LOG('SecurityInfo', WARNING, 'Class "%s" had conflicting '
                'security declarations' % classobj.__name__)

_moduleSecurity = {}

def secureModule(mname, *imp):
    modsec = _moduleSecurity.get(mname, None)
    if modsec is None:
        return
    del _moduleSecurity[mname]

    if len(imp):
        apply(__import__, (mname,) + tuple(imp))
    module = sys.modules[mname]
    modsec.apply(module.__dict__)
    return module

class ModuleSecurityInfo(SecurityInfo):
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
            LOG('SecurityInfo', WARNING, 'Module "%s" had conflicting '
                'security declarations' % dict['__name__'])

    def protected(self, permission_name, *names):
        """Cannot declare module names protected."""
        pass

    def setDefaultRoles(self, permission_name, roles):
        """Cannot set default roles for permissions in a module."""
        pass

