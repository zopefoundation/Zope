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
__doc__='''short description


$Id: SecurityManager.py,v 1.8 2001/10/26 16:07:50 matt Exp $'''
__version__='$Revision: 1.8 $'[11:-2]

import ZopeSecurityPolicy, os, string

_noroles = ZopeSecurityPolicy._noroles

try: max_stack_size=string.atoi(os.environ.get('Z_MAX_STACK_SIZE','100'))
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
        'validate': 1, 'validateValue': 1, 'checkPermission': 1,
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

    def validateValue(self, value, roles=_noroles):
        """Convenience for common case of simple value validation.
        """
        policy=self._policy
        if roles is _noroles:
            return policy.validate(None, None, None, value,
                                   self._context)
        else:
            return policy.validate(None, None, None, value,
                                   self._context, roles)

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
    #raise ImportError
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
