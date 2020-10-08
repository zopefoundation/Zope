##############################################################################
#
# Copyright (c) 2005,2010 Zope Foundation and Contributors.
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
Subscriber definitions.
"""

from logging import getLogger

import OFS.interfaces
import zope.component
import zope.interface
import zope.location.interfaces
from AccessControl import getSecurityManager
from Acquisition import aq_base
from App.config import getConfiguration
from ZODB.POSException import ConflictError
from zope.container.contained import dispatchToSublocations
from zope.lifecycleevent.interfaces import IObjectCopiedEvent
from zope.lifecycleevent.interfaces import IObjectMovedEvent


deprecatedManageAddDeleteClasses = []

LOG = getLogger('OFS.subscribers')


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
    if getattr(getattr(ob, method_name), '__five_method__', False):
        # Method knows it's deprecated
        return
    if isinstance(ob, tuple(deprecatedManageAddDeleteClasses)):
        return
    class_ = ob.__class__
    LOG.debug(
        "%s.%s.%s is discouraged. You should use event subscribers instead." %
        (class_.__module__, class_.__name__, method_name))


@zope.interface.implementer(zope.location.interfaces.ISublocations)
@zope.component.adapter(OFS.interfaces.IObjectManager)
class ObjectManagerSublocations:
    """Get the sublocations for an ObjectManager.
    """

    def __init__(self, container):
        self.container = container

    def sublocations(self):
        yield from self.container.objectValues()

# The following subscribers should really be defined in ZCML
# but we don't have enough control over subscriber ordering for
# that to work exactly right.
# (Sometimes IItem comes before IObjectManager, sometimes after,
# depending on some of Zope's classes.)
# This code can be simplified when Zope is completely rid of
# manage_afterAdd & co, then IItem wouldn't be relevant anymore and we
# could have a simple subscriber for IObjectManager that directly calls
# dispatchToSublocations.


@zope.component.adapter(OFS.interfaces.IItem,
                        OFS.interfaces.IObjectWillBeMovedEvent)
def dispatchObjectWillBeMovedEvent(ob, event):
    """Multi-subscriber for IItem + IObjectWillBeMovedEvent.
    """
    # First, dispatch to sublocations
    if OFS.interfaces.IObjectManager.providedBy(ob):
        dispatchToSublocations(ob, event)
    # Next, do the manage_beforeDelete dance
    callManageBeforeDelete(ob, event.object, event.oldParent)


@zope.component.adapter(OFS.interfaces.IItem, IObjectMovedEvent)
def dispatchObjectMovedEvent(ob, event):
    """Multi-subscriber for IItem + IObjectMovedEvent.
    """
    # First, do the manage_afterAdd dance
    callManageAfterAdd(ob, event.object, event.newParent)
    # Next, dispatch to sublocations
    if OFS.interfaces.IObjectManager.providedBy(ob):
        dispatchToSublocations(ob, event)


@zope.component.adapter(OFS.interfaces.IItem,
                        OFS.interfaces.IObjectClonedEvent)
def dispatchObjectClonedEvent(ob, event):
    """Multi-subscriber for IItem + IObjectClonedEvent.
    """
    # First, do the manage_afterClone dance
    callManageAfterClone(ob, event.object)
    # Next, dispatch to sublocations
    if OFS.interfaces.IObjectManager.providedBy(ob):
        dispatchToSublocations(ob, event)


@zope.component.adapter(OFS.interfaces.IItem, IObjectCopiedEvent)
def dispatchObjectCopiedEvent(ob, event):
    """Multi-subscriber for IItem + IObjectCopiedEvent.
    """
    # Dispatch to sublocations
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
    import OFS.ObjectManager  # avoid circular imports
    try:
        ob.manage_beforeDelete(item, container)
    except OFS.ObjectManager.BeforeDeleteException:
        raise
    except ConflictError:
        raise
    except Exception:
        LOG.error('_delObject() threw', exc_info=True)
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
