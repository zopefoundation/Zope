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
__doc__='''Define Zope\'s default security policy


$Id: ZopeSecurityPolicy.py,v 1.18 2002/01/11 17:14:27 evan Exp $'''
__version__='$Revision: 1.18 $'[11:-2]


_use_python_impl = 0
import os
if os.environ.get("ZOPE_SECURITY_POLICY", None) == "PYTHON":
    _use_python_impl = 1
else:
    try:
        # C Optimization:
        from cAccessControl import ZopeSecurityPolicy
        from SimpleObjectPolicies import _noroles
    except ImportError:
        # Fall back to Python implementation.
        _use_python_impl = 1


if _use_python_impl:

    from types import StringType

    import SimpleObjectPolicies
    from AccessControl import Unauthorized
    _noroles=SimpleObjectPolicies._noroles
    from zLOG import LOG, PROBLEM
    from Acquisition import aq_base

    from PermissionRole import _what_not_even_god_should_do, \
         rolesForPermissionOn


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
            
            self._ownerous=ownerous
            self._authenticated=authenticated

        def validate(self, accessed, container, name, value, context,
                     roles=_noroles, None=None, type=type, IntType=type(0),
                     DictType=type({}), getattr=getattr, _noroles=_noroles,
                     StringType=type(''),
                     Containers=SimpleObjectPolicies.Containers,
                     valid_aq_=('aq_parent','aq_inner', 'aq_explicit')):


            ############################################################
            # Provide special rules for the acquisition attributes
            if type(name) is StringType:
                if name.startswith('aq_') and name not in valid_aq_:
                    return 0

            containerbase = aq_base(container)
            accessedbase=getattr(accessed, 'aq_base', container)

            ############################################################
            # If roles weren't passed in, we'll try to get them from the object

            if roles is _noroles:
                roles=getattr(value, '__roles__', _noroles)

            ############################################################
            # We still might not have any roles

            if roles is _noroles:

                ############################################################
                # We have an object without roles and we didn't get a list
                # of roles passed in. Presumably, the value is some simple
                # object like a string or a list.  We'll try to get roles
                # from its container.
                if container is None: return 0 # Bail if no container

                roles=getattr(container, '__roles__', _noroles)
                if roles is _noroles:
                    aq=getattr(container, 'aq_acquire', None)
                    if aq is None:
                        roles=_noroles
                        if containerbase is not accessedbase: return 0
                    else:
                        # Try to acquire roles
                        try: roles=aq('__roles__')
                        except AttributeError:
                            roles=_noroles
                            if containerbase is not accessedbase: return 0

                # We need to make sure that we are allowed to
                # get unprotected attributes from the container. We are
                # allowed for certain simple containers and if the
                # container says we can. Simple containers
                # may also impose name restrictions.
                p=Containers(type(container), None)
                if p is None:
                    p=getattr(container,
                              '__allow_access_to_unprotected_subobjects__', None)

                if p is not None:
                    tp=type(p)
                    if tp is not IntType:
                        if tp is DictType:
                            p=p.get(name, None)
                        else:
                            p=p(name, value)

                if not p:
                    if (containerbase is accessedbase):
                        raise Unauthorized(name, value)
                    else:
                        return 0

                if roles is _noroles: return 1

                # We are going to need a security-aware object to pass
                # to allowed(). We'll use the container.
                value=container

            # Short-circuit tests if we can:
            try:
                if roles is None or 'Anonymous' in roles: return 1
            except TypeError:
                # 'roles' isn't a sequence
                LOG('Zope Security Policy', PROBLEM, "'%s' passed as roles"
                    " during validation of '%s' is not a sequence." % (
                    `roles`, name))
                raise

            # Check executable security
            stack=context.stack
            if stack:
                eo=stack[-1]

                # If the executable had an owner, can it execute?
                if self._ownerous:
                    owner=eo.getOwner()
                    if (owner is not None) and not owner.allowed(value, roles):
                        # We don't want someone to acquire if they can't
                        # get an unacquired!
                        if accessedbase is containerbase:
                            raise Unauthorized(name, value)
                        return 0

                # Proxy roles, which are a lot safer now.
                proxy_roles=getattr(eo, '_proxy_roles', None)
                if proxy_roles:
                    for r in proxy_roles:
                        if r in roles: return 1

                    # Proxy roles actually limit access!
                    if accessedbase is containerbase:
                        raise Unauthorized(name, value)

                    return 0


            try:
                if self._authenticated and context.user.allowed(value, roles):
                    return 1
            except AttributeError: pass

            # We don't want someone to acquire if they can't get an unacquired!
            if accessedbase is containerbase:
                raise Unauthorized(name, value)

            return 0

        def checkPermission(self, permission, object, context):
            # XXX proxy roles and executable owner are not checked
            roles=rolesForPermissionOn(permission, object)
            if type(roles) is StringType:
                roles=[roles]
            return context.user.allowed(object, roles)
