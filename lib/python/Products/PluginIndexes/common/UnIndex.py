##############################################################################
# 
# Zope Public License (ZPL) Version 1.0
# -------------------------------------
# 
# Copyright (c) Digital Creations.  All rights reserved.
# 
# This license has been certified as Open Source(tm).
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
# 
# 1. Redistributions in source code must retain the above copyright
#    notice, this list of conditions, and the following disclaimer.
# 
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions, and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
# 
# 3. Digital Creations requests that attribution be given to Zope
#    in any manner possible. Zope includes a "Powered by Zope"
#    button that is installed by default. While it is not a license
#    violation to remove this button, it is requested that the
#    attribution remain. A significant investment has been put
#    into Zope, and this effort will continue if the Zope community
#    continues to grow. This is one way to assure that growth.
# 
# 4. All advertising materials and documentation mentioning
#    features derived from or use of this software must display
#    the following acknowledgement:
# 
#      "This product includes software developed by Digital Creations
#      for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
#    In the event that the product being advertised includes an
#    intact Zope distribution (with copyright and license included)
#    then this clause is waived.
# 
# 5. Names associated with Zope or Digital Creations must not be used to
#    endorse or promote products derived from this software without
#    prior written permission from Digital Creations.
# 
# 6. Modified redistributions of any form whatsoever must retain
#    the following acknowledgment:
# 
#      "This product includes software developed by Digital Creations
#      for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
#    Intact (re-)distributions of any official Zope release do not
#    require an external acknowledgement.
# 
# 7. Modifications are encouraged but must be packaged separately as
#    patches to official Zope releases.  Distributions that do not
#    clearly separate the patches from the original work must be clearly
#    labeled as unofficial distributions.  Modifications which do not
#    carry the name Zope may be packaged in any form, as long as they
#    conform to all of the clauses above.
# 
# 
# Disclaimer
# 
#   THIS SOFTWARE IS PROVIDED BY DIGITAL CREATIONS ``AS IS'' AND ANY
#   EXPRESSED OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
#   IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
#   PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL DIGITAL CREATIONS OR ITS
#   CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
#   SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
#   LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF
#   USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#   ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
#   OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT
#   OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
#   SUCH DAMAGE.
# 
# 
# This software consists of contributions made by Digital Creations and
# many individuals on behalf of Digital Creations.  Specific
# attributions are listed in the accompanying credits file.
# 
##############################################################################

"""Simple column indices"""

__version__='$Revision: 1.5 $'[11:-2]

from Globals import Persistent
from Acquisition import Implicit
import BTree
import IOBTree
import string
from zLOG import LOG, ERROR
from types import StringType, ListType, IntType, TupleType

from BTrees.OOBTree import OOBTree, OOSet
from BTrees.IOBTree import IOBTree
from BTrees.IIBTree import IITreeSet, IISet, union, intersection
import BTrees.Length

from Products.PluginIndexes.common.util import parseIndexRequest
import sys

_marker = []

