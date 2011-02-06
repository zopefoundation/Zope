##############################################################################
#
# Copyright (c) 2004, 2005 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Five security handling

$Id$
"""
from zope.deferredimport import deprecated

deprecated("Please import InitializeClass from App.class_init",
           initializeClass = 'App.class_init:InitializeClass',
          )

from zope.component import getUtility
from zope.component import queryUtility
from zope.interface import classProvides
from zope.interface import implements
from zope.security.checker import CheckerPublic
from zope.security.interfaces import IInteraction
from zope.security.interfaces import ISecurityPolicy
from zope.security.interfaces import IPermission
from zope.security.management import thread_local
from zope.security.simplepolicies import ParanoidSecurityPolicy

from AccessControl.SecurityInfo import ClassSecurityInfo
from AccessControl.SecurityManagement import getSecurityManager
from AccessControl.Permission import _registeredPermissions
from AccessControl.Permission import pname

import Products

from AccessControl.Permission import ApplicationDefaultPermissions

CheckerPublicId = 'zope.Public'
CheckerPrivateId = 'zope2.Private'

def getSecurityInfo(klass):
    sec = {}
    info = vars(klass)
    if info.has_key('__ac_permissions__'):
        sec['__ac_permissions__'] = info['__ac_permissions__']
    for k, v in info.items():
        if k.endswith('__roles__'):
            sec[k] = v
    return sec

def clearSecurityInfo(klass):
    sec = {}
    info = vars(klass)
    if info.has_key('__ac_permissions__'):
        delattr(klass, '__ac_permissions__')
    for k, v in info.items():
        if k.endswith('__roles__'):
            delattr(klass, k)

def checkPermission(permission, object, interaction=None):
    """Return whether security policy allows permission on object.

    Arguments:
    permission -- A permission name
    object -- The object being accessed according to the permission
    interaction -- This Zope 3 concept has no equivalent in Zope 2,
        and is ignored.

    checkPermission is guaranteed to return True if permission is
    CheckerPublic or None.
    """
    if (permission in ('zope.Public', 'zope2.Public') or
        permission is None or permission is CheckerPublic):
        return True

    if isinstance(permission, basestring):
        permission = queryUtility(IPermission, unicode(permission))
        if permission is None:
            return False

    if getSecurityManager().checkPermission(permission.title, object):
        return True

    return False

class FiveSecurityPolicy(ParanoidSecurityPolicy):
    """Security policy that bridges between Zope 3 security mechanisms and
    Zope 2's security policy.

    Don't let the name of the base class fool you... This really just
    delegates to Zope 2's security manager."""
    classProvides(ISecurityPolicy)
    implements(IInteraction)

    def checkPermission(self, permission, object):
        return checkPermission(permission, object)

def newInteraction():
    """Con Zope 3 to use Zope 2's checkPermission.

    Zope 3 when it does a checkPermission will turn around and
    ask the thread local interaction for the checkPermission method.
    By making the interaction *be* Zope 2's security manager, we can
    con Zope 3 into using Zope 2's checker...
    """
    if getattr(thread_local, 'interaction', None) is None:
        thread_local.interaction = FiveSecurityPolicy()

def _getSecurity(klass):
    # a Zope 2 class can contain some attribute that is an instance
    # of ClassSecurityInfo. Zope 2 scans through things looking for
    # an attribute that has the name __security_info__ first
    info = vars(klass)
    for k, v in info.items():
        if hasattr(v, '__security_info__'):
            return v
    # we stuff the name ourselves as __security__, not security, as this
    # could theoretically lead to name clashes, and doesn't matter for
    # zope 2 anyway.
    security = ClassSecurityInfo()
    setattr(klass, '__security__', security)
    return security

def protectName(klass, name, permission_id, override_existing_protection=True):
    """Protect the attribute 'name' on 'klass' using the given
       permission"""
    security = _getSecurity(klass)
    # Zope 2 uses string, not unicode yet
    name = str(name)
    if not override_existing_protection and ('%s__roles__' % name) in dir(klass):
        # There is already a declaration for this name from a base class.
        return
    if permission_id == CheckerPublicId or permission_id is CheckerPublic:
        # Sometimes, we already get a processed permission id, which
        # can mean that 'zope.Public' has been interchanged for the
        # CheckerPublic object
        security.declarePublic(name)
    elif permission_id == CheckerPrivateId:
        security.declarePrivate(name)
    else:
        permission = getUtility(IPermission, name=permission_id)
        # Zope 2 uses string, not unicode yet
        perm = str(permission.title)
        security.declareProtected(perm, name)

def protectClass(klass, permission_id):
    """Protect the whole class with the given permission"""
    security = _getSecurity(klass)
    if permission_id == CheckerPublicId or permission_id is CheckerPublic:
        # Sometimes, we already get a processed permission id, which
        # can mean that 'zope.Public' has been interchanged for the
        # CheckerPublic object
        security.declareObjectPublic()
    elif permission_id == CheckerPrivateId:
        security.declareObjectPrivate()
    else:
        permission = getUtility(IPermission, name=permission_id)
        # Zope 2 uses string, not unicode yet
        perm = str(permission.title)
        security.declareObjectProtected(perm)

def create_permission_from_permission_directive(permission, event):
    """When a new IPermission utility is registered (via the <permission />
    directive), create the equivalent Zope2 style permission.
    """

    global _registeredPermissions

    # Zope 2 uses string, not unicode yet
    zope2_permission = str(permission.title)
    roles = ('Manager',)

    if not _registeredPermissions.has_key(zope2_permission):
        _registeredPermissions[zope2_permission] = 1

        Products.__ac_permissions__ += ((zope2_permission, (), roles,),)

        mangled = pname(zope2_permission)
        setattr(ApplicationDefaultPermissions, mangled, roles)
