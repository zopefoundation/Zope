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

"""Python implementation of the access control machinery."""

import os
import string
from logging import getLogger

from Acquisition import aq_acquire
from Acquisition import aq_base
from Acquisition import aq_inner
from Acquisition import aq_inContextOf
from Acquisition import aq_parent
from ExtensionClass import Base
from zope.interface import implements

# This is used when a permission maps explicitly to no permission.  We
# try and get this from cAccessControl first to make sure that if both
# security implementations exist, we can switch between them later.
try:
    from cAccessControl import _what_not_even_god_should_do
except ImportError:
    _what_not_even_god_should_do = []

from AccessControl.SecurityManagement import getSecurityManager
from AccessControl.unauthorized import Unauthorized
from AccessControl.interfaces import ISecurityPolicy
from AccessControl.interfaces import ISecurityManager
from AccessControl.SimpleObjectPolicies import Containers
from AccessControl.SimpleObjectPolicies import _noroles
from AccessControl.ZopeGuards import guarded_getitem

LOG = getLogger('ImplPython')

# AccessControl.PermissionRole
# ----------------------------

_ident_chars = string.ascii_letters + string.digits + "_"
name_trans = filter(lambda c, an=_ident_chars: c not in an,
                    map(chr, range(256)))
name_trans = string.maketrans(''.join(name_trans), '_' * len(name_trans))

_default_roles = ('Manager',)

# If _embed_permission_in_roles is enabled, computed __roles__
# attributes will often include a special role that encodes the name
# of the permission from which the roles were derived.  This is useful
# for verbose security exceptions.
_embed_permission_in_roles = 0


