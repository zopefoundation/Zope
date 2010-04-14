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
"""Path index.
"""

from logging import getLogger

from App.special_dtml import DTMLFile
from OFS.SimpleItem import SimpleItem
from BTrees.IIBTree import IITreeSet
from BTrees.IIBTree import IISet
from BTrees.IIBTree import intersection
from BTrees.IIBTree import multiunion
from BTrees.IIBTree import union
from BTrees.IOBTree import IOBTree
from BTrees.OOBTree import OOBTree
from BTrees.Length import Length
from Persistence import Persistent
from zope.interface import implements

from Products.PluginIndexes.common import safe_callable
from Products.PluginIndexes.common.util import parseIndexRequest
from Products.PluginIndexes.interfaces import IPathIndex
from Products.PluginIndexes.interfaces import ISortIndex
from Products.PluginIndexes.interfaces import IUniqueValueIndex

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
    implements(IPathIndex, IUniqueValueIndex, ISortIndex)

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

    def __len__(self):
        return self._length()

    # IPluggableIndex implementation

    def getEntryForObject(self, docid, default=None):
        """ See IPluggableIndex.
        """
        try:
            return self._unindex[docid]
        except KeyError:
            return default

    def getIndexSourceNames(self):
        """ See IPluggableIndex.
        """
        return (self.id, 'getPhysicalPath', )

    def index_object(self, docid, obj ,threshold=100):
        """ See IPluggableIndex.
        """
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
        """ See IPluggableIndex.
        """
        if docid not in self._unindex:
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

    def _apply_index(self, request):
        """ See IPluggableIndex.

        o Unpacks args from catalog and mapps onto '_search'.
        """
        record = parseIndexRequest(request, self.id, self.query_options)
        if record.keys is None:
            return None

        level = record.get("level", 0)
        operator = record.get('operator', self.useOperator).lower()

        # depending on the operator we use intersection of union
        if operator == "or":
            set_func = union
        else:
            set_func = intersection

        res = None
        for k in record.keys:
            rows = self._search(k,level)
            res = set_func(res,rows)

        if res:
            return res, (self.id,)
        else:
            return IISet(), (self.id,)

    def numObjects(self):
        """ See IPluggableIndex.
        """
        return len(self._unindex)

    def indexSize(self):
        """ See IPluggableIndex.
        """
        return len(self)

    def clear(self):
        """ See IPluggableIndex.
        """
        self._depth = 0
        self._index = OOBTree()
        self._unindex = IOBTree()
        self._length = Length(0)

    # IUniqueValueIndex implementation

    def hasUniqueValuesFor(self, name):
        """ See IUniqueValueIndex.
        """
        return name == self.id

    def uniqueValues(self, name=None, withLength=0):
        """  See IUniqueValueIndex.
        """
        if name in (None, self.id, 'getPhysicalPath'):
            if withLength:
                for key in self._index:
                    yield key, len(self._search(key, -1))
            else:
                for key in self._index.keys():
                    yield key

    # ISortIndex implementation

    def keyForDocument(self, documentId):
        """ See ISortIndex.
        """
        return self._unindex.get(documentId)

    def documentToKeyMap(self):
        """ See ISortIndex.
        """
        return self._unindex

    # IPathIndex implementation.

    def insertEntry(self, comp, id, level):
        """ See IPathIndex
        """
        if not self._index.has_key(comp):
            self._index[comp] = IOBTree()

        if not self._index[comp].has_key(level):
            self._index[comp][level] = IITreeSet()

        self._index[comp][level].insert(id)
        if level > self._depth:
            self._depth = level

    # Helper methods

    def _search(self, path, default_level=0):
        """ Perform the actual search.

        ``path``
            a string representing a relative URL, or a part of a relative URL,
            or a tuple ``(path, level)``.  In the first two cases, use
            ``default_level`` as the level for the search.

        ``default_level``
            the level to use for non-tuple queries.

        ``level >= 0`` =>  match ``path`` only at the given level.

        ``level <  0`` =>  match ``path`` at *any* level
        """
        if isinstance(path, str):
            level = default_level
        else:
            level = int(path[1])
            path  = path[0]
        
        if level < 0:
            # Search at every level, return the union of all results
            return multiunion(
                [self._search(path, level) 
                 for level in xrange(self._depth + 1)])

        comps = filter(None, path.split('/'))
        
        if level + len(comps) - 1 > self._depth:
            # Our search is for a path longer than anything in the index
            return IISet()

        if len(comps) == 0:
            return IISet(self._unindex.keys())

        results = None
        for i, comp in reversed(list(enumerate(comps))):
            if not self._index.get(comp, {}).has_key(level+i): return IISet()
            results = intersection(results, self._index[comp][level+i])
        return results

    manage = manage_main = DTMLFile('dtml/managePathIndex', globals())
    manage_main._setName('manage_main')


manage_addPathIndexForm = DTMLFile('dtml/addPathIndex', globals())

def manage_addPathIndex(self, id, REQUEST=None, RESPONSE=None, URL3=None):
    """Add a path index"""
    return self.manage_addIndex(id, 'PathIndex', extra=None, \
                REQUEST=REQUEST, RESPONSE=RESPONSE, URL1=URL3)
