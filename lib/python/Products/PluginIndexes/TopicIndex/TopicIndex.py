##############################################################################
#
# Copyright (c) 2001 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################

__version__ = '$Id: TopicIndex.py,v 1.12 2003/01/23 17:46:31 andreasjung Exp $'

from Products.PluginIndexes import PluggableIndex
from Products.PluginIndexes.common.util import parseIndexRequest

from Globals import Persistent, DTMLFile
from OFS.SimpleItem import SimpleItem
from Acquisition import Implicit
from BTrees.OOBTree import OOBTree
from BTrees.IIBTree import IISet,intersection,union
from zLOG import ERROR, LOG
import FilteredSet

_marker = []

class TopicIndex(Persistent, Implicit, SimpleItem):

    """ A TopicIndex maintains a set of FilteredSet objects.
    Every FilteredSet object consists of an expression and
    and IISet with all Ids of indexed objects that eval with
    this expression to 1.
    """

    __implements__ = (PluggableIndex.PluggableIndexInterface,)

    meta_type="TopicIndex"

    manage_options= (
        {'label': 'FilteredSets',
         'action': 'manage_workspace',
         'help': ('TopicIndex','TopicIndex_searchResults.stx')},
    )

    manage_workspace = DTMLFile('dtml/manageTopicIndex',globals())

    query_options = ('query','operator')

    def __init__(self,id,caller=None):
        self.id             = id
        self.filteredSets   = OOBTree()
        # experimental code for specifing the operator
        self.operators       = ('or','and')
        self.defaultOperator = 'or'


    def getId(self): return self.id

    def clear(self):
        """ clear everything """
        self.filteredSets = OOBTree()


    def index_object(self, documentId, obj ,threshold=100):
        """ hook for (Z)Catalog """

        for fid, filteredSet in self.filteredSets.items():
            filteredSet.index_object(documentId,obj)

        return 1


    def unindex_object(self,documentId):
        """ hook for (Z)Catalog """

        for fs in self.filteredSets.values():

            try:
                fs.unindex_object(documentId)
            except KeyError:
                LOG(self.__class__.__name__, ERROR,
                    'Attempt to unindex document'
                    ' with id %s failed' % documentId)
        return 1


    def __len__(self):
        """ len """
        n=0
        for fs in self.filteredSets.values():
            n = n + len(fs.getIds())
        return n


    def numObjects(self):
        return "N/A"


    def keys(self):   pass
    def values(self): pass
    def items(self):  pass


    def search(self,filterId):

        if self.filteredSets.has_key(filterId):
            return self.filteredSets[filterId].getIds()


    def _apply_index(self, request, cid=''):
        """ hook for (Z)Catalog
        request   mapping type (usually {"topic": "..." }
        cid      ???
        """

        record = parseIndexRequest(request,self.id,self.query_options)
        if record.keys==None: return None

        # experimental code for specifing the operator
        operator = record.get('operator',self.defaultOperator).lower()

        # depending on the operator we use intersection of union
        if operator=="or":  set_func = union
        else:               set_func = intersection

        res = None

        for filterId in record.keys:
            rows = self.search(filterId)
            res = set_func(res,rows)

        if res:
            return res, (self.id,)
        else:
            return IISet(), (self.id,)


    def uniqueValues(self,name=None,withLength=0):
        """ needed to be consistent with the interface """

        return self.filteredSets.keys()


    def getEntryForObject(self,documentId,default=_marker):
        """ Takes a document ID and returns all the information we have
        on that specific object. """

        return self.filteredSets.keys()


    def addFilteredSet(self, filterId, typeFilteredSet, expr):

        if self.filteredSets.has_key(filterId):
            raise KeyError,\
                'A FilteredSet with this name already exists: %s' % filterId

        self.filteredSets[filterId] = \
            FilteredSet.factory(filterId, typeFilteredSet, expr)


    def delFilteredSet(self,filterId):

        if not self.filteredSets.has_key(filterId):
            raise KeyError,\
                'no such FilteredSet:  %s' % filterId

        del self.filteredSets[filterId]


    def clearFilteredSet(self,filterId):

        if not self.filteredSets.has_key(filterId):
            raise KeyError,\
                'no such FilteredSet:  %s' % filterId

        self.filteredSets[filterId].clear()


    def manage_addFilteredSet(self, filterId, typeFilteredSet, expr, URL1, \
            REQUEST=None,RESPONSE=None):
        """ add a new filtered set """

        if len(filterId)==0: raise RuntimeError,'Length of ID too short'
        if len(expr)==0: raise RuntimeError,'Length of expression too short'

        self.addFilteredSet(filterId, typeFilteredSet, expr)

        if RESPONSE:
            RESPONSE.redirect(URL1+'/manage_workspace?'
            'manage_tabs_message=FilteredSet%20added')


    def manage_delFilteredSet(self, filterIds=[], URL1=None, \
            REQUEST=None,RESPONSE=None):
        """ delete a list of FilteredSets"""

        for filterId in filterIds:
            self.delFilteredSet(filterId)

        if RESPONSE:
            RESPONSE.redirect(URL1+'/manage_workspace?'
            'manage_tabs_message=FilteredSet(s)%20deleted')


    def manage_saveFilteredSet(self,filterId, expr, URL1=None,\
            REQUEST=None,RESPONSE=None):
        """ save expression for a FilteredSet """

        self.filteredSets[filterId].setExpression(expr)

        if RESPONSE:
            RESPONSE.redirect(URL1+'/manage_workspace?'
            'manage_tabs_message=FilteredSet(s)%20updated')

    def getIndexSourceNames(self):
        """ return names of indexed attributes """
        return ('n/a',)
    

    def manage_clearFilteredSet(self, filterIds=[], URL1=None, \
            REQUEST=None,RESPONSE=None):
        """  clear a list of FilteredSets"""

        for filterId in filterIds:
            self.clearFilteredSet(filterId)

        if RESPONSE:
            RESPONSE.redirect(URL1+'/manage_workspace?'
             'manage_tabs_message=FilteredSet(s)%20cleared')


    editFilteredSet = DTMLFile('dtml/editFilteredSet',globals())
    index_html      = DTMLFile('dtml/index', globals())


manage_addTopicIndexForm = DTMLFile('dtml/addTopicIndex', globals())

def manage_addTopicIndex(self, id, REQUEST=None, RESPONSE=None, URL3=None):
    """Add a TopicIndex"""
    return self.manage_addIndex(id, 'TopicIndex', extra=None, \
                REQUEST=REQUEST, RESPONSE=RESPONSE, URL1=URL3)
