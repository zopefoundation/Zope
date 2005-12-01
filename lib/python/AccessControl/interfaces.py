##############################################################################
#
# Copyright (c) 2005 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
"""Access control interfaces
"""

from AccessControl.SimpleObjectPolicies import _noroles
from zope.interface import Interface
from zope.interface import Attribute

class ISecurityPolicy(Interface):
    """Plug-in policy for checking access to objects within untrusted code.
    """
    def validate(accessed, container, name, value, context, roles=_noroles):
        """Check that the current user (from context) has access.

        o Raise Unauthorized if access is not allowed;  otherwise, return
          a true value.

        Arguments:

        accessed -- the object that was being accessed

        container -- the object the value was found in

        name -- The name used to access the value

        value -- The value retrieved though the access.

        context -- the security context (normally supplied by the security
                   manager).

        roles -- The roles of the object if already known.
        """

    def checkPermission(permission, object, context):
        """Check whether the current user has a permission w.r.t. an object.
        """

class ISecurityManager(Interface):
    """Check access and manages executable context and policies.
    """
    _policy = Attribute(u'Current Security Policy')

    def validate(accessed=None,
                 container=None,
                 name=None,
                 value=None,
                 roles=_noroles,
                ):
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

    def DTMLValidate(accessed=None,
                     container=None,
                     name=None,
                     value=None,
                     md=None,
                    ):
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

    def checkPermission(permission, object):
        """Check whether the security context allows the given permission on
        the given object.

        Arguments:

        permission -- A permission name

        object -- The object being accessed according to the permission
        """

    def addContext(anExecutableObject):
        """Add an ExecutableObject to the current security context.
        
        o If it declares a custom security policy,  make that policy
          "current";  otherwise, make the "default" security policy
          current.
        """

    def removeContext(anExecutableObject):
        """Remove an ExecutableObject from the current security context.
        
        o Remove all objects from the top of the stack "down" to the
          supplied object.

        o If the top object on the stack declares a custom security policy,
          make that policy "current".

        o If the stack is empty, or if the top declares no custom security
          policy, restore the 'default" security policy as current.
        """

    def getUser():
        """Get the currently authenticated user
        """

    def calledByExecutable():
        """Return a boolean value indicating whether this context was called
           in the context of an by an executable (i.e., one added via
           'addContext').
        """
