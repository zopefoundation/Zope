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

"""Simple column indices"""
__version__='$Revision: 1.30 $'[11:-2]

from Persistence import Persistent
from BTrees.OOBTree import OOBTree
from BTrees.IIBTree import IITreeSet
import operator
from Missing import MV
import string

ListType=type([])
StringType=type('s')


def nonEmpty(s):
    "returns true if a non-empty string or any other (nonstring) type"
    if type(s) is StringType:
        if s: return 1
        else: return 0
    else:
        return 1


class Index(Persistent):
    """Index object interface"""

    def __init__(self, data=None, schema=None, id=None,
                 ignore_ex=None, call_methods=None):
        """Create an index

        The arguments are:

          'data' -- a mapping from integer object ids to objects or
          records,

          'schema' -- a mapping from item name to index into data
          records.  If 'data' is a mapping to objects, then schema
          should ne 'None'.

          'id' -- the name of the item attribute to index.  This is
          either an attribute name or a record key.

        """
        ######################################################################
        # For b/w compatability, have to allow __init__ calls with zero args

        if not data==schema==id==ignore_ex==call_methods==None:
            self._data = data
            self._schema = schema
            self.id = id
            self.ignore_ex=ignore_ex
            self.call_methods=call_methods
            self._index = OOBTree()

            self._reindex()
        else:
            pass

    # for b/w compatability
    _init = __init__


    def dpHasUniqueValuesFor(self, name):
        ' has unique values for column NAME '
        if name == self.id:
            return 1
        else:
            return 0


    def dpUniqueValues(self, name=None, withLengths=0):
        """\
        returns the unique values for name

        if withLengths is true, returns a sequence of
        tuples of (value, length)
        """
        if name is None:
            name = self.id
        elif name != self.id:
            return []
        if not withLengths: return tuple(
            filter(nonEmpty,self._index.keys())
            )
        else:
            rl=[]
            for i in self._index.keys():
                if not nonEmpty(i): continue
                else: rl.append((i, len(self._index[i])))
            return tuple(rl)


    def clear(self):
        self._index = OOBTree()


    def _reindex(self, start=0):
        """Recompute index data for data with ids >= start."""

        index=self._index
        get=index.get

        if not start: index.clear()

        id = self.id
        if self._schema is None:
            f=getattr
        else:
            f = operator.__getitem__
            id = self._schema[id]

        for i,row in self._data.items(start):
            k=f(row,id)

            if k is None or k == MV: continue

            set=get(k)
            if set is None: index[k] = set = IITreeSet()
            set.insert(i)


    def index_item(self, i, obj=None):
        """Recompute index data for data with ids >= start."""
        index = self._index
        id = self.id
        if (self._schema is None) or (obj is not None):
            f = getattr
        else:
            f = operator.__getitem__
            id = self._schema[id]

        if obj is None:
            obj = self._data[i]

        try:    k=f(obj, id)
        except: return
        if self.call_methods:
            k=k()
        if k is None or k == MV:
            return

        set = index.get(k)
        if set is None: index[k] = set = IITreeSet()
        set.insert(i)


    def unindex_item(self, i, obj=None):
        """Recompute index data for data with ids >= start."""
        index = self._index
        id = self.id
        if self._schema is None:
            f = getattr
        else:
            f = operator.__getitem__
            id = self._schema[id]
        if obj is None:
            obj = self._data[i]

        try:    k=f(obj, id)
        except: return
        if self.call_methods:
            k=k()
        if k is None or k == MV:
            return

        set = index.get(k)
        if set is not None: set.remove(i)


    def _apply_index(self, request, cid=''):
        """Apply the index to query parameters given in the argument,
        request

        The argument should be a mapping object.

        If the request does not contain the needed parameters, then
        None is returned.

        If the request contains a parameter with the name of the
        column + '_usage', it is sniffed for information on how to
        handle applying the index.

        Otherwise two objects are returned.  The first object is a
        ResultSet containing the record numbers of the matching
        records.  The second object is a tuple containing the names of
        all data fields used.

        """
        id = self.id              #name of the column

        cidid = "%s/%s" % (cid,id)
        has_key = request.has_key
        if has_key(cidid): keys = request[cidid]
        elif has_key(id): keys = request[id]
        else: return None

        if type(keys) is not ListType: keys=[keys]
        index = self._index
        r = None
        anyTrue = 0
        opr = None

        if request.has_key(id+'_usage'):
            # see if any usage params are sent to field
            opr=string.split(string.lower(request[id+"_usage"]),':')
            opr, opr_args=opr[0], opr[1:]

        if opr=="range":
            if 'min' in opr_args: lo = min(keys)
            else: lo = None
            if 'max' in opr_args: hi = max(keys)
            else: hi = None

            anyTrue=1
            try:
                if hi: setlist = index.items(lo,hi)
                else:  setlist = index.items(lo)
                for k,set in setlist:
                    w, r = weightedUnion(r, set)
            except KeyError: pass
        else:           #not a range
            get = index.get
            for key in keys:
                if key: anyTrue = 1
                set=get(key)
                if set is not None:
                    w, r = weightedUnion(r, set)

        if r is None:
            if anyTrue: r=IISet()
            else: return None

        return r, (id,)
