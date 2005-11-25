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
"""Bad monkey!

BBB: goes away when Zope 3.2 >= r40368 is stiched in

$Id$
"""
def monkeyPatch():
    """Trigger all monkey patches needed to make Five work.

    Monkey patches are kept to a minimum level.
    """
    zope3_monkey()

def zope3_monkey():
    """Fix Zope 3 to have the proper ContainerModifiedEvent that has
    been added for 3.2.
    """
    try:
        from zope.app.container.contained import notifyContainerModified
    except ImportError:
        pass
    else:
        return

    # BBB: goes away when Zope 3.2 >= r40368 is stiched in

    from zope.event import notify
    from zope.interface import implements
    import zope.app.container.contained
    import zope.app.container.interfaces
    from zope.app.event.objectevent import ObjectModifiedEvent
    from zope.app.event.interfaces import IObjectModifiedEvent

    class IContainerModifiedEvent(IObjectModifiedEvent):
        """The container has been modified.

        This event is specific to "containerness" modifications, which
        means addition, removal or reordering of sub-objects.
        """

    zope.app.container.interfaces.IContainerModifiedEvent = \
        IContainerModifiedEvent


    class ContainerModifiedEvent(ObjectModifiedEvent):
        """The container has been modified."""
        implements(IContainerModifiedEvent)

    zope.app.container.contained.ContainerModifiedEvent = \
        ContainerModifiedEvent


    def notifyContainerModified(object, *descriptions):
        """Notify that the container was modified."""
        notify(ContainerModifiedEvent(object, *descriptions))

    zope.app.container.contained.notifyContainerModified = \
        notifyContainerModified
