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

from Persistence import Persistent
import Acquisition
import BTree, OIBTree, IOBTree, IIBTree
IIBucket=IIBTree.Bucket
from intSet import intSet
from SearchIndex import UnIndex, UnTextIndex, UnKeywordIndex, Query
import regex, pdb
from string import lower
import Record
from Missing import MV

from Lazy import LazyMap, LazyFilter, LazyCat

class NoBrainer:
    """ This is the default class that gets instantiated for records
    returned by a __getitem__ on the Catalog.  By default, no special
    methods or attributes are defined.
    """
    pass

def orify(seq,
          query_map={
              type(regex.compile('')): Query.Regex,
              type(''): Query.String,
              }):
    subqueries=[]
    for q in seq:
        try: q=query_map[type(q)](q)
        except: q=Query.Cmp(q)
        subqueries.append(q)
    return apply(Query.Or,tuple(subqueries))
    

class Catalog(Persistent, Acquisition.Implicit):
    """ An Object Catalog

    An Object Catalog maintains a table of object metadata, and a
    series of manageable indexes to quickly search for objects
    (references in the metadata) that satisfy a search query.

    This class is not Zope specific, and can be used in any python
    program to build catalogs of objects.
    """

    _v_brains = NoBrainer
    _v_result_class = NoBrainer

    def __init__(self, brains=None):

        self.schema = {}    # mapping from attribute name to column number
        self.names = ()     # sequence of column names
        self.indexes = {}   # maping from index name to index object

        # The catalog maintains a BTree of object meta_data for
        # convenient display on result pages.  meta_data attributes
        # are turned into brain objects and returned by
        # searchResults.  The indexing machinery indexes all records
        # by an integer id (rid).  self.data is a mapping from the
        # integer id to the meta_data, self.uids is a mapping of the
        # object unique identifier to the rid, and self.paths is a
        # mapping of the rid to the unique identifier.
        
        self.data = BTree.BTree()       # mapping of rid to meta_data
        self.uids = OIBTree.BTree()     # mapping of uid to rid
        self.paths = IOBTree.BTree()    # mapping of rid to uid

        if brains is not None:
            self._v_brains = brains
            
        self.useBrains(self._v_brains)

    def __getitem__(self, index, ttype=type(())):
        """ Returns instances of self._v_brains, or whatever is passed 
        into self.useBrains.
        """
##        import pdb
##        pdb.set_trace()
        if type(index) is ttype:
            score, key = index
            r=self._v_result_class(self.data[key]).__of__(self.aq_parent)
            r.data_record_score_ = score
            r.data_record_id_ = key
        else:
            r=self._v_result_class(self.data[index]).__of__(self.aq_parent)
            r.data_record_id_ = index
            r.data_record_id_ = 1

        return r

    def __setstate__(self, state):
        Persistent.__setstate__(self, state)
        self.useBrains(self._v_brains)

    def useBrains(self, brains):
        
        """ Sets up the Catalog to return an object (ala ZTables) that
        is created on the fly from the tuple stored in the self.data
        Btree.
        """

        class mybrains(Record.Record, Acquisition.Implicit, brains):
            __doc__ = 'Data record'
            def has_key(self, key):
                return self.__record_schema__.has_key(key)
        
        scopy={}
        scopy = self.schema.copy()

        scopy['data_record_id_']=len(self.schema.keys())
        scopy['data_record_score_']=len(self.schema.keys())+1
        mybrains.__record_schema__ = scopy

        self._v_brains = brains
        self._v_result_class=mybrains

    def addColumn(self, name, default_value=None):
        """ adds a row to the meta data schema """
        
        schema = self.schema
        names = list(self.names)

        if schema.has_key(name):
            raise 'Column Exists', 'The column exists'
        
        if not schema.has_key(name):
            if schema.values():
                schema[name] = max(schema.values())+1
            else:
                schema[name] = 0
            names.append(name)

        if default_value is None or default_value == '':
            default_value = MV

        for key in self.data.keys():
            rec = list(self.data[key])
            rec.append(default_value)
            self.data[key] = tuple(rec)

        self.names = tuple(names)
        self.schema = schema

        self.useBrains(self._v_brains)
            
        self.__changed__(1)    #why?
            
    def delColumn(self, name):
        """ deletes a row from the meta data schema """
        names = list(self.names)
        _index = names.index(name)

        if not self.schema.has_key(name):
            return

        names.remove(name)

        # rebuild the schema
        i=0; schema = {}
        for name in names:
            schema[name] = i
            i = i + 1

        self.schema = schema
        self.names = tuple(names)

        self.useBrains(self._v_brains)

        # remove the column value from each record
        for key in self.data.keys():
            rec = list(self.data[key])
            rec.remove(rec[_index])
            self.data[key] = tuple(rec)

    def addIndex(self, name, type):
        """ adds an index """
        if self.indexes.has_key(name):
            raise 'Index Exists', 'The index specified allready exists'

        indexes = self.indexes
        if type == 'FieldIndex':
            indexes[name] = UnIndex.UnIndex(name)
        elif type == 'TextIndex':
            indexes[name] = UnTextIndex.UnTextIndex(name)
        elif type == 'KeywordIndex':
            indexes[name] = UnKeywordIndex.UnKeywordIndex(name)

        self.indexes = indexes

    def delIndex(self, name):
        """ deletes an index """

        if not self.indexes.has_key(name):
            raise 'No Index', 'The index specified does not exist'

        indexes = self.indexes
        del indexes[name]
        self.indexes = indexes

    # the cataloging API

    def catalogObject(self, object, uid, threshold=None):
        """ 

        Adds an object to the Catalog by iteratively applying it
        all indexes.

        'object' is the object to be cataloged

        'uid' is the unique Catalog identifier for this object

        """

        data = self.data

        if self.uids.has_key(uid):
            i = self.uids[uid]
        elif data:
            i = data.keys()[-1] + 1  # find the next available rid
        else:
            i = 0                       

        self.uids[uid] = i
        self.paths[i] = uid
        
        # meta_data is stored as a tuple for efficiency
        data[i] = self.recordify(object)

        total = 0
        for x in self.indexes.values():
            if hasattr(x, 'index_object'):
                blah = x.index_object(i, object, threshold)
                total = total + blah

        self.data = data

        return total

    def uncatalogObject(self, uid):
        """ 

        Uncatalog and object from the Catalog.  and 'uid' is a unique
        Catalog identifier

        Note, the uid must be the same as when the object was
        catalogued, otherwise it will not get removed from the catalog

        """
        
        if uid not in self.uids.keys():
            return
        
        rid = self.uids[uid]

        for x in self.indexes.values():
            if hasattr(x, 'unindex_object'):
                try:
                    x.unindex_object(rid)
                except KeyError:
                    pass  #fugedaboudit

        # I think if your data gets out of sync due to crashes or
        # ZClass problems, some items might not be here.  The try's
        # catch any inconsistencies and lets 'Update Catalog' sanify
        # the situation
        del self.data[rid]
        del self.uids[uid]
        del self.paths[rid]

    def clear(self):

        """ clear catalog """
        
        self.data = BTree.BTree()
        self.uids = OIBTree.BTree()
        self.paths = IOBTree.BTree()

        for x in self.indexes.values():
            x.clear()

    def uniqueValuesFor(self, name):
        """ return unique values for FieldIndex name """
        return self.indexes[name].uniqueValues()

    def hasuid(self, uid):
        """ return the rid if catalog contains an object with uid """
        if uid in self.uids.keys():
            return self.uids[uid]
        else:
            return None

    def recordify(self, object):
        """ turns an object into a record tuple """

        record = []
        # the unique id is allways the first element
        for x in self.names:
            try:
                attr = getattr(object, x)
                if(callable(attr)):
                    attr = attr()
                    
            except:
                attr = MV
            record.append(attr)

        return tuple(record)

    def instantiate(self, record):

        r=self._v_result_class(record[1])
        r.data_record_id_ = record[0]
        return r.__of__(self)

