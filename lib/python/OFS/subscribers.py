##############################################################################
#
# Copyright (c) 2005 Zope Corporation and Contributors.
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
Five subscriber definitions.

$Id$
"""

import warnings
import sys

from zLOG import LOG, ERROR
from App.config import getConfiguration
from AccessControl import getSecurityManager
from ZODB.POSException import ConflictError
import OFS.interfaces

from zope.interface import implements
from zope.component import adapts
from zope.app.container.contained import dispatchToSublocations
from zope.app.location.interfaces import ISublocations


deprecatedManageAddDeleteClasses = []


def hasDeprecatedMethods(ob):
    """Do we need to call the deprecated methods?
    """
    for class_ in deprecatedManageAddDeleteClasses:
        if isinstance(ob, class_):
            return True
    return False

def maybeCallDeprecated(method_name, ob, *args):
    """Call a deprecated method, if the framework doesn't call it already.
    """
    if hasDeprecatedMethods(ob):
        # Already deprecated through zcml
        return
    method = getattr(ob, method_name)
    if getattr(method, '__five_method__', False):
        # Method knows it's deprecated
        return
    if deprecatedManageAddDeleteClasses:
        # Not deprecated through zcml and directives fully loaded
        class_ = ob.__class__
        warnings.warn(
            "Calling %s.%s.%s is deprecated when using Five, "
            "instead use event subscribers or "
            "mark the class with <five:deprecatedManageAddDelete/>"
            % (class_.__module__, class_.__name__, method_name),
            DeprecationWarning)
    # Note that calling the method can lead to incorrect behavior
    # but in the most common case that's better than not calling it.
    method(ob, *args)

##################################################

class ObjectManagerSublocations(object):
    """Get the sublocations for an ObjectManager.
    """
    adapts(OFS.interfaces.IObjectManager)
    implements(ISublocations)

    def __init__(self, container):
        self.container = container

    def sublocations(self):
        for ob in self.container.objectValues():
            yield ob

# The following subscribers should really be defined in ZCML
# but we don't have enough control over subscriber ordering for
# that to work exactly right.
# (Sometimes IItem comes before IObjectManager, sometimes after,
# depending on some of Zope's classes.)
# This code can be simplified when Zope is completely rid of
# manage_afterAdd & co, then IItem wouldn't be relevant anymore and we
# could have a simple subscriber for IObjectManager that directly calls
# dispatchToSublocations.

def dispatchObjectWillBeMovedEvent(ob, event):
    """Multi-subscriber for IItem + IObjectWillBeMovedEvent.
    """
    # First, dispatch to sublocations
    if OFS.interfaces.IObjectManager.providedBy(ob):
        dispatchToSublocations(ob, event)
    # Next, do the manage_beforeDelete dance
    #import pdb; pdb.set_trace()
    if hasDeprecatedMethods(ob):
        callManageBeforeDelete(ob, event)

def dispatchObjectMovedEvent(ob, event):
    """Multi-subscriber for IItem + IObjectMovedEvent.
    """
    # First, do the manage_afterAdd dance
    if hasDeprecatedMethods(ob):
        callManageAfterAdd(ob, event)
    # Next, dispatch to sublocations
    if OFS.interfaces.IObjectManager.providedBy(ob):
        dispatchToSublocations(ob, event)

def dispatchObjectClonedEvent(ob, event):
    """Multi-subscriber for IItem + IObjectClonedEvent.
    """
    # First, do the manage_afterClone dance
    if hasDeprecatedMethods(ob):
        callManageAfterClone(ob, event)
    # Next, dispatch to sublocations
    if OFS.interfaces.IObjectManager.providedBy(ob):
        dispatchToSublocations(ob, event)


def callManageAfterAdd(ob, event):
    """Compatibility subscriber for manage_afterAdd.
    """
    container = event.newParent
    if container is None:
        # this is a remove
        return
    ob.manage_afterAdd(event.object, container)

def callManageBeforeDelete(ob, event):
    """Compatibility subscriber for manage_beforeDelete.
    """
    import OFS.ObjectManager # avoid circular imports
    container = event.oldParent
    if container is None:
        # this is an add
        return
    try:
        ob.manage_beforeDelete(event.object, container)
    except OFS.ObjectManager.BeforeDeleteException:
        raise
    except ConflictError:
        raise
    except:
        LOG('Zope', ERROR, '_delObject() threw', error=sys.exc_info())
        # In debug mode when non-Manager, let exceptions propagate.
        if getConfiguration().debug_mode:
            if not getSecurityManager().getUser().has_role('Manager'):
                raise

def callManageAfterClone(ob, event):
    """Compatibility subscriber for manage_afterClone.
    """
    ob.manage_afterClone(event.object)
