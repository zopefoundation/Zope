##############################################################################
#
# Zope Public License (ZPL) Version 0.9.4
# ---------------------------------------
# 
# Copyright (c) Digital Creations.  All rights reserved.
# 
# Redistribution and use in source and binary forms, with or
# without modification, are permitted provided that the following
# conditions are met:
# 
# 1. Redistributions in source code must retain the above
#    copyright notice, this list of conditions, and the following
#    disclaimer.
# 
# 2. Redistributions in binary form must reproduce the above
#    copyright notice, this list of conditions, and the following
#    disclaimer in the documentation and/or other materials
#    provided with the distribution.
# 
# 3. Any use, including use of the Zope software to operate a
#    website, must either comply with the terms described below
#    under "Attribution" or alternatively secure a separate
#    license from Digital Creations.
# 
# 4. All advertising materials, documentation, or technical papers
#    mentioning features derived from or use of this software must
#    display the following acknowledgement:
# 
#      "This product includes software developed by Digital
#      Creations for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
# 5. Names associated with Zope or Digital Creations must not be
#    used to endorse or promote products derived from this
#    software without prior written permission from Digital
#    Creations.
# 
# 6. Redistributions of any form whatsoever must retain the
#    following acknowledgment:
# 
#      "This product includes software developed by Digital
#      Creations for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
# 7. Modifications are encouraged but must be packaged separately
#    as patches to official Zope releases.  Distributions that do
#    not clearly separate the patches from the original work must
#    be clearly labeled as unofficial distributions.
# 
# Disclaimer
# 
#   THIS SOFTWARE IS PROVIDED BY DIGITAL CREATIONS ``AS IS'' AND
#   ANY EXPRESSED OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
#   LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND
#   FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.  IN NO EVENT
#   SHALL DIGITAL CREATIONS OR ITS CONTRIBUTORS BE LIABLE FOR ANY
#   DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
#   CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
#   PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
#   DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#   ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
#   LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING
#   IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF
#   THE POSSIBILITY OF SUCH DAMAGE.
# 
# Attribution
# 
#   Individuals or organizations using this software as a web site
#   must provide attribution by placing the accompanying "button"
#   and a link to the accompanying "credits page" on the website's
#   main entry point.  In cases where this placement of
#   attribution is not feasible, a separate arrangment must be
#   concluded with Digital Creations.  Those using the software
#   for purposes other than web sites must provide a corresponding
#   attribution in locations that include a copyright using a
#   manner best suited to the application environment.
# 
# This software consists of contributions made by Digital
# Creations and many individuals on behalf of Digital Creations.
# Specific attributions are listed in the accompanying credits
# file.
# 
##############################################################################

"""Simple column indices"""
__version__='$Revision: 1.17 $'[11:-2]

from Globals import Persistent
from BTree import BTree
from intSet import intSet
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

    def _init(self,data,schema,id):
        """Create an index

        The arguments are:

          'data' -- a mapping from integer object ids to objects or records,

          'schema' -- a mapping from item name to index into data records.
              If 'data' is a mapping to objects, then schema should ne 'None'.

          'id' -- the name of the item attribute to index.  This is either
              an attribute name or a record key.
        """
        self._data=data
        self._schema=schema
        self.id=id
        self._index=BTree()
        
        self._reindex()

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
        self._index=BTree()

    def _reindex(self,start=0):
        """Recompute index data for data with ids >= start."""

        index=self._index
        get=index.get
        
        if not start: index.clear()

        id=self.id
        if self._schema is None:
            f=getattr
        else:
            f=operator.__getitem__
            id=self._schema[id]

        for i,row in self._data.items(start):
            k=f(row,id)

            if k is None or k == MV: continue

            set=get(k)
            if set is None: index[k]=set=intSet()
            set.insert(i)

    def index_item(self,i):
        """Recompute index data for data with ids >= start."""

        index=self._index

        id=self.id
        if self._schema is None:
            f=getattr
        else:
            f=operator.__getitem__
            id=self._schema[id]

        row=self._data[i]
        k=f(row,id)

        if k is None or k == MV: return

        set=index.get(k)
        if set is None: index[k]=set=intSet()
        set.insert(i)

    def unindex_item(self,i):
        """Recompute index data for data with ids >= start."""

        index=self._index

        id=self.id
        if self._schema is None:
            f=getattr
        else:
            f=operator.__getitem__
            id=self._schema[id]

        row=self._data[i]
        k=f(row,id)
        
        set=index.get(k)
        if set is not None: set.remove(i)

    def _apply_index(self, request, cid=''):
        """Apply the index to query parameters given in the argument, request

        The argument should be a mapping object.

        If the request does not contain the needed parameters, then None is
        returned.

        If the request contains a parameter with the name of the column
        + '_usage', it is sniffed for information on how to handle applying
        the index.

        Otherwise two objects are returned.  The first object is a
        ResultSet containing the record numbers of the matching
        records.  The second object is a tuple containing the names of
        all data fields used.

        """
        id=self.id              #name of the column

        cidid="%s/%s" % (cid,id)
        has_key=request.has_key
        if has_key(cidid): keys=request[cidid]
        elif has_key(id): keys=request[id]
        else: return None

        if type(keys) is not ListType: keys=[keys]
        index=self._index
        r=None
        anyTrue=0
        opr=None

        if request.has_key(id+'_usage'):
            # see if any usage params are sent to field
            opr=string.split(string.lower(request[id+"_usage"]),':')
            opr, opr_args=opr[0], opr[1:]

        if opr=="range":
            if 'min' in opr_args: lo=min(keys)
            else: lo=None
            if 'max' in opr_args: hi=max(keys)
            else: hi=None

            anyTrue=1
            try:
                if hi: setlist=index.items(lo,hi)
                else:  setlist=index.items(lo)
                for k,set in setlist:
                    if r is None: r=set
                    else: r=r.union(set)
            except KeyError: pass
        else:           #not a range
            get=index.get
            for key in keys:
                if key: anyTrue=1
                set=get(key)
                if set is not None:
                    if r is None: r=set
                    else: r = r.union(set)

        if r is None:
            if anyTrue: r=intSet()
            else: return None

        return r, (id,)
