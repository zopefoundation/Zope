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

__version__='$Revision: 1.23 $'[11:-2]



from Globals import Persistent
from Acquisition import Implicit
import BTree
import IOBTree
from intSet import intSet
import operator
from Missing import MV
import string, pdb
from zLOG import LOG, ERROR
from types import *


def nonEmpty(s):
    "returns true if a non-empty string or any other (nonstring) type"
    if type(s) is StringType:
        if s: return 1
        else: return 0
    else:
        return 1


class UnIndex(Persistent, Implicit):
    """UnIndex object interface"""

    meta_type = 'Field Index'

    def __init__(self, id=None, ignore_ex=None, call_methods=None):
        """Create an unindex

        UnIndexes are indexes that contain two index components, the
        forward index (like plain index objects) and an inverted
        index.  The inverted index is so that objects can be unindexed 
        even when the old value of the object is not known.

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
	######################################################################
	# For b/w compatability, have to allow __init__ calls with zero args

        if not id==ignore_ex==call_methods==None:
            self.id = id
            self.ignore_ex=ignore_ex        # currently unimplimented
            self.call_methods=call_methods
            self._index = BTree.BTree()
            self._unindex = IOBTree.BTree()

        else:
            pass


    def __len__(self):
        return len(self._unindex)


    def histogram(self):
        """Return a mapping which provides a histogram of the number of
        elements found at each point in the index."""

        histogram = {}
        for (key, value) in self._index.items():
            entry = len(value)
            histogram[entry] = histogram.get(entry, 0) + 1

        return histogram


    def referencedObjects(self):
        """Generate a list of IDs for which we have referenced objects."""
        return self._unindex.keys()


    def getEntryForObject(self, documentId, default=None):
        """Takes a document ID and returns all the information we have
        on that specific object."""
        if default is None:
            return self._unindex.get(documentId, default)
        else:
            return self._unindex.get(documentId)
            
        
    def removeForwardIndexEntry(self, entry, documentId):
        """Take the entry provided and remove any reference to documentId
        in its entry in the index."""

        indexRow = self._index.get(entry, MV)
        if indexRow is not MV:
            try:
                indexRow.remove(documentId)
                if len(indexRow) == 0:
                    del self._index[entry]
            except:
                LOG(self.__class__.__name__, ERROR,
                    ('unindex_object could not remove '
                     'integer id %s from index %s.  This '
                     'should not happen.'
                     % (str(i), str(k)))) 
        else:
            LOG(self.__class__.__name__, ERROR,
                ('unindex_object tried to retrieve set %s '
                 'from index %s but couldn\'t.  This '
                 'should not happen.' % (repr(set),str(k))))

        
    def insertForwardIndexEntry(self, entry, documentId):
        """Take the entry provided and put it in the correct place
        in the forward index.

        This will also deal with creating the entire row if necessary."""

        indexRow = self._index.get(entry, MV)

        # Make sure there's actually a row there already.  If not, create
        # an IntSet and stuff it in first.
        if indexRow is MV:
            self._index[entry] = intSet()
            indexRow = self._index[entry]
        indexRow.insert(documentId)


    def index_object(self, documentId, obj, threshold=None):
        """ index and object 'obj' with integer id 'documentId'"""

        returnStatus = 0

        # First we need to see if there's anything interesting to look at
        # self.id is the name of the index, which is also the name of the
        # attribute we're interested in.  If the attribute is callable,
        # we'll do so.
        try:
            datum = getattr(obj, self.id)
            if callable(datum):
                datum = datum()
        except:
            datum = MV
 
        # We don't want to do anything that we don't have to here, so we'll
        # check to see if the new and existing information is the same.
        if not (datum == self._unindex.get(documentId, MV)):
            self.insertForwardIndexEntry(datum, documentId)
            self._unindex[documentId] = datum

            returnStatus = 1
            self._p_changed = 1         # Tickle the transaction

        return returnStatus
    

    def unindex_object(self, documentId):
        """ Unindex the object with integer id 'documentId' and don't
        raise an exception if we fail """

        unindexRecord = self._unindex.get(documentId, None)
        if unindexRecord is None:
            return None

        self.removeForwardIndexEntry(unindexRecord, documentId)
        
        del self._unindex[documentId]
        

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

        if request.has_key(cidid):
            keys = request[cidid]
        elif request.has_key(id):
            keys = request[id]
        else:
            return None

        if type(keys) not in (ListType, TupleType):
            keys = [keys]

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
                if hi:
                    setlist = index.items(lo,hi)
                else:
                    setlist = index.items(lo)

                for k, set in setlist:
                    if r is None:
                        r = set
                    else:
                        r = r.union(set)

            except KeyError:
                pass

        else:           #not a range
            get = index.get
            for key in keys:
                if nonEmpty(key):
                    anyTrue = 1
                set=get(key)
                if set is not None:
                    if r is None:
                        r = set
                    else:
                        r = r.union(set)

        if r is None:
            if anyTrue:
                r=intSet()
            else:
                return None

        return r, (id,)


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
        self._index = BTree.BTree()
        self._unindex = IOBTree.BTree()



