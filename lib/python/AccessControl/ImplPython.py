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

"""Python implementation of the access control machinery."""

import os
import string

from Acquisition import aq_base
from Acquisition import aq_parent
from Acquisition import aq_inner
from Acquisition import aq_acquire
from ExtensionClass import Base
from zLOG import LOG, PROBLEM

# This is used when a permission maps explicitly to no permission.  We
# try and get this from cAccessControl first to make sure that if both
# security implementations exist, we can switch between them later.
try:
    from cAccessControl import _what_not_even_god_should_do
except ImportError:
    _what_not_even_god_should_do = []

from AccessControl import SecurityManagement
from AccessControl import Unauthorized
from AccessControl.SimpleObjectPolicies import Containers, _noroles
from AccessControl.ZopeGuards import guarded_getitem


# AccessControl.PermissionRole
# ----------------------------

_ident_chars = string.ascii_letters + string.digits + "_"
name_trans = filter(lambda c, an=_ident_chars: c not in an,
                    map(chr, range(256)))
name_trans = string.maketrans(''.join(name_trans), '_' * len(name_trans))

_default_roles = ('Manager',)

def rolesForPermissionOn(perm, object, default=_default_roles, n=None):
    """Return the roles that have the given permission on the given object
    """
    n = n or '_' + string.translate(perm, name_trans) + "_Permission"
    r = None
    
    while 1:
        if hasattr(object, n):
            roles = getattr(object, n)
            if roles is None:
                return 'Anonymous',

            t = type(roles)
            if t is tuple:
                # If we get a tuple, then we don't acquire
                if r is None:
                    return roles
                return r+list(roles)

            if t is str:
                # We found roles set to a name.  Start over
                # with the new permission name.  If the permission
                # name is '', then treat as private!
                if roles:
                    n = roles
                else:
                    return _what_not_even_god_should_do

            elif roles:
                if r is None:
                    r = list(roles)
                else: r = r + list(roles)

        object = getattr(object, 'aq_inner', None)
        if object is None:
            break
        object = object.aq_parent

    if r is None:
        return default

    return r



class PermissionRole(Base):
    """Implement permission-based roles.

    Under normal circumstances, our __of__ method will be
    called with an unwrapped object.  The result will then be called
    with a wrapped object, if the original object was wrapped.
    To deal with this, we have to create an intermediate object.

    """

    def __init__(self, name, default=('Manager',)):
        self.__name__ = name
        self._p = '_' + string.translate(name, name_trans) + "_Permission"
        self._d = self.__roles__ = default

    def __of__(self, parent):
        r = imPermissionRole()
        r._p = self._p
        r._pa = parent
        r._d = self._d
        p = getattr(parent, 'aq_inner', None)
        if p is not None:
            return r.__of__(p)
        else:
            return r

    def rolesForPermissionOn(self, value):
        return rolesForPermissionOn(None, value, self._d, self._p)


class imPermissionRole(Base):
    """Implement permission-based roles"""

    def __of__(self, value):
        return rolesForPermissionOn(None, value, self._d, self._p)
    rolesForPermissionOn = __of__

    # The following methods are needed in the unlikely case that an unwrapped
    # object is accessed:
    def __getitem__(self, i):
        try:
            v = self._v
        except:
            v = self._v = self.__of__(self._pa)
            del self._pa

        return v[i]

    def __len__(self):
        try:
            v = self._v
        except:
            v = self._v = self.__of__(self._pa)
            del self._pa

        return len(v)


# AccessControl.DTML
# ------------------

class RestrictedDTML:
    """A mix-in for derivatives of DT_String.String that adds Zope security."""

    def guarded_getattr(self, *args): # ob, name [, default]
        return guarded_getattr(*args)

    def guarded_getitem(self, ob, index):
        return guarded_getitem(ob, index)


# AccessControl.ZopeSecurityPolicy
# --------------------------------
#
#   TODO:  implement this in cAccessControl, and have Implementation
#          do the indirection.
#
from AccessControl.ZopeSecurityPolicy import getRoles  # XXX

