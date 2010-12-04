##############################################################################
#
# Copyright (c) 2003 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
""" Order support for 'Object Manager'.
"""

import warnings

from AccessControl.class_init import InitializeClass
from AccessControl.Permissions import access_contents_information
from AccessControl.Permissions import manage_properties
from AccessControl.SecurityInfo import ClassSecurityInfo
from Acquisition import aq_base
from DocumentTemplate.sequence import sort
from zope.interface import implements
from zope.container.contained import notifyContainerModified

from OFS.interfaces import IOrderedContainer as IOrderedContainer
from OFS.ObjectManager import ObjectManager


class OrderSupport(object):

    """ Ordered container mixin class.

    This is an extension to the regular ObjectManager. It saves the objects in
    order and lets you change the order of the contained objects. This is
    particular helpful, if the order does not depend on object attributes, but
    is totally user-specific.
    """

    implements(IOrderedContainer)
    security = ClassSecurityInfo()

    has_order_support = 1
    _default_sort_key = 'position'
    _default_sort_reverse = 0

    manage_options = (
        {'label':'Contents', 'action':'manage_main'},
        )

    #
    #   ZMI Methods
    #

    security.declareProtected(manage_properties, 'manage_move_objects_up')
    def manage_move_objects_up(self, REQUEST, ids=None, delta=1):
        """ Move specified sub-objects up by delta in container.
        """
        if ids:
            try:
                attempt = self.moveObjectsUp(ids, delta)
                message = '%d item%s moved up.' % ( attempt,
                                              ( (attempt!=1) and 's' or '' ) )
            except ValueError, errmsg:
                message = 'Error: %s' % (errmsg)
        else:
            message = 'Error: No items were specified!'
        return self.manage_main(self, REQUEST, skey='position',
                                manage_tabs_message=message, update_menu=1)

    security.declareProtected(manage_properties, 'manage_move_objects_down')
    def manage_move_objects_down(self, REQUEST, ids=None, delta=1):
        """ Move specified sub-objects down by delta in container.
        """
        if ids:
            try:
                attempt = self.moveObjectsDown(ids, delta)
                message = '%d item%s moved down.' % ( attempt,
                                              ( (attempt!=1) and 's' or '' ) )
            except ValueError, errmsg:
                message = 'Error: %s' % (errmsg)
        else:
            message = 'Error: No items were specified!'
        return self.manage_main(self, REQUEST, skey='position',
                                manage_tabs_message=message, update_menu=1)

    security.declareProtected(manage_properties, 'manage_move_objects_to_top')
    def manage_move_objects_to_top(self, REQUEST, ids=None):
        """ Move specified sub-objects to top of container.
        """
        if ids:
            try:
                attempt = self.moveObjectsToTop(ids)
                message = '%d item%s moved to top.' % ( attempt,
                                              ( (attempt!=1) and 's' or '' ) )
            except ValueError, errmsg:
                message = 'Error: %s' % (errmsg)
        else:
            message = 'Error: No items were specified!'
        return self.manage_main(self, REQUEST, skey='position',
                                manage_tabs_message=message, update_menu=1)

    security.declareProtected(manage_properties, 'manage_move_objects_to_bottom')
    def manage_move_objects_to_bottom(self, REQUEST, ids=None):
        """ Move specified sub-objects to bottom of container.
        """
        if ids:
            try:
                attempt = self.moveObjectsToBottom(ids)
                message = '%d item%s moved to bottom.' % ( attempt,
                                              ( (attempt!=1) and 's' or '' ) )
            except ValueError, errmsg:
                message = 'Error: %s' % (errmsg)
        else:
            message = 'Error: No items were specified!'
        return self.manage_main(self, REQUEST, skey='position',
                                manage_tabs_message=message, update_menu=1)

    security.declareProtected(manage_properties, 'manage_set_default_sorting')
    def manage_set_default_sorting(self, REQUEST, key, reverse):
        """ Set default sorting key and direction.
        """
        self.setDefaultSorting(key, reverse)
        return self.manage_main(self, REQUEST, update_menu=1)


    #
    #   IOrderedContainer Interface Methods
    #

    security.declareProtected(manage_properties, 'moveObjectsByDelta')
    def moveObjectsByDelta(self, ids, delta, subset_ids=None,
                           suppress_events=False):
        """ Move specified sub-objects by delta.
        """
        if isinstance(ids, basestring):
            ids = (ids,)
        min_position = 0
        objects = list(self._objects)
        if subset_ids is None:
            subset_ids = self.getIdsSubset(objects)
        else:
            subset_ids = list(subset_ids)
        # unify moving direction
        if delta > 0:
            ids = list(ids)
            ids.reverse()
            subset_ids.reverse()
        counter = 0

        for id in ids:
            old_position = subset_ids.index(id)
            new_position = max( old_position - abs(delta), min_position )
            if new_position == min_position:
                min_position += 1
            if not old_position == new_position:
                subset_ids.remove(id)
                subset_ids.insert(new_position, id)
                counter += 1

        if counter > 0:
            if delta > 0:
                subset_ids.reverse()
            obj_dict = {}
            for obj in objects:
                obj_dict[ obj['id'] ] = obj
            pos = 0
            for i in range( len(objects) ):
                if objects[i]['id'] in subset_ids:
                    try:
                        objects[i] = obj_dict[ subset_ids[pos] ]
                        pos += 1
                    except KeyError:
                        raise ValueError('The object with the id "%s" does '
                                         'not exist.' % subset_ids[pos])
            self._objects = tuple(objects)

        if not suppress_events:
            notifyContainerModified(self)

        return counter

    security.declareProtected(manage_properties, 'moveObjectsUp')
    def moveObjectsUp(self, ids, delta=1, subset_ids=None):
        """ Move specified sub-objects up by delta in container.
        """
        return self.moveObjectsByDelta(ids, -delta, subset_ids)

    security.declareProtected(manage_properties, 'moveObjectsDown')
    def moveObjectsDown(self, ids, delta=1, subset_ids=None):
        """ Move specified sub-objects down by delta in container.
        """
        return self.moveObjectsByDelta(ids, delta, subset_ids)

    security.declareProtected(manage_properties, 'moveObjectsToTop')
    def moveObjectsToTop(self, ids, subset_ids=None):
        """ Move specified sub-objects to top of container.
        """
        return self.moveObjectsByDelta( ids, -len(self._objects), subset_ids )

    security.declareProtected(manage_properties, 'moveObjectsToBottom')
    def moveObjectsToBottom(self, ids, subset_ids=None):
        """ Move specified sub-objects to bottom of container.
        """
        return self.moveObjectsByDelta( ids, len(self._objects), subset_ids )

    security.declareProtected(manage_properties, 'orderObjects')
    def orderObjects(self, key, reverse=None):
        """ Order sub-objects by key and direction.
        """
        ids = [ id for id, obj in sort( self.objectItems(),
                                        ( (key, 'cmp', 'asc'), ) ) ]
        if reverse:
            ids.reverse()
        return self.moveObjectsByDelta( ids, -len(self._objects) )

    security.declareProtected(access_contents_information,
                              'getObjectPosition')
    def getObjectPosition(self, id):
        """ Get the position of an object by its id.
        """
        ids = self.objectIds()
        if id in ids:
            return ids.index(id)
        raise ValueError('The object with the id "%s" does not exist.' % id)

    security.declareProtected(manage_properties, 'moveObjectToPosition')
    def moveObjectToPosition(self, id, position, suppress_events=False):
        """ Move specified object to absolute position.
        """
        delta = position - self.getObjectPosition(id)
        return self.moveObjectsByDelta(id, delta,
                                       suppress_events=suppress_events)

    security.declareProtected(access_contents_information, 'getDefaultSorting')
    def getDefaultSorting(self):
        """ Get default sorting key and direction.
        """
        return self._default_sort_key, self._default_sort_reverse

    security.declareProtected(manage_properties, 'setDefaultSorting')
    def setDefaultSorting(self, key, reverse):
        """ Set default sorting key and direction.
        """
        self._default_sort_key = key
        self._default_sort_reverse = reverse and 1 or 0


    #
    #   Override Inherited Method of ObjectManager Subclass
    #

    def manage_renameObject(self, id, new_id, REQUEST=None):
        """ Rename a particular sub-object without changing its position.
        """
        old_position = self.getObjectPosition(id)
        result = super(OrderSupport, self).manage_renameObject(id, new_id,
                                                               REQUEST)
        self.moveObjectToPosition(new_id, old_position,
                                  suppress_events=True)
        return result

    def tpValues(self):
        # Return a list of subobjects, used by tree tag.
        r=[]
        if hasattr(aq_base(self), 'tree_ids'):
            tree_ids=self.tree_ids
            try:   tree_ids=list(tree_ids)
            except TypeError:
                pass
            if hasattr(tree_ids, 'sort'):
                tree_ids.sort()
            for id in tree_ids:
                if hasattr(self, id):
                    r.append(self._getOb(id))
        else:
            # this part is different from the ObjectManager code
            r = [ obj for obj in self.objectValues()
                  if getattr(obj, 'isPrincipiaFolderish', False) ]
            r = sort( r, ( (self._default_sort_key, 'cmp', 'asc'), ) )
            if self._default_sort_reverse:
                r.reverse()
        return r

    #
    #   Helper methods
    #

    def getIdsSubset(self, objects):
        return [obj['id'] for obj in objects]


InitializeClass(OrderSupport)