def rolesForPermissionOn(perm, object, default=_default_roles, n=None):
    """Return the roles that have the given permission on the given object
    """
    n = n or '_' + string.translate(perm, name_trans) + "_Permission"
    r = None
    
    while 1:
        if hasattr(object, n):
            roles = getattr(object, n)
            if roles is None:
                if _embed_permission_in_roles:
                    return ('Anonymous', n)
                return 'Anonymous',

            t = type(roles)
            if t is tuple:
                # If we get a tuple, then we don't acquire
                if r is None:
                    if _embed_permission_in_roles:
                        return roles + (n,)
                    return roles
                if _embed_permission_in_roles:
                    return r + list(roles) + [n]
                return r + list(roles)

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
                else:
                    r = r + list(roles)

        object = aq_inner(object)
        if object is None:
            break
        object = aq_parent(object)

    if r is None:
        if _embed_permission_in_roles:
            if default:
                if isinstance(default, tuple):
                    return default + (n,)
                else:
                    return default + [n]
            else:
                return [n]
        return default

    if _embed_permission_in_roles:
        return r + [n]
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

    implements(ISecurityPolicy)

    def __init__(self, ownerous=1, authenticated=1, verbose=0):
        """Create a Zope security policy.

        Optional arguments may be provided:

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

        verbose --  Include debugging information in Unauthorized
                    exceptions.  Not suitable for public sites.
        """
        self._ownerous = ownerous
        self._authenticated = authenticated
        self._verbose = verbose

    def validate(self, accessed, container, name, value, context,
                 roles=_noroles, getattr=getattr, _noroles=_noroles,
                 valid_aq_=('aq_parent','aq_inner', 'aq_explicit')):

        ############################################################
        # Provide special rules for the acquisition attributes
        if isinstance(name, str):
            if name.startswith('aq_') and name not in valid_aq_:
                if self._verbose:
                    raiseVerbose(
                        'aq_* names (other than %s) are not allowed'
                        % ', '.join(valid_aq_),
                        accessed, container, name, value, context
                        )
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
                if self._verbose:
                    raiseVerbose(
                        'No container provided',
                        accessed, container, name, value, context)
                raise Unauthorized(name, value)

            roles = getattr(container, '__roles__', roles)
            if roles is _noroles:
                if containerbase is container:
                    # Container is not wrapped.
                    if containerbase is not accessedbase:
                        if self._verbose:
                            raiseVerbose(
                                'Unable to find __roles__ in the container '
                                'and the container is not wrapped',
                                accessed, container, name, value, context)
                        raise Unauthorized(name, value)
                else:
                    # Try to acquire roles
                    try: roles = aq_acquire(container, '__roles__')
                    except AttributeError:
                        if containerbase is not accessedbase:
                            if self._verbose:
                                raiseVerbose(
                                    'Unable to find or acquire __roles__ '
                                    'from the container',
                                    accessed, container, name, value, context)
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
                if not isinstance(p, int): # catches bool too
                    if isinstance(p, dict):
                        if isinstance(name, basestring):
                            p = p.get(name)
                        else:
                            p = 1
                    else:
                        p = p(name, value)

            if not p:
                if self._verbose:
                    raiseVerbose(
                        'The container has no security assertions',
                        accessed, container, name, value, context)
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
            LOG.error("'%s' passed as roles"
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
                    if self._verbose:
                        if len(roles) < 1:
                            raiseVerbose(
                                "The object is marked as private",
                                accessed, container, name, value, context)
                        elif userHasRolesButNotInContext(owner, value, roles):
                            raiseVerbose(
                                "The owner of the executing script is defined "
                                "outside the context of the object being "
                                "accessed",
                                accessed, container, name, value, context,
                                required_roles=roles, eo_owner=owner, eo=eo)
                        else:
                            raiseVerbose(
                                "The owner of the executing script does not "
                                "have the required permission",
                                accessed, container, name, value, context,
                                required_roles=roles, eo_owner=owner, eo=eo,
                                eo_owner_roles=getUserRolesInContext(
                                owner, value))
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
                            if self._verbose:
                                raiseVerbose(
                                    "The owner of the executing script is "
                                    "defined outside the context of the "
                                    "object being accessed.  The script has "
                                    "proxy roles, but they do not apply in "
                                    "this context.",
                                    accessed, container, name, value, context,
                                    required_roles=roles, eo_owner=owner,
                                    eo=eo)
                            raise Unauthorized(name, value)

                for r in proxy_roles:
                    if r in roles:
                        return 1

                # Proxy roles actually limit access!
                if self._verbose:
                    if len(roles) < 1:
                        raiseVerbose(
                            "The object is marked as private",
                            accessed, container, name, value, context)
                    else:
                        raiseVerbose(
                            "The proxy roles set on the executing script "
                            "do not allow access",
                            accessed, container, name, value, context,
                            eo=eo, eo_proxy_roles=proxy_roles,
                            required_roles=roles)
                raise Unauthorized(name, value)

        try:
            if self._authenticated and context.user.allowed(value, roles):
                return 1
        except AttributeError:
            pass

        if self._verbose:
            if len(roles) < 1:
                raiseVerbose(
                    "The object is marked as private",
                    accessed, container, name, value, context)
            elif not self._authenticated:
                raiseVerbose(
                    "Authenticated access is not allowed by this "
                    "security policy",
                    accessed, container, name, value, context)
            elif userHasRolesButNotInContext(context.user, value, roles):
                raiseVerbose(
                    "Your user account is defined outside "
                    "the context of the object being accessed",
                    accessed, container, name, value, context,
                    required_roles=roles, user=context.user)
            else:
                raiseVerbose(
                    "Your user account does not "
                    "have the required permission",
                    accessed, container, name, value, context,
                    required_roles=roles, user=context.user,
                    user_roles=getUserRolesInContext(context.user, value))
        raise Unauthorized(name, value)

    def checkPermission(self, permission, object, context):
        roles = rolesForPermissionOn(permission, object)
        if isinstance(roles, basestring):
            roles = [roles]

        # check executable owner and proxy roles
        stack = context.stack
        if stack:
            eo = stack[-1]
            # If the executable had an owner, can it execute?
            if self._ownerous:
                owner = eo.getOwner()
                if (owner is not None) and not owner.allowed(object, roles):
                    # We don't want someone to acquire if they can't 
                    # get an unacquired!
                    return 0
            proxy_roles = getattr(eo, '_proxy_roles', None)
            if proxy_roles:
                # Verify that the owner actually can state the proxy role
                # in the context of the accessed item; users in subfolders
                # should not be able to use proxy roles to access items 
                # above their subfolder!
                owner = eo.getWrappedOwner()
                if owner is not None:
                    if object is not aq_base(object):
                        if not owner._check_context(object):
                            # object is higher up than the owner, 
                            # deny access
                            return 0

                for r in proxy_roles:
                    if r in roles:
                        return 1
                return 0

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

def setDefaultBehaviors(ownerous, authenticated, verbose):
    global _defaultPolicy
    global _embed_permission_in_roles
    _defaultPolicy = ZopeSecurityPolicy(
        ownerous=ownerous,
        authenticated=authenticated,
        verbose=verbose)
    _embed_permission_in_roles = verbose

setDefaultBehaviors(True, True, False)


class SecurityManager:
    """A security manager provides methods for checking access and managing
    executable context and policies
    """
    implements(ISecurityManager)
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
    validate = getSecurityManager().validate
    aq_acquire(inst, name, aq_validate, validate)
    
    return v


# Helpers for verbose authorization exceptions
# --------------------------------------------

def item_repr(ob):
    """Generates a repr without angle brackets (to avoid HTML quoting)"""
    return repr(ob).replace('<', '(').replace('>', ')')

def simplifyRoles(roles):
    """Sorts and removes duplicates from a role list."""
    d = {}
    for r in roles:
        d[r] = 1
    lst = d.keys()
    lst.sort()
    return lst

def raiseVerbose(msg, accessed, container, name, value, context,
                 required_roles=None,
                 user_roles=None,
                 user=None,
                 eo=None,
                 eo_owner=None,
                 eo_owner_roles=None,
                 eo_proxy_roles=None,
                 ):
    """Raises an Unauthorized error with a verbose explanation."""

    s = '%s.  Access to %s of %s' % (
        msg, repr(name), item_repr(container))
    if aq_base(container) is not aq_base(accessed):
        s += ', acquired through %s,' % item_repr(accessed)
    info = [s + ' denied.']

    if user is not None:
        try:
            ufolder = '/'.join(aq_parent(aq_inner(user)).getPhysicalPath())
        except:
            ufolder = '(unknown)'
        info.append('Your user account, %s, exists at %s.' % (
            str(user), ufolder))

    if required_roles is not None:
        p = None
        required_roles = list(required_roles)
        for r in required_roles:
            if r.startswith('_') and r.endswith('_Permission'):
                p = r[1:]
                required_roles.remove(r)
                break
        sr = simplifyRoles(required_roles)
        if p:
            # got a permission name
            info.append('Access requires %s, '
                        'granted to the following roles: %s.' %
                        (p, sr))
        else:
            # permission name unknown
            info.append('Access requires one of the following roles: %s.'
                        % sr)

    if user_roles is not None:
        info.append(
            'Your roles in this context are %s.' % simplifyRoles(user_roles))

    if eo is not None:
        s = 'The executing script is %s' % item_repr(eo)
        if eo_proxy_roles is not None:
            s += ', with proxy roles: %s' % simplifyRoles(eo_proxy_roles)
        if eo_owner is not None:
            s += ', owned by %s' % repr(eo_owner)
        if eo_owner_roles is not None:
            s += ', who has the roles %s' % simplifyRoles(eo_owner_roles)
        info.append(s + '.')

    text = ' '.join(info)
    LOG.debug('Unauthorized: %s' % text)
    raise Unauthorized(text)

def getUserRolesInContext(user, context):
    """Returns user roles for a context."""
    if hasattr(aq_base(user), 'getRolesInContext'):
        return user.getRolesInContext(context)
    else:
        return ()

def userHasRolesButNotInContext(user, object, object_roles):
    '''Returns 1 if the user has any of the listed roles but
    is not defined in a context which is not an ancestor of object.
    '''
    if object_roles is None or 'Anonymous' in object_roles:
        return 0
    usr_roles = getUserRolesInContext(user, object)
    for role in object_roles:
        if role in usr_roles:
            # User has the roles.
            return (not verifyAcquisitionContext(
                user, object, object_roles))
    return 0

def verifyAcquisitionContext(user, object, object_roles=None):
    """Mimics the relevant section of User.allowed().

    Returns true if the object is in the context of the user's user folder.
    """
    ufolder = aq_parent(user)
    ucontext = aq_parent(ufolder)
    if ucontext is not None:
        if object is None:
            # This is a strange rule, though
            # it doesn't cause any security holes. SDH
            return 1
        if hasattr(object, 'im_self'):
            # This is a method.  Grab its self.
            object=object.im_self
        if not aq_inContextOf(object, ucontext, 1):
            if 'Shared' in object_roles:
                # Old role setting. Waaa
                object_roles=user._shared_roles(object)
                if 'Anonymous' in object_roles:
                    return 1
            return None
    # Note that if the user were not wrapped, it would
    # not be possible to determine the user's context
    # and this method would return 1.
    # However, as long as user folders always return
    # wrapped user objects, this is safe.
    return 1