## Searching engine

    def _indexedSearch(self, args, sort_index, append, used,
                       IIBType=type(IIBucket()), intSType=type(intSet())):

        rs=None
        data=self.data
        
        if used is None: used={}
        for i in self.indexes.keys():
            try:
                index = self.indexes[i]
                if hasattr(index,'_apply_index'):
                    r=index._apply_index(args)
                    if r is not None:
                        r, u = r
                        for name in u:
                            used[name]=1
                        if rs is None:
                            rs = r
                        else:
                            if type(rs) is intSType and type(r) is IIBType:
                                rs=r.intersection(rs)
                            else:
                                rs=rs.intersection(r)
            except:
                return used

        if rs is None:
            if sort_index is None:
                rs=data.items()
                append(LazyMap(self.instantiate, rs))
            else:
                for k, intset in sort_index._index.items():
                    append((k,LazyMap(self.__getitem__, intset)))
        elif rs:
            if type(rs) is IIBType:
                rset = []
                for key, score in rs.items():
                    rset.append((score, key))
                rset.sort()
                rset.reverse()
                append(LazyMap(self.__getitem__, rset))
                    
            elif sort_index is None and type(rs) is intSType:
                append(LazyMap(self.__getitem__, rs))
            else:
                for k, intset in sort_index._index.items():
                    intset=intset.intersection(rs)
                    if intset: 
                        append((k,LazyMap(self.__getitem__, intset)))

        return used

    def searchResults(self, REQUEST=None, used=None,
                      query_map={
                          type(regex.compile('')): Query.Regex,
                          type([]): orify,
                          type(''): Query.String,
                          }, **kw):

        #################################################################
        # Get search arguments:
        if REQUEST is None and not kw:
            try: REQUEST=self.REQUEST
            except: pass

        if kw:
            if REQUEST:
                m=KWMultiMapping()
                m.push(REQUEST)
                m.push(kw)
                kw=m
        elif REQUEST: kw=REQUEST


        #################################################################
        # Make sure batch size is set
        if REQUEST and not REQUEST.has_key('batch_size'):
            try: batch_size=self.default_batch_size
            except: batch_size=20
            REQUEST['batch_size']=batch_size

        #################################################################
        # Compute "sort_index", which is a sort index, or none:
        if kw.has_key('sort-on'):
            sort_index=kw['sort-on']
        elif hasattr(self, 'sort-on'):
            sort_index=getattr(self, 'sort-on')
        elif kw.has_key('sort_on'):
            sort_index=kw['sort_on']
        else: sort_index=None
        sort_order=''
        if sort_index is not None and sort_index in self.indexes.keys():
            sort_index=self.indexes[sort_index]

        #################################################################
        # Perform searches with indexes and sort_index
        r=[]
        used=self._indexedSearch(kw, sort_index, r.append, used)
        if not r: return r

        #################################################################
        # Sort/merge sub-results
        if len(r)==1:
            if sort_index is None: r=r[0]
            else: r=r[0][1]
        else:
            if sort_index is None: r=LazyCat(r)
            else:
                r.sort()
                if kw.has_key('sort-order'):
                    so=kw['sort-order']
                elif hasattr(self, 'sort-order'):
                    so=getattr(self, 'sort-order')
                elif kw.has_key('sort_order'):
                    so=kw['sort_order']
                else: so=None
                if (type(so) is type('') and
                    lower(so) in ('reverse', 'descending')):
                    r.reverse()
                r=LazyCat(map(lambda i: i[1], r))

        return r

    __call__ = searchResults





