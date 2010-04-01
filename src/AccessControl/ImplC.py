##############################################################################
#
# Copyright (c) 2003 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################

"""C implementation of the access control machinery."""

try:
    from AccessControl.cAccessControl import rolesForPermissionOn
    from AccessControl.cAccessControl import PermissionRole
    from AccessControl.cAccessControl import imPermissionRole
    from AccessControl.cAccessControl import _what_not_even_god_should_do
    from AccessControl.cAccessControl import RestrictedDTMLMixin
    from AccessControl.cAccessControl import aq_validate
    from AccessControl.cAccessControl import guarded_getattr
    from AccessControl.cAccessControl import setDefaultBehaviors
    from AccessControl.cAccessControl import ZopeSecurityPolicy \
        as cZopeSecurityPolicy
    from AccessControl.cAccessControl import SecurityManager \
        as cSecurityManager
except ImportError:
    import sys
    # make sure a partial import doesn't pollute sys.modules
    del sys.modules[__name__]
    raise
    
from AccessControl.ImplPython import RestrictedDTML
from AccessControl.ImplPython import SecurityManager
from AccessControl.ImplPython import ZopeSecurityPolicy


class RestrictedDTML(RestrictedDTMLMixin, RestrictedDTML):
    """A mix-in for derivatives of DT_String.String that adds Zope security."""

class ZopeSecurityPolicy(cZopeSecurityPolicy, ZopeSecurityPolicy):
    """A security manager provides methods for checking access and managing
    executable context and policies
    """

class SecurityManager(cSecurityManager, SecurityManager):
    """A security manager provides methods for checking access and managing
    executable context and policies
    """
