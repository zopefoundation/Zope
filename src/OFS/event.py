##############################################################################
#
# Copyright (c) 2005 Zope Foundation and Contributors.
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
"""
OFS event definitions.
"""

import OFS.interfaces
from zope.interface import implementer
from zope.interface.interfaces import ObjectEvent


@implementer(OFS.interfaces.IObjectWillBeMovedEvent)
class ObjectWillBeMovedEvent(ObjectEvent):

    """An object will be moved."""

    def __init__(self, object, oldParent, oldName, newParent, newName):
        ObjectEvent.__init__(self, object)
        self.oldParent = oldParent
        self.oldName = oldName
        self.newParent = newParent
        self.newName = newName


@implementer(OFS.interfaces.IObjectWillBeAddedEvent)
class ObjectWillBeAddedEvent(ObjectWillBeMovedEvent):

    """An object will be added to a container."""

    def __init__(self, object, newParent=None, newName=None):
        ObjectWillBeMovedEvent.__init__(self, object, None, None,
                                        newParent, newName)


@implementer(OFS.interfaces.IObjectWillBeRemovedEvent)
class ObjectWillBeRemovedEvent(ObjectWillBeMovedEvent):

    """An object will be removed from a container."""

    def __init__(self, object, oldParent=None, oldName=None):
        ObjectWillBeMovedEvent.__init__(self, object, oldParent, oldName,
                                        None, None)


@implementer(OFS.interfaces.IObjectClonedEvent)
class ObjectClonedEvent(ObjectEvent):

    """An object has been cloned into a container."""
