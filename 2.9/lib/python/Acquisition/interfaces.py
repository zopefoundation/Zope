##############################################################################
#
# Copyright (c) 2005 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Acquisition z3 interfaces.

$Id$
"""

from zope.interface import Attribute
from zope.interface import Interface


class IAcquirer(Interface):

    """Acquire attributes from containers.
    """

    def __of__(context):
        """Get the object in a context.
        """


class IAcquisitionWrapper(Interface):

    """Wrapper object for acquisition.
    """

    def aq_acquire(name, filter=None, extra=None, explicit=True, default=0,
                   containment=0):
        """Get an attribute, acquiring it if necessary.
        """

    def aq_inContextOf(obj, inner=1):
        """Test whether the object is currently in the context of the argument.
        """

    aq_base = Attribute(
        """Get the object unwrapped."""
        )

    aq_parent = Attribute(
        """Get the parent of an object."""
        )

    aq_self = Attribute(
        """Get the object with the outermost wrapper removed."""
        )

    aq_inner = Attribute(
        """Get the object with all but the innermost wrapper removed."""
        )

    aq_chain = Attribute(
        """Get a list of objects in the acquisition environment."""
        )
