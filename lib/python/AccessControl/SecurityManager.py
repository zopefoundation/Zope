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
__doc__='''short description


$Id: SecurityManager.py,v 1.14 2003/11/28 16:44:03 jim Exp $'''
__version__='$Revision: 1.14 $'[11:-2]

import ZopeSecurityPolicy, os

_noroles = ZopeSecurityPolicy._noroles

try: max_stack_size=int(os.environ.get('Z_MAX_STACK_SIZE','100'))
except: max_stack_size=100

if os.environ.has_key("ZSP_OWNEROUS_SKIP"): ownerous=0
else: ownerous=1
if os.environ.has_key("ZSP_AUTHENTICATION_SKIP"): authenticated=0
else: authenticated=1
_defaultPolicy=ZopeSecurityPolicy.ZopeSecurityPolicy(ownerous=ownerous,
    authenticated=authenticated)
def setSecurityPolicy(aSecurityPolicy):
    """Set the system default security policy.

    This method should only be caused by system startup code. It should
    never, for example, be called during a web request.
    """
    global _defaultPolicy
    last=_defaultPolicy
    _defaultPolicy=aSecurityPolicy
    return last


class SecurityManager:
    """A security manager provides methods for checking access and managing
    executable context and policies
    """

    __allow_access_to_unprotected_subobjects__ = {
        'validate': 1, 'checkPermission': 1,
        'getUser': 1, 'calledByExecutable': 1
        }

    def __init__(self, thread_id, context):
        self._thread_id=thread_id
        self._context=context
        self._policy=_defaultPolicy

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
        policy=self._policy
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
        policy=self._policy
        return policy.validate(accessed, container, name, value,
                               self._context)

    def checkPermission(self, permission, object):
        """Check whether the security context allows the given permission on
        the given object.

        Arguments:

        permission -- A permission name

        object -- The object being accessed according to the permission
        """
        policy=self._policy
        return policy.checkPermission(permission, object,
                                      self._context)

    def addContext(self, anExecutableObject,
                   getattr=getattr):
        """Add an ExecutableObject to the current security
        context. Optionally, add a new SecurityPolicy as well.
        """
        stack=self._context.stack
        if len(stack) > max_stack_size:
            raise SystemError, 'Excessive recursion'
        stack.append(anExecutableObject)
        p=getattr(anExecutableObject, '_customSecurityPolicy', None)
        if p is not None:
            p=p()
        else:
            p=_defaultPolicy
        self._policy=p

    def removeContext(self, anExecutableObject,
                      getattr=getattr):
        """Remove an ExecutableObject, and optionally, a
        SecurityPolicy, from the current security context.
        """
        stack=self._context.stack
        if not stack: return
        top=stack[-1]
        if top is anExecutableObject:
            del stack[-1]
        else:
            indexes=range(len(stack))
            indexes.reverse()
            for i in indexes:
                top=stack[i]
                if top is anExecutableObject:
                    del stack[i:]
                    break
            else:
                return

        if stack:
            top=stack[-1]
            p=getattr(top, '_customSecurityPolicy', None)
            if p is not None:
                p=p()
            else:
                p=_defaultPolicy
            self._policy=p
        else:
            self._policy=_defaultPolicy

    def getUser(self):
        """Get the current authenticated user"""
        return self._context.user

    def calledByExecutable(self):
        """Return a boolean value indicating if this context was called
        by an executable"""
        return len(self._context.stack)


try:
    #raise ImportError # uncomment to disable C optimization
    import os
    if os.environ.get("ZOPE_SECURITY_POLICY", None) == "PYTHON":
        raise ImportError # :)
    from cAccessControl import SecurityManager as cSecurityManager
except ImportError:
    pass
else:

    class SecurityManager(cSecurityManager, SecurityManager):
        """A security manager provides methods for checking access and managing
        executable context and policies
        """
