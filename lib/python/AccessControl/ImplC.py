##############################################################################
#
# Copyright (c) 2003 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################

"""C implementation of the access control machinery."""


try:
    from cAccessControl import rolesForPermissionOn, \
         PermissionRole, imPermissionRole, _what_not_even_god_should_do, \
         RestrictedDTMLMixin, aq_validate, guarded_getattr, \
         setDefaultBehaviors
    from cAccessControl import ZopeSecurityPolicy as cZopeSecurityPolicy
    from cAccessControl import SecurityManager as cSecurityManager
except ImportError:
    import sys
    # make sure a partial import doesn't pollute sys.modules
    del sys.modules[__name__]


from ImplPython import RestrictedDTML, SecurityManager, ZopeSecurityPolicy


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
