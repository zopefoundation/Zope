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

__version__ = '$Id$'

from types import StringType, ListType, TupleType
from logging import getLogger

from Globals import Persistent, DTMLFile
from OFS.SimpleItem import SimpleItem
from BTrees.IOBTree import IOBTree
from BTrees.OOBTree import OOBTree
from BTrees.IIBTree import IITreeSet, IISet, intersection, union
from BTrees.Length import Length

from Products.PluginIndexes import PluggableIndex
from Products.PluginIndexes.common.util import parseIndexRequest
from Products.PluginIndexes.common import safe_callable

_marker = []
LOG = getLogger('Zope.PathIndex')

class PathIndex(Persistent, SimpleItem):
    """ A path index stores all path components of the physical
    path of an object:

    Internal datastructure:

    - a physical path of an object is split into its components

    - every component is kept as a  key of a OOBTree in self._indexes

    - the value is a mapping 'level of the path component' to
      'all docids with this path component on this level'

    """

    __implements__ = (PluggableIndex.UniqueValueIndex,)

    meta_type="PathIndex"

    manage_options= (
        {'label': 'Settings',
         'action': 'manage_main',
         'help': ('PathIndex','PathIndex_Settings.stx')},
    )

    query_options = ("query", "level", "operator", "depth", "navtree")

    def ___init__(self,id,caller=None):
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


    def numObjects(self):
        """ return the number distinct values """
        return len(self._unindex)

    def indexSize(self):
        """ return the number of indexed objects"""
        return len(self)

    def __len__(self):
        return self._length()

    def hasUniqueValuesFor(self, name):
        """has unique values for column name"""
        return name == self.id

    def uniqueValues(self, name=None, withLength=0):
        """ needed to be consistent with the interface """
        return self._index.keys()

    def getEntryForObject(self, docid, default=_marker):
        """ Takes a document ID and returns all the information 
            we have on that specific object. 
        """
        try:
            return self._unindex[docid]
        except KeyError:
            # XXX Why is default ignored?
            return None






    def __init__(self, id, extra=None, caller=None):
        """ ExtendedPathIndex supports indexed_attrs """
        self.___init__( id, caller)

        def get(o, k, default):
            if isinstance(o, dict):
                return o.get(k, default)
            else:
                return getattr(o, k, default)

        attrs = get(extra, 'indexed_attrs', None)
        if attrs is None:
            return
        if isinstance(attrs, str):
            attrs = attrs.split(',')
        attrs = filter(None, [a.strip() for a in attrs])

        if attrs:
            # We only index the first attribute so snip off the rest
            self.indexed_attrs = tuple(attrs[:1])

    def index_object(self, docid, obj ,threshold=100):
        """ hook for (Z)Catalog """

        # PathIndex first checks for an attribute matching its id and
        # falls back to getPhysicalPath only when failing to get one.
        # The presence of 'indexed_attrs' overrides this behavior and
        # causes indexing of the custom attribute.

        attrs = getattr(self, 'indexed_attrs', None)
        if attrs:
            index = attrs[0]
        else:
            index = self.id

        f = getattr(obj, index, None)
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

        # Make sure we reindex properly when path change
        if self._unindex.has_key(docid) and self._unindex.get(docid) != path:
            self.unindex_object(docid)

        if not self._unindex.has_key(docid):
            if hasattr(self, '_migrate_length'):
                self._migrate_length()
            self._length.change(1)

        for i in range(len(comps)):
            self.insertEntry(comps[i], docid, i)

        # Add terminator
        self.insertEntry(None, docid, len(comps)-1)

        self._unindex[docid] = path
        return 1

    def unindex_object(self, docid):
        """ hook for (Z)Catalog """

        if not self._unindex.has_key(docid):
            LOG.error('Attempt to unindex nonexistent document'
                     ' with id %s' % docid)
            return

        # There is an assumption that paths start with /
        path = self._unindex[docid]
        if not path.startswith('/'):
            path = '/'+path
        comps =  path.split('/')

        def unindex(comp, level, docid=docid):
            try:
                self._index[comp][level].remove(docid)

                if not self._index[comp][level]:
                    del self._index[comp][level]

                if not self._index[comp]:
                    del self._index[comp]
            except KeyError:
                LOG.error('Attempt to unindex document'
                          ' with id %s failed' % docid)
                return

        for level in range(len(comps[1:])):
            comp = comps[level+1]
            unindex(comp, level)

        # Remove the terminator
        level = len(comps[1:])
        comp = None
        unindex(comp, level-1)

        if hasattr(self, '_migrate_length'):
            self._migrate_length()
                
        self._length.change(-1)
        del self._unindex[docid]

    def search(self, path, default_level=0, depth=-1, navtree=0):
        """
        path is either a string representing a
        relative URL or a part of a relative URL or
        a tuple (path,level).

        level >= 0  starts searching at the given level
        level <  0  not implemented yet
        """

        if isinstance(path, str):
            startlevel = default_level
        else:
            startlevel = int(path[1])
            path  = path[0]

        comps = filter(None, path.split('/'))

        # Make sure that we get depth = 1 if in navtree mode
        # unless specified otherwise

        if depth == -1:
            depth = 0 or navtree

        if len(comps) == 0:
            if not depth and not navtree:
                return IISet(self._unindex.keys())

        if startlevel >= 0:

            pathset = None # Same as pathindex
            navset  = None # For collecting siblings along the way
            depthset = None # For limiting depth

            if navtree and depth and \
                   self._index.has_key(None) and \
                   self._index[None].has_key(startlevel):
                navset = self._index[None][startlevel]

            for level in range(startlevel, startlevel+len(comps) + depth):
                if level-startlevel < len(comps):
                    comp = comps[level-startlevel]
                    if not self._index.has_key(comp) or not self._index[comp].has_key(level): 
                        # Navtree is inverse, keep going even for nonexisting paths
                        if navtree:
                            pathset = IISet()
                        else:
                            return IISet()
                    else:
                        pathset = intersection(pathset, self._index[comp][level])
                    if navtree and depth and \
                           self._index.has_key(None) and \
                           self._index[None].has_key(level+depth):
                        navset  = union(navset, intersection(pathset, self._index[None][level+depth]))
                if level-startlevel >= len(comps) or navtree:
                    if self._index.has_key(None) and self._index[None].has_key(level):
                        depthset = union(depthset, intersection(pathset, self._index[None][level]))

            if navtree:
                return union(depthset, navset) or IISet()
            else:
                return intersection(pathset,depthset) or IISet()

        else:
            results = IISet()
            for level in range(0,self._depth + 1):
                ids = None
                error = 0
                for cn in range(0,len(comps)):
                    comp = comps[cn]
                    try:
                        ids = intersection(ids,self._index[comp][level+cn])
                    except KeyError:
                        error = 1
                if error==0:
                    results = union(results,ids)
            return results

    def _apply_index(self, request, cid=''):
        """ hook for (Z)Catalog
            'request' --  mapping type (usually {"path": "..." }
             additionaly a parameter "path_level" might be passed
             to specify the level (see search())

            'cid' -- ???
        """

        record = parseIndexRequest(request,self.id,self.query_options)
        if record.keys==None: return None

        level    = record.get("level",0)
        operator = record.get('operator',self.useOperator).lower()
        depth    = getattr(record, 'depth',-1) # Set to 0 or navtree in search - use getattr to get 0 value
        navtree  = record.get('navtree',0)

        # depending on the operator we use intersection of union
        if operator == "or":  set_func = union
        else: set_func = intersection

        res = None
        for k in record.keys:
            rows = self.search(k,level, depth, navtree)
            res = set_func(res,rows)

        if res:
            return res, (self.id,)
        else:
            return IISet(), (self.id,)

    def getIndexSourceNames(self):
        """ return names of indexed attributes """

        # By default PathIndex advertises getPhysicalPath even
        # though the logic in index_object is different.

        try:
            return tuple(self.indexed_attrs)
        except AttributeError:
            return ('getPhysicalPath',)


    index_html = DTMLFile('dtml/index', globals())
    manage_workspace = DTMLFile('dtml/managePathIndex', globals())

manage_addPathIndexForm = DTMLFile('dtml/addPathIndex', globals())

def manage_addPathIndex(self, id, REQUEST=None, RESPONSE=None, URL3=None):
    """Add a path index"""
    return self.manage_addIndex(id, 'PathIndex', extra=None, \
                REQUEST=REQUEST, RESPONSE=RESPONSE, URL1=URL3)
