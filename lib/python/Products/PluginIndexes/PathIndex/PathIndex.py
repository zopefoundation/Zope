##############################################################################
#
# Copyright (c) 2002 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Path index.

$Id$
"""

from logging import getLogger

from Globals import Persistent, DTMLFile
from OFS.SimpleItem import SimpleItem
from BTrees.IOBTree import IOBTree
from BTrees.OOBTree import OOBTree
from BTrees.IIBTree import IITreeSet, IISet, intersection, union, multiunion
from BTrees.Length import Length
from zope.interface import implements

from Products.PluginIndexes.common import safe_callable
from Products.PluginIndexes.common.util import parseIndexRequest
from Products.PluginIndexes.interfaces import IPathIndex
from Products.PluginIndexes.interfaces import IUniqueValueIndex

_marker = []
LOG = getLogger('Zope.PathIndex')


class PathIndex(Persistent, SimpleItem):

    """Index for paths returned by getPhysicalPath.

    A path index stores all path components of the physical path of an object.

    Internal datastructure:

    - a physical path of an object is split into its components

    - every component is kept as a  key of a OOBTree in self._indexes

    - the value is a mapping 'level of the path component' to
      'all docids with this path component on this level'
    """
    implements(IPathIndex, IUniqueValueIndex)

    meta_type="PathIndex"
    query_options = ('query', 'level', 'operator')

    manage_options= (
        {'label': 'Settings',
         'action': 'manage_main',
         'help': ('PathIndex','PathIndex_Settings.stx')},
    )

    def __init__(self,id,caller=None):
        self.id = id
        self.operators = ('or','and')
        self.useOperator = 'or'
        self.clear()

    def clear(self):
        self._depth = 0
        self._index = OOBTree()
        self._unindex = IOBTree()
        self._length = Length(0)

    def insertEntry(self, comp, id, level):
        """Insert an entry.

           comp is a path component
           id is the docid
           level is the level of the component inside the path
        """

        if not self._index.has_key(comp):
            self._index[comp] = IOBTree()

        if not self._index[comp].has_key(level):
            self._index[comp][level] = IITreeSet()

        self._index[comp][level].insert(id)
        if level > self._depth:
            self._depth = level

    def index_object(self, docid, obj ,threshold=100):
        """ hook for (Z)Catalog """

        f = getattr(obj, self.id, None)
        if f is not None:
            if safe_callable(f):
                try:
                    path = f()
                except AttributeError:
                    return 0
            else:
                path = f

            if not isinstance(path, (str, tuple)):
                raise TypeError('path value must be string or tuple of strings')
        else:
            try:
                path = obj.getPhysicalPath()
            except AttributeError:
                return 0

        if isinstance(path, (list, tuple)):
            path = '/'+ '/'.join(path[1:])
        comps = filter(None, path.split('/'))

        if not self._unindex.has_key(docid):
            self._length.change(1)

        for i in range(len(comps)):
            self.insertEntry(comps[i], docid, i)
        self._unindex[docid] = path
        return 1

    def unindex_object(self, docid):
        """ hook for (Z)Catalog """

        if not self._unindex.has_key(docid):
            LOG.debug('Attempt to unindex nonexistent document with id %s'
                      % docid)
            return

        comps =  self._unindex[docid].split('/')

        for level in range(len(comps[1:])):
            comp = comps[level+1]

            try:
                self._index[comp][level].remove(docid)

                if not self._index[comp][level]:
                    del self._index[comp][level]

                if not self._index[comp]:
                    del self._index[comp]
            except KeyError:
                LOG.debug('Attempt to unindex document with id %s failed'
                          % docid)

        self._length.change(-1)
        del self._unindex[docid]

    def search(self, path, default_level=0):
        """
        path is either a string representing a
        relative URL or a part of a relative URL or
        a tuple (path,level).

        level >= 0  starts searching at the given level
        level <  0  match at *any* level
        """
        if isinstance(path, str):
            level = default_level
        else:
            level = int(path[1])
            path  = path[0]
        
        if level < 0:
            # Search at every level, return the union of all results
            return multiunion(
                [self.search(path, level) 
                 for level in xrange(self._depth + 1)])

        comps = filter(None, path.split('/'))

        if len(comps) == 0:
            return IISet(self._unindex.keys())

        results = None
        for i, comp in enumerate(comps):
            if not self._index.get(comp, {}).has_key(level+i): return IISet()
            results = intersection(results, self._index[comp][level+i])
        return results

    def numObjects(self):
        """ return the number distinct values """
        return len(self._unindex)

    def indexSize(self):
        """ return the number of indexed objects"""
        return len(self)

    def __len__(self):
        return self._length()

    def _apply_index(self, request):
        """ hook for (Z)Catalog
            'request' --  mapping type (usually {"path": "..." }
             additionaly a parameter "path_level" might be passed
             to specify the level (see search())
        """
        record = parseIndexRequest(request, self.id, self.query_options)
        if record.keys is None:
            return None

        level    = record.get("level",0)
        operator = record.get('operator',self.useOperator).lower()

        # depending on the operator we use intersection of union
        if operator == "or":  set_func = union
        else: set_func = intersection

        res = None
        for k in record.keys:
            rows = self.search(k,level)
            res = set_func(res,rows)

        if res:
            return res, (self.id,)
        else:
            return IISet(), (self.id,)

    def hasUniqueValuesFor(self, name):
        """has unique values for column name"""
        return name == self.id

    def uniqueValues(self, name=None, withLength=0):
        """ needed to be consistent with the interface """
        return self._index.keys()

    def getIndexSourceNames(self):
        """ return names of indexed attributes """
        return ('getPhysicalPath', )

    def getEntryForObject(self, docid, default=_marker):
        """ Takes a document ID and returns all the information
            we have on that specific object.
        """
        try:
            return self._unindex[docid]
        except KeyError:
            # XXX Why is default ignored?
            return None

    manage = manage_main = DTMLFile('dtml/managePathIndex', globals())
    manage_main._setName('manage_main')


manage_addPathIndexForm = DTMLFile('dtml/addPathIndex', globals())

def manage_addPathIndex(self, id, REQUEST=None, RESPONSE=None, URL3=None):
    """Add a path index"""
    return self.manage_addIndex(id, 'PathIndex', extra=None, \
                REQUEST=REQUEST, RESPONSE=RESPONSE, URL1=URL3)
