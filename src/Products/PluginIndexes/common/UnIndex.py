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
"""Base for bi-directional indexes.

$Id$
"""
from cgi import escape
from logging import getLogger
import sys

from BTrees.IIBTree import intersection
from BTrees.IIBTree import IITreeSet
from BTrees.IIBTree import IISet
from BTrees.IIBTree import union
from BTrees.IOBTree import IOBTree
from BTrees.Length import Length
from BTrees.OOBTree import OOBTree
from OFS.SimpleItem import SimpleItem
from ZODB.POSException import ConflictError
from zope.interface import implements

from Products.PluginIndexes.common import safe_callable
from Products.PluginIndexes.common.util import parseIndexRequest
from Products.PluginIndexes.interfaces import IPluggableIndex
from Products.PluginIndexes.interfaces import ISortIndex
from Products.PluginIndexes.interfaces import IUniqueValueIndex

_marker = []
LOG = getLogger('Zope.UnIndex')


class UnIndex(SimpleItem):

    """Simple forward and reverse index.
    """
    implements(IPluggableIndex, IUniqueValueIndex, ISortIndex)

    def __init__(
        self, id, ignore_ex=None, call_methods=None, extra=None, caller=None):
        """Create an unindex

        UnIndexes are indexes that contain two index components, the
        forward index (like plain index objects) and an inverted
        index.  The inverted index is so that objects can be unindexed
        even when the old value of the object is not known.

        e.g.

        self._index = {datum:[documentId1, documentId2]}
        self._unindex = {documentId:datum}

        If any item in self._index has a length-one value, the value is an
        integer, and not a set.  There are special cases in the code to deal
        with this.

        The arguments are:

          'id' -- the name of the item attribute to index.  This is
          either an attribute name or a record key.

          'ignore_ex' -- should be set to true if you want the index
          to ignore exceptions raised while indexing instead of
          propagating them.

          'call_methods' -- should be set to true if you want the index
          to call the attribute 'id' (note: 'id' should be callable!)
          You will also need to pass in an object in the index and
          uninded methods for this to work.

          'extra' -- a mapping object that keeps additional
          index-related parameters - subitem 'indexed_attrs'
          can be string with comma separated attribute names or
          a list

          'caller' -- reference to the calling object (usually
          a (Z)Catalog instance
        """

        def _get(o, k, default):
            """ return a value for a given key of a dict/record 'o' """
            if isinstance(o, dict):
                return o.get(k, default)
            else:
                return getattr(o, k, default)

        self.id = id
        self.ignore_ex=ignore_ex        # currently unimplimented
        self.call_methods=call_methods

        self.operators = ('or', 'and')
        self.useOperator = 'or'

        # allow index to index multiple attributes
        ia = _get(extra, 'indexed_attrs', id)
        if isinstance(ia, str):
            self.indexed_attrs = ia.split(',')
        else:
            self.indexed_attrs = list(ia)
        self.indexed_attrs = [ attr.strip()
                               for attr in self.indexed_attrs if attr ]
        if not self.indexed_attrs:
            self.indexed_attrs = [id]

        self._length = Length()
        self.clear()

    def __len__(self):
        return self._length()

    def getId(self):
        return self.id

    def clear(self):
        self._length = Length()
        self._index = OOBTree()
        self._unindex = IOBTree()

    def __nonzero__(self):
        return not not self._unindex

    def histogram(self):
        """Return a mapping which provides a histogram of the number of
        elements found at each point in the index.
        """
        histogram = {}
        for item in self._index.items():
            if isinstance(item,int):
                entry = 1 # "set" length is 1
            else:
                key, value = item
                entry = len(value)
            histogram[entry] = histogram.get(entry, 0) + 1

        return histogram

    def referencedObjects(self):
        """Generate a list of IDs for which we have referenced objects."""
        return self._unindex.keys()

    def getEntryForObject(self, documentId, default=_marker):
        """Takes a document ID and returns all the information we have
        on that specific object.
        """
        if default is _marker:
            return self._unindex.get(documentId)
        else:
            return self._unindex.get(documentId, default)

    def removeForwardIndexEntry(self, entry, documentId):
        """Take the entry provided and remove any reference to documentId
        in its entry in the index.
        """
        indexRow = self._index.get(entry, _marker)
        if indexRow is not _marker:
            try:
                indexRow.remove(documentId)
                if not indexRow:
                    del self._index[entry]
                    self._length.change(-1)

            except ConflictError:
                raise

            except AttributeError:
                # index row is an int
                try:
                    del self._index[entry]
                except KeyError:
                    # XXX swallow KeyError because it was probably
                    # removed and then _length AttributeError raised
                    pass 
                if isinstance(self.__len__, Length):
                    self._length = self.__len__
                    del self.__len__ 
                self._length.change(-1)

            except:
                LOG.error('%s: unindex_object could not remove '
                          'documentId %s from index %s.  This '
                          'should not happen.' % (self.__class__.__name__,
                           str(documentId), str(self.id)),
                           exc_info=sys.exc_info())
        else:
            LOG.error('%s: unindex_object tried to retrieve set %s '
                      'from index %s but couldn\'t.  This '
                      'should not happen.' % (self.__class__.__name__,
                      repr(entry), str(self.id)))

    def insertForwardIndexEntry(self, entry, documentId):
        """Take the entry provided and put it in the correct place
        in the forward index.

        This will also deal with creating the entire row if necessary.
        """
        indexRow = self._index.get(entry, _marker)

        # Make sure there's actually a row there already.  If not, create
        # an IntSet and stuff it in first.
        if indexRow is _marker:
            self._index[entry] = documentId
            # XXX _length needs to be migrated to Length object
            try:
                self._length.change(1)
            except AttributeError:
                if isinstance(self.__len__, Length):
                    self._length = self.__len__
                    del self.__len__
                self._length.change(1)
        else:
            try: indexRow.insert(documentId)
            except AttributeError:
                # index row is an int
                indexRow=IITreeSet((indexRow, documentId))
                self._index[entry] = indexRow

    def index_object(self, documentId, obj, threshold=None):
        """ wrapper to handle indexing of multiple attributes """

        fields = self.getIndexSourceNames()

        res = 0
        for attr in fields:
            res += self._index_object(documentId, obj, threshold, attr)

        return res > 0

    def _index_object(self, documentId, obj, threshold=None, attr=''):
        """ index and object 'obj' with integer id 'documentId'"""
        returnStatus = 0

        # First we need to see if there's anything interesting to look at
        datum = self._get_object_datum(obj, attr)

        # We don't want to do anything that we don't have to here, so we'll
        # check to see if the new and existing information is the same.
        oldDatum = self._unindex.get(documentId, _marker)
        if datum != oldDatum:
            if oldDatum is not _marker:
                self.removeForwardIndexEntry(oldDatum, documentId)
                if datum is _marker:
                    try:
                        del self._unindex[documentId]
                    except ConflictError:
                        raise
                    except:
                        LOG.error('Should not happen: oldDatum was there, now its not,'
                                  'for document with id %s' % documentId)

            if datum is not _marker:
                self.insertForwardIndexEntry(datum, documentId)
                self._unindex[documentId] = datum

            returnStatus = 1

        return returnStatus

    def _get_object_datum(self,obj, attr):
        # self.id is the name of the index, which is also the name of the
        # attribute we're interested in.  If the attribute is callable,
        # we'll do so.
        try:
            datum = getattr(obj, attr)
            if safe_callable(datum):
                datum = datum()
        except (AttributeError, TypeError):
            datum = _marker
        return datum

    def numObjects(self):
        """Return the number of indexed objects."""
        return len(self._unindex)

    def indexSize(self):
        """Return the size of the index in terms of distinct values."""
        return len(self)

    def unindex_object(self, documentId):
        """ Unindex the object with integer id 'documentId' and don't
        raise an exception if we fail
        """
        unindexRecord = self._unindex.get(documentId, _marker)
        if unindexRecord is _marker:
            return None

        self.removeForwardIndexEntry(unindexRecord, documentId)

        try:
            del self._unindex[documentId]
        except ConflictError:
            raise
        except:
            LOG.debug('Attempt to unindex nonexistent document'
                      ' with id %s' % documentId,exc_info=True)

    def _apply_index(self, request):
        """Apply the index to query parameters given in the request arg.

        The request argument should be a mapping object.

        If the request does not have a key which matches the "id" of
        the index instance, then None is returned.

        If the request *does* have a key which matches the "id" of
        the index instance, one of a few things can happen:

          - if the value is a blank string, None is returned (in
            order to support requests from web forms where
            you can't tell a blank string from empty).

          - if the value is a nonblank string, turn the value into
            a single-element sequence, and proceed.

          - if the value is a sequence, return a union search.

        If the request contains a parameter with the name of the
        column + '_usage', it is sniffed for information on how to
        handle applying the index.

        If the request contains a parameter with the name of the
        column = '_operator' this overrides the default method
        ('or') to combine search results. Valid values are "or"
        and "and".

        If None is not returned as a result of the abovementioned
        constraints, two objects are returned.  The first object is a
        ResultSet containing the record numbers of the matching
        records.  The second object is a tuple containing the names of
        all data fields used.

        FAQ answer:  to search a Field Index for documents that
        have a blank string as their value, wrap the request value
        up in a tuple ala: request = {'id':('',)}
        """
        record = parseIndexRequest(request, self.id, self.query_options)
        if record.keys is None:
            return None

        index = self._index
        r     = None
        opr   = None

        # experimental code for specifing the operator
        operator = record.get('operator',self.useOperator)
        if not operator in self.operators :
            raise RuntimeError,"operator not valid: %s" % escape(operator)

        # depending on the operator we use intersection or union
        if operator=="or":  set_func = union
        else:               set_func = intersection

        # Range parameter
        range_parm = record.get('range',None)
        if range_parm:
            opr = "range"
            opr_args = []
            if range_parm.find("min")>-1:
                opr_args.append("min")
            if range_parm.find("max")>-1:
                opr_args.append("max")

        if record.get('usage',None):
            # see if any usage params are sent to field
            opr = record.usage.lower().split(':')
            opr, opr_args=opr[0], opr[1:]

        if opr=="range":   # range search
            if 'min' in opr_args: lo = min(record.keys)
            else: lo = None
            if 'max' in opr_args: hi = max(record.keys)
            else: hi = None
            if hi:
                setlist = index.items(lo,hi)
            else:
                setlist = index.items(lo)

            for k, set in setlist:
                if isinstance(set, int):
                    set = IISet((set,))
                r = set_func(r, set)
        else: # not a range search
            for key in record.keys:
                set=index.get(key, None)
                if set is None:
                    set = IISet(())
                elif isinstance(set, int):
                    set = IISet((set,))
                r = set_func(r, set)

        if isinstance(r, int):  r=IISet((r,))
        if r is None:
            return IISet(), (self.id,)
        else:
            return r, (self.id,)

    def hasUniqueValuesFor(self, name):
        """has unique values for column name"""
        if name == self.id:
            return 1
        else:
            return 0

    def getIndexSourceNames(self):
        """ return sequence of indexed attributes """
        # BBB:  older indexes didn't have 'indexed_attrs'
        return getattr(self, 'indexed_attrs', [self.id])

    def uniqueValues(self, name=None, withLengths=0):
        """returns the unique values for name

        if withLengths is true, returns a sequence of
        tuples of (value, length)
        """
        if name is None:
            name = self.id
        elif name != self.id:
            return []

        if not withLengths:
            return tuple(self._index.keys())
        else:
            rl=[]
            for i in self._index.keys():
                set = self._index[i]
                if isinstance(set, int):
                    l = 1
                else:
                    l = len(set)
                rl.append((i, l))
            return tuple(rl)

    def keyForDocument(self, id):
        # This method is superceded by documentToKeyMap
        return self._unindex[id]

    def documentToKeyMap(self):
        return self._unindex

    def items(self):
        items = []
        for k,v in self._index.items():
            if isinstance(v, int):
                v = IISet((v,))
            items.append((k, v))
        return items