class ZopeSecurityPolicy:

    def __init__(self, ownerous=1, authenticated=1):
        """Create a Zope security policy.

        Two optional keyword arguments may be provided:

        ownerous -- Untrusted users can create code
                    (e.g. Python scripts or templates),
                    so check that code owners can access resources.
                    The argument must have a truth value.
                    The default is true.

        authenticated -- Allow access to resources based on the
                    privaledges of the authenticated user.
                    The argument must have a truth value.
                    The default is true.

                    This (somewhat experimental) option can be set
                    to false on sites that allow only public
                    (unauthenticated) access. An anticipated
                    scenario is a ZEO configuration in which some
                    clients allow only public access and other
                    clients allow full management.
        """
        self._ownerous = ownerous
        self._authenticated = authenticated

    def validate(self, accessed, container, name, value, context,
                 roles=_noroles, getattr=getattr, _noroles=_noroles,
                 valid_aq_=('aq_parent','aq_inner', 'aq_explicit')):

        # Note: accessed is not used.

        ############################################################
        # Provide special rules for the acquisition attributes
        if isinstance(name, str):
            if name.startswith('aq_') and name not in valid_aq_:
                raise Unauthorized(name, value)

        containerbase = aq_base(container)
        accessedbase = aq_base(accessed)
        if accessedbase is accessed:
            # accessed is not a wrapper, so assume that the
            # value could not have been acquired.
            accessedbase = container

        ############################################################
        # If roles weren't passed in, we'll try to get them from the object

        if roles is _noroles:
            roles = getRoles(container, name, value, _noroles)

        ############################################################
        # We still might not have any roles

        if roles is _noroles:

            ############################################################
            # We have an object without roles and we didn't get a list
            # of roles passed in. Presumably, the value is some simple
            # object like a string or a list.  We'll try to get roles
            # from its container.
            if container is None:
                # Either container or a list of roles is required
                # for ZopeSecurityPolicy to know whether access is
                # allowable.
                raise Unauthorized(name, value)

            roles = getattr(container, '__roles__', roles)
            if roles is _noroles:
                if containerbase is container:
                    # Container is not wrapped.
                    if containerbase is not accessedbase:
                        raise Unauthorized(name, value)
                else:
                    # Try to acquire roles
                    try: roles = container.aq_acquire('__roles__')
                    except AttributeError:
                        if containerbase is not accessedbase:
                            raise Unauthorized(name, value)

            # We need to make sure that we are allowed to
            # get unprotected attributes from the container. We are
            # allowed for certain simple containers and if the
            # container says we can. Simple containers
            # may also impose name restrictions.
            p = Containers(type(container), None)
            if p is None:
                p = getattr(container,
                            '__allow_access_to_unprotected_subobjects__',
                            None)

            if p is not None:
                tp = p.__class__
                if tp is not int:
                    if tp is dict:
                        if isinstance(name, basestring):
                            p = p.get(name)
                        else:
                            p = 1
                    else:
                        p = p(name, value)

            if not p:
                raise Unauthorized(name, value)

            if roles is _noroles:
                return 1

            # We are going to need a security-aware object to pass
            # to allowed(). We'll use the container.
            value = container

        # Short-circuit tests if we can:
        try:
            if roles is None or 'Anonymous' in roles:
                return 1
        except TypeError:
            # 'roles' isn't a sequence
            LOG('Zope Security Policy', PROBLEM, "'%s' passed as roles"
                " during validation of '%s' is not a sequence." % (
                `roles`, name))
            raise

        # Check executable security
        stack = context.stack
        if stack:
            eo = stack[-1]

            # If the executable had an owner, can it execute?
            if self._ownerous:
                owner = eo.getOwner()
                if (owner is not None) and not owner.allowed(value, roles):
                    # We don't want someone to acquire if they can't
                    # get an unacquired!
                    raise Unauthorized(name, value)

            # Proxy roles, which are a lot safer now.
            proxy_roles = getattr(eo, '_proxy_roles', None)
            if proxy_roles:
                # Verify that the owner actually can state the proxy role
                # in the context of the accessed item; users in subfolders
                # should not be able to use proxy roles to access items
                # above their subfolder!
                owner = eo.getWrappedOwner()

                if owner is not None:
                    if container is not containerbase:
                        # Unwrapped objects don't need checking
                        if not owner._check_context(container):
                            # container is higher up than the owner,
                            # deny access
                            raise Unauthorized(name, value)

                for r in proxy_roles:
                    if r in roles:
                        return 1

                # Proxy roles actually limit access!
                raise Unauthorized(name, value)

        try:
            if self._authenticated and context.user.allowed(value, roles):
                return 1
        except AttributeError:
            pass

        raise Unauthorized(name, value)

    def checkPermission(self, permission, object, context):
        # XXX proxy roles and executable owner are not checked
        roles = rolesForPermissionOn(permission, object)
        if isinstance(roles, basestring):
            roles = [roles]
        return context.user.allowed(object, roles)


# AccessControl.SecurityManager
# -----------------------------

# There is no corresponding control in the C implementation of the
# access control machinery (cAccessControl.c); this should probably go
# away in a future version.  If you're concerned about the size of
# security stack, you probably have bigger problems.
#
try: max_stack_size = int(os.environ.get('Z_MAX_STACK_SIZE','100'))
except: max_stack_size = 100

def setDefaultBehaviors(ownerous, authenticated):
    global _defaultPolicy
    _defaultPolicy = ZopeSecurityPolicy(
        ownerous=ownerous,
        authenticated=authenticated)

setDefaultBehaviors(True, True)


