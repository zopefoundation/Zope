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
from Acquisition import aq_base
from App.config import getConfiguration
from AccessControl import getSecurityManager
from ZODB.POSException import ConflictError
import OFS.interfaces

from zope.interface import implements
from zope.component import adapts
from zope.app.container.contained import dispatchToSublocations
from zope.app.location.interfaces import ISublocations


deprecatedManageAddDeleteClasses = []


def compatibilityCall(method_name, *args):
    """Call a method if events have not been setup yet.

    This is the case for some unit tests that have not been converted to
    use the component architecture.
    """
    if deprecatedManageAddDeleteClasses:
        # Events initialized, don't do compatibility call
        return
    if method_name == 'manage_afterAdd':
        callManageAfterAdd(*args)
    elif method_name == 'manage_beforeDelete':
        callManageBeforeDelete(*args)
    else:
        callManageAfterClone(*args)

def maybeWarnDeprecated(ob, method_name):
    """Send a warning if a method is deprecated.
    """
    if not deprecatedManageAddDeleteClasses:
        # Directives not fully loaded
        return
    for cls in deprecatedManageAddDeleteClasses:
        if isinstance(ob, cls):
            # Already deprecated through zcml
            return
    if getattr(getattr(ob, method_name), '__five_method__', False):
        # Method knows it's deprecated
        return
    class_ = ob.__class__
    warnings.warn(
        "%s.%s.%s is deprecated and will be removed in Zope 2.11, "
        "you should use event subscribers instead, and meanwhile "
        "mark the class with <five:deprecatedManageAddDelete/>"
        % (class_.__module__, class_.__name__, method_name),
        DeprecationWarning)

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
    callManageBeforeDelete(ob, event.object, event.oldParent)

def dispatchObjectMovedEvent(ob, event):
    """Multi-subscriber for IItem + IObjectMovedEvent.
    """
    # First, do the manage_afterAdd dance
    callManageAfterAdd(ob, event.object, event.newParent)
    # Next, dispatch to sublocations
    if OFS.interfaces.IObjectManager.providedBy(ob):
        dispatchToSublocations(ob, event)

def dispatchObjectClonedEvent(ob, event):
    """Multi-subscriber for IItem + IObjectClonedEvent.
    """
    # First, do the manage_afterClone dance
    callManageAfterClone(ob, event.object)
    # Next, dispatch to sublocations
    if OFS.interfaces.IObjectManager.providedBy(ob):
        dispatchToSublocations(ob, event)


def callManageAfterAdd(ob, item, container):
    """Compatibility subscriber for manage_afterAdd.
    """
    if container is None:
        return
    if getattr(aq_base(ob), 'manage_afterAdd', None) is None:
        return
    maybeWarnDeprecated(ob, 'manage_afterAdd')
    ob.manage_afterAdd(item, container)

def callManageBeforeDelete(ob, item, container):
    """Compatibility subscriber for manage_beforeDelete.
    """
    if container is None:
        return
    if getattr(aq_base(ob), 'manage_beforeDelete', None) is None:
        return
    maybeWarnDeprecated(ob, 'manage_beforeDelete')
    import OFS.ObjectManager # avoid circular imports
    try:
        ob.manage_beforeDelete(item, container)
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

def callManageAfterClone(ob, item):
    """Compatibility subscriber for manage_afterClone.
    """
    if getattr(aq_base(ob), 'manage_afterClone', None) is None:
        return
    maybeWarnDeprecated(ob, 'manage_afterClone')
    ob.manage_afterClone(item)
