##############################################################################
#
# Copyright (c) 2003 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################


class OrderSupport:
    """ Ordered container mixin class.

    This is an extension to the regular ObjectManager. It saves the objects in
    order and lets you change the order of the contained objects. This is
    particular helpful, if the order does not depend on object attributes, but
    is totally user-specific.
    """

    def moveObjectsByDelta(ids, delta, subset_ids=None):
        """ Move specified sub-objects by delta.

        If delta is higher than the possible maximum, objects will be moved to
        the bottom. If delta is lower than the possible minimum, objects will
        be moved to the top.

        If subset_ids is not None, delta will be interpreted relative to the
        subset specified by a sequence of ids. The position of objects that
        are not part of this subset will not be changed.

        The order of the objects specified by ids will always be preserved. So
        if you don't want to change their original order, make sure the order
        of ids corresponds to their original order.

        If an object with id doesn't exist an error will be raised.

        Permission -- Manage properties

        Returns -- Number of moved sub-objects
        """

    def moveObjectsUp(ids, delta=1, subset_ids=None):
        """ Move specified sub-objects up by delta in container.

        If no delta is specified, delta is 1. See moveObjectsByDelta for more
        details.

        Permission -- Manage properties

        Returns -- Number of moved sub-objects
        """

    def moveObjectsDown(ids, delta=1, subset_ids=None):
        """ Move specified sub-objects down by delta in container.

        If no delta is specified, delta is 1. See moveObjectsByDelta for more
        details.

        Permission -- Manage properties

        Returns -- Number of moved sub-objects
        """

    def moveObjectsToTop(ids, subset_ids=None):
        """ Move specified sub-objects to top of container.

        See moveObjectsByDelta for more details.

        Permission -- Manage properties

        Returns -- Number of moved sub-objects
        """

    def moveObjectsToBottom(ids, subset_ids=None):
        """ Move specified sub-objects to bottom of container.

        See moveObjectsByDelta for more details.

        Permission -- Manage properties

        Returns -- Number of moved sub-objects
        """

    def orderObjects(key, reverse=None):
        """ Order sub-objects by key and direction.

        Permission -- Manage properties

        Returns -- Number of moved sub-objects
        """

    def getObjectPosition(id):
        """ Get the position of an object by its id.

        Permission -- Access contents information

        Returns -- Position
        """

    def moveObjectToPosition(id, position):
        """ Move specified object to absolute position.

        Permission -- Manage properties

        Returns -- Number of moved sub-objects
        """
