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

from logging import getLogger

from App.special_dtml import DTMLFile
from BTrees.IIBTree import IIBTree, IITreeSet, IISet
from BTrees.IIBTree import union, intersection, difference
import BTrees.Length
from ZODB.POSException import ConflictError

from Products.PluginIndexes.common.util import parseIndexRequest
from Products.PluginIndexes.common.UnIndex import UnIndex

_marker = object()
LOG = getLogger('BooleanIndex.UnIndex')


class BooleanIndex(UnIndex):
    """Index for booleans

       self._index = set([documentId1, documentId2])
       self._unindex = {documentId:[True/False]}

       False doesn't have actual entries in _index.
    """

    meta_type = "BooleanIndex"

    manage_options= (
        {'label': 'Settings',
         'action': 'manage_main'},
        {'label': 'Browse',
         'action': 'manage_browse'},
    )

    query_options = ["query"]

    manage = manage_main = DTMLFile('dtml/manageBooleanIndex', globals())
    manage_main._setName('manage_main')
    manage_browse = DTMLFile('../dtml/browseIndex', globals())

    def clear(self):
        self._length = BTrees.Length.Length()
        self._index = IITreeSet()
        self._unindex = IIBTree()

    def insertForwardIndexEntry(self, entry, documentId):
        """If True, insert directly into treeset
        """
        if entry:
            self._index.insert(documentId)
            self._length.change(1)

    def removeForwardIndexEntry(self, entry, documentId):
        """Take the entry provided and remove any reference to documentId
        in its entry in the index.
        """
        try:
            if entry:
                self._index.remove(documentId)
                self._length.change(-1)
        except ConflictError:
            raise
        except Exception:
            LOG.exception('%s: unindex_object could not remove '
                          'documentId %s from index %s. This '
                          'should not happen.' % (self.__class__.__name__,
                          str(documentId), str(self.id)))

    def _index_object(self, documentId, obj, threshold=None, attr=''):
        """ index and object 'obj' with integer id 'documentId'"""
        returnStatus = 0

        # First we need to see if there's anything interesting to look at
        datum = self._get_object_datum(obj, attr)

        # Make it boolean, int as an optimization
        datum = int(bool(datum))

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
                    except Exception:
                        LOG.error('Should not happen: oldDatum was there, now '
                                  'its not, for document with id %s' %
                                  documentId)

            if datum is not _marker:
                if datum:
                    self.insertForwardIndexEntry(datum, documentId)
                self._unindex[documentId] = datum

            returnStatus = 1

        return returnStatus

    def _apply_index(self, request, resultset=None):
        record = parseIndexRequest(request, self.id, self.query_options)
        if record.keys is None:
            return None

        index = self._index

        for key in record.keys:
            if key:
                # If True, check index
                return (intersection(index, resultset), (self.id, ))
            else:
                # Otherwise, remove from resultset or _unindex
                if resultset is None:
                    return (union(difference(self._unindex, index), IISet([])),
                            (self.id, ))
                else:
                    return (difference(resultset, index), (self.id, ))
        return (IISet(), (self.id, ))

    def indexSize(self):
        """Return distinct values, as an optimization we always claim 2."""
        return 2

    def items(self):
        items = []
        for v, k in self._unindex.items():
            if isinstance(v, int):
                v = IISet((v, ))
            items.append((k, v))
        return items

manage_addBooleanIndexForm = DTMLFile('dtml/addBooleanIndex', globals())


def manage_addBooleanIndex(self, id, extra=None,
                REQUEST=None, RESPONSE=None, URL3=None):
    """Add a boolean index"""
    return self.manage_addIndex(id, 'BooleanIndex', extra=extra, \
             REQUEST=REQUEST, RESPONSE=RESPONSE, URL1=URL3)