class UnIndex(Persistent, Implicit):
    """UnIndex object interface"""


    def __init__(self, id, ignore_ex=None, call_methods=None):
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

        """

        self.id = id
        self.ignore_ex=ignore_ex        # currently unimplimented
        self.call_methods=call_methods

        # experimental code for specifing the operator
        self.operators = ['or','and'] 
        self.useOperator = 'or'

        self.__len__=BTrees.Length.Length() # see __len__ method docstring
        self.clear()

    def clear(self):
        # inplace opportunistic conversion from old-style to new style BTrees
        try: self.__len__.set(0)
        except AttributeError: self.__len__=BTrees.Length.Length()
        self._index = OOBTree()
        self._unindex = IOBTree()

    def _convertBTrees(self, threshold=200):
        if type(self._index) is OOBTree: return

        from BTrees.convert import convert

        _index=self._index
        self._index=OOBTree()
        
        def convertSet(s,
                       IITreeSet=IITreeSet, IntType=type(0),
                       type=type, len=len,
                       doneTypes = (IntType, IITreeSet)):

            if type(s) in doneTypes: return s

            if len(s) == 1:
                try: return s[0]  # convert to int
                except: pass # This is just an optimization.

            return IITreeSet(s)
    
        convert(_index, self._index, threshold, convertSet)

        _unindex=self._unindex
        self._unindex=IOBTree()
        convert(_unindex, self._unindex, threshold)

        self.__len__=BTrees.Length.Length(len(_index))

    def __nonzero__(self):
        return not not self._unindex

    def __len__(self):
        """Return the number of objects indexed.

        This method is only called for indexes which have "old" BTrees,
        and the *only* reason that UnIndexes maintain a __len__ is for
        the searching code in the catalog during sorting.
        """
        return len(self._unindex)

    def histogram(self):
        """Return a mapping which provides a histogram of the number of
        elements found at each point in the index."""

        histogram = {}
        for item in self._index.items():
            if type(item) is IntType:
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
        on that specific object."""
        if default is _marker:
            return self._unindex.get(documentId)
        else:
            return self._unindex.get(documentId, default)
            
        
    def removeForwardIndexEntry(self, entry, documentId):
        """Take the entry provided and remove any reference to documentId
        in its entry in the index."""
        global _marker
        indexRow = self._index.get(entry, _marker)
        if indexRow is not _marker:
            try:
                indexRow.remove(documentId)
                if not indexRow:
                    del self._index[entry]
                    try: self.__len__.change(-1)
                    except AttributeError: pass # pre-BTrees-module instance
            except AttributeError:
                # index row is an int
                del self._index[entry]
                try: self.__len__.change(-1)
                except AttributeError: pass # pre-BTrees-module instance   
            except:
                LOG(self.__class__.__name__, ERROR,
                    ('unindex_object could not remove '
                     'documentId %s from index %s.  This '
                     'should not happen.'
                     % (str(documentId), str(self.id))), '',
                    sys.exc_info())
        else:
            LOG(self.__class__.__name__, ERROR,
                ('unindex_object tried to retrieve set %s '
                 'from index %s but couldn\'t.  This '
                 'should not happen.' % (repr(entry), str(self.id))))

        
    def insertForwardIndexEntry(self, entry, documentId):
        """Take the entry provided and put it in the correct place
        in the forward index.

        This will also deal with creating the entire row if necessary."""
        global _marker
        indexRow = self._index.get(entry, _marker)
        
        # Make sure there's actually a row there already.  If not, create
        # an IntSet and stuff it in first.
        if indexRow is _marker:
            self._index[entry] = documentId
            try:  self.__len__.change(1)
            except AttributeError: pass # pre-BTrees-module instance
        else:
            try: indexRow.insert(documentId)
            except AttributeError:
                # index row is an int
                indexRow=IITreeSet((indexRow, documentId))
                self._index[entry] = indexRow

    def index_object(self, documentId, obj, threshold=None):
        """ index and object 'obj' with integer id 'documentId'"""
        global _marker
        returnStatus = 0

        # First we need to see if there's anything interesting to look at
        # self.id is the name of the index, which is also the name of the
        # attribute we're interested in.  If the attribute is callable,
        # we'll do so.
        try:
            datum = getattr(obj, self.id)
            if callable(datum):
                datum = datum()
        except AttributeError:
            datum = _marker
 
        # We don't want to do anything that we don't have to here, so we'll
        # check to see if the new and existing information is the same.
        oldDatum = self._unindex.get(documentId, _marker)
        if datum != oldDatum:
            if oldDatum is not _marker:
                self.removeForwardIndexEntry(oldDatum, documentId)

            if datum is not _marker:
                self.insertForwardIndexEntry(datum, documentId)
                self._unindex[documentId] = datum

            returnStatus = 1

        return returnStatus

    def numObjects(self):
        """ return number of indexed objects """
        return len(self._index)


    def unindex_object(self, documentId):
        """ Unindex the object with integer id 'documentId' and don't
        raise an exception if we fail """

        global _marker
        unindexRecord = self._unindex.get(documentId, _marker)
        if unindexRecord is _marker:
            return None

        self.removeForwardIndexEntry(unindexRecord, documentId)
        
        try:
            del self._unindex[documentId]
        except:
            LOG('UnIndex', ERROR, 'Attempt to unindex nonexistent document'
                ' with id %s' % documentId)

    def _apply_index(self, request, cid='', type=type, None=None): 
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
        if record.keys==None: return None

        index = self._index
        r     = None
        opr   = None


        # experimental code for specifing the operator
        operator = record.get('operator',self.useOperator)
        if not operator in self.operators :
           raise RuntimeError,"operator not valid: %s" % operator

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
                if type(set) is IntType:
                    set = IISet((set,))
                r = set_func(r, set)
        else: # not a range search
            for key in record.keys:
                set=index.get(key, None)
                if set is not None:
                    if type(set) is IntType:
                        set = IISet((set,))
                    r = set_func(r, set)

        if type(r) is IntType:  r=IISet((r,))
        if r is None:
            return IISet(), (self.id,)
        else:
            return r, (self.id,)

    def hasUniqueValuesFor(self, name):
        ' has unique values for column NAME '
        if name == self.id:
            return 1
        else:
            return 0


    def uniqueValues(self, name=None, withLengths=0):
        """\
        returns the unique values for name

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
                if type(set) is IntType:
                    l = 1
                else:
                    l = len(set)
                rl.append((i, l))
            return tuple(rl)

    def keyForDocument(self, id):
        return self._unindex[id]

    def items(self):
        items = []
        for k,v in self._index.items():
            if type(v) is IntType:
                v = IISet((v,))
            items.append((k, v))
        return items

