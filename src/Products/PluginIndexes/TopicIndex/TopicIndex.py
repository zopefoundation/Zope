##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Topic index.
"""

from logging import getLogger

from App.special_dtml import DTMLFile
from BTrees.IIBTree import IITreeSet
from BTrees.IIBTree import intersection
from BTrees.IIBTree import union
from BTrees.OOBTree import OOBTree
from OFS.SimpleItem import SimpleItem
from Persistence import Persistent
from zope.interface import implements

from Products.PluginIndexes.common.util import parseIndexRequest
from Products.PluginIndexes.interfaces import IPluggableIndex
from Products.PluginIndexes.interfaces import ITopicIndex

from Products.PluginIndexes.TopicIndex.FilteredSet import factory

_marker = []
LOG = getLogger('Zope.TopicIndex')


class TopicIndex(Persistent, SimpleItem):

    """A TopicIndex maintains a set of FilteredSet objects.

    Every FilteredSet object consists of an expression and and IISet with all
    Ids of indexed objects that eval with this expression to 1.
    """
    implements(ITopicIndex, IPluggableIndex)

    meta_type="TopicIndex"
    query_options = ('query', 'operator')

    manage_options= (
        {'label': 'FilteredSets', 'action': 'manage_main'},
    )

    def __init__(self,id,caller=None):
        self.id = id
        self.filteredSets  = OOBTree()
        self.operators = ('or','and')
        self.defaultOperator = 'or'

    def getId(self):
        return self.id

    def clear(self):
        for fs in self.filteredSets.values():
            fs.clear()

    def index_object(self, docid, obj ,threshold=100):
        """ hook for (Z)Catalog """
        for fid, filteredSet in self.filteredSets.items():
            filteredSet.index_object(docid,obj)
        return 1

    def unindex_object(self,docid):
        """ hook for (Z)Catalog """

        for fs in self.filteredSets.values():
            try:
                fs.unindex_object(docid)
            except KeyError:
                LOG.debug('Attempt to unindex document'
                          ' with id %s failed' % docid)
        return 1

    def numObjects(self):
        """Return the number of indexed objects."""
        return "n/a"

    def indexSize(self):
        """Return the size of the index in terms of distinct values."""
        return "n/a"

    def search(self,filter_id):
        if self.filteredSets.has_key(filter_id):
            return self.filteredSets[filter_id].getIds()

    def _apply_index(self, request):
        """ hook for (Z)Catalog
            'request' --  mapping type (usually {"topic": "..." }
        """
        record = parseIndexRequest(request, self.id, self.query_options)
        if record.keys is None:
            return None

        operator = record.get('operator', self.defaultOperator).lower()
        if operator == 'or':  set_func = union
        else: set_func = intersection

        res = None
        for filter_id in record.keys:
            rows = self.search(filter_id)
            res = set_func(res,rows)

        if res:
            return res, (self.id,)
        else:
            return IITreeSet(), (self.id,)

    def uniqueValues(self,name=None, withLength=0):
        """ needed to be consistent with the interface """
        return self.filteredSets.keys()

    def getEntryForObject(self,docid, default=_marker):
        """ Takes a document ID and returns all the information we have
            on that specific object.
        """
        return self.filteredSets.keys()

    def addFilteredSet(self, filter_id, typeFilteredSet, expr):
        # Add a FilteredSet object.
        if self.filteredSets.has_key(filter_id):
            raise KeyError,\
                'A FilteredSet with this name already exists: %s' % filter_id
        self.filteredSets[filter_id] = factory(filter_id,
                                               typeFilteredSet,
                                               expr,
                                              )

    def delFilteredSet(self, filter_id):
        # Delete the FilteredSet object specified by 'filter_id'.
        if not self.filteredSets.has_key(filter_id):
            raise KeyError,\
                'no such FilteredSet:  %s' % filter_id
        del self.filteredSets[filter_id]

    def clearFilteredSet(self, filter_id):
        # Clear the FilteredSet object specified by 'filter_id'.
        if not self.filteredSets.has_key(filter_id):
            raise KeyError,\
                'no such FilteredSet:  %s' % filter_id
        self.filteredSets[filter_id].clear()

    def manage_addFilteredSet(self, filter_id, typeFilteredSet, expr, URL1, \
            REQUEST=None,RESPONSE=None):
        """ add a new filtered set """

        if len(filter_id) == 0: raise RuntimeError,'Length of ID too short'
        if len(expr) == 0: raise RuntimeError,'Length of expression too short'

        self.addFilteredSet(filter_id, typeFilteredSet, expr)

        if RESPONSE:
            RESPONSE.redirect(URL1+'/manage_workspace?'
            'manage_tabs_message=FilteredSet%20added')

    def manage_delFilteredSet(self, filter_ids=[], URL1=None, \
            REQUEST=None,RESPONSE=None):
        """ delete a list of FilteredSets"""

        for filter_id in filter_ids:
            self.delFilteredSet(filter_id)

        if RESPONSE:
            RESPONSE.redirect(URL1+'/manage_workspace?'
            'manage_tabs_message=FilteredSet(s)%20deleted')

    def manage_saveFilteredSet(self,filter_id, expr, URL1=None,\
            REQUEST=None,RESPONSE=None):
        """ save expression for a FilteredSet """

        self.filteredSets[filter_id].setExpression(expr)

        if RESPONSE:
            RESPONSE.redirect(URL1+'/manage_workspace?'
            'manage_tabs_message=FilteredSet(s)%20updated')

    def getIndexSourceNames(self):
        """ return names of indexed attributes """
        return ('n/a',)

    def manage_clearFilteredSet(self, filter_ids=[], URL1=None, \
            REQUEST=None,RESPONSE=None):
        """  clear a list of FilteredSets"""

        for filter_id in filter_ids:
            self.clearFilteredSet(filter_id)

        if RESPONSE:
            RESPONSE.redirect(URL1+'/manage_workspace?'
             'manage_tabs_message=FilteredSet(s)%20cleared')

    manage = manage_main = DTMLFile('dtml/manageTopicIndex',globals())
    manage_main._setName('manage_main')
    editFilteredSet = DTMLFile('dtml/editFilteredSet',globals())


manage_addTopicIndexForm = DTMLFile('dtml/addTopicIndex', globals())

def manage_addTopicIndex(self, id, REQUEST=None, RESPONSE=None, URL3=None):
    """Add a TopicIndex"""
    return self.manage_addIndex(id, 'TopicIndex', extra=None, \
                REQUEST=REQUEST, RESPONSE=RESPONSE, URL1=URL3)