class SecurityManager:
    """A security manager provides methods for checking access and managing
    executable context and policies
    """

    __allow_access_to_unprotected_subobjects__ = {
        'validate': 1, 'checkPermission': 1,
        'getUser': 1, 'calledByExecutable': 1
        }

    def __init__(self, thread_id, context):
        self._thread_id = thread_id
        self._context = context
        self._policy = _defaultPolicy

    def validate(self, accessed=None, container=None, name=None, value=None,
                 roles=_noroles):
        """Validate access.

        Arguments:

        accessed -- the object that was being accessed

        container -- the object the value was found in

        name -- The name used to access the value

        value -- The value retrieved though the access.

        roles -- The roles of the object if already known.

        The arguments may be provided as keyword arguments. Some of these
        arguments may be ommitted, however, the policy may reject access
        in some cases when arguments are ommitted.  It is best to provide
        all the values possible.
        """
        policy = self._policy
        if roles is _noroles:
            return policy.validate(accessed, container, name, value,
                                   self._context)
        else:
            return policy.validate(accessed, container, name, value,
                                   self._context, roles)

    def DTMLValidate(self, accessed=None, container=None, name=None,
                    value=None, md=None):
        """Validate access.
        * THIS EXISTS FOR DTML COMPATIBILITY *

        Arguments:

        accessed -- the object that was being accessed

        container -- the object the value was found in

        name -- The name used to access the value

        value -- The value retrieved though the access.

        md -- multidict for DTML (ignored)

        The arguments may be provided as keyword arguments. Some of these
        arguments may be ommitted, however, the policy may reject access
        in some cases when arguments are ommitted.  It is best to provide
        all the values possible.

        """
        policy = self._policy
        return policy.validate(accessed, container, name, value, self._context)

    def checkPermission(self, permission, object):
        """Check whether the security context allows the given permission on
        the given object.

        Arguments:

        permission -- A permission name

        object -- The object being accessed according to the permission
        """
        policy = self._policy
        return policy.checkPermission(permission, object, self._context)

    def addContext(self, anExecutableObject,
                   getattr=getattr):
        """Add an ExecutableObject to the current security
        context. Optionally, add a new SecurityPolicy as well.
        """
        stack = self._context.stack
        if len(stack) > max_stack_size:
            raise SystemError, 'Excessive recursion'
        stack.append(anExecutableObject)
        p = getattr(anExecutableObject, '_customSecurityPolicy', None)
        if p is not None:
            p = p()
        else:
            p = _defaultPolicy
        self._policy = p

    def removeContext(self, anExecutableObject):
        """Remove an ExecutableObject, and optionally, a
        SecurityPolicy, from the current security context.
        """
        stack = self._context.stack
        if not stack:
            return
        top = stack[-1]
        if top is anExecutableObject:
            del stack[-1]
        else:
            indexes = range(len(stack))
            indexes.reverse()
            for i in indexes:
                top = stack[i]
                if top is anExecutableObject:
                    del stack[i:]
                    break
            else:
                return

        if stack:
            top = stack[-1]
            p = getattr(top, '_customSecurityPolicy', None)
            if p is not None:
                p = p()
            else:
                p = _defaultPolicy
            self._policy = p
        else:
            self._policy = _defaultPolicy

    def getUser(self):
        """Get the current authenticated user"""
        return self._context.user

    def calledByExecutable(self):
        """Return a boolean value indicating if this context was called
        by an executable"""
        return len(self._context.stack)


# AccessControl.ZopeGuards
# ------------------------

def aq_validate(inst, object, name, v, validate):
    return validate(inst, object, name, v)


_marker = object()

def guarded_getattr(inst, name, default=_marker):
    """Retrieves an attribute, checking security in the process.

    Raises Unauthorized if the attribute is found but the user is
    not allowed to access the attribute.
    """
    if name[:1] == '_':
        raise Unauthorized, name

    # Try to get the attribute normally so that unusual
    # exceptions are caught early.
    try:
        v = getattr(inst, name)
    except AttributeError:
        if default is not _marker:
            return default
        raise

    try:
        container = v.im_self
    except AttributeError:
        container = aq_parent(aq_inner(v)) or inst

    assertion = Containers(type(container))

    if isinstance(assertion, dict):
        # We got a table that lets us reason about individual
        # attrs
        assertion = assertion.get(name)
        if assertion:
            # There's an entry, but it may be a function.
            if callable(assertion):
                return assertion(inst, name)

            # Nope, it's boolean
            return v
        raise Unauthorized, name

    if assertion:
        if callable(assertion):
            factory = assertion(name, v)
            if callable(factory):
                return factory(inst, name)
            assert factory == 1
        else:
            assert assertion == 1
        return v


    # See if we can get the value doing a filtered acquire.
    # aq_acquire will either return the same value as held by
    # v or it will return an Unauthorized raised by validate.
    validate = SecurityManagement.getSecurityManager().validate
    aq_acquire(inst, name, aq_validate, validate)
    
    return v
