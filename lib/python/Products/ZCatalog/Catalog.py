from Persistence import Persistent
import Acquisition
import BTree, OIBTree, IOBTree
from SearchIndex import UnIndex, UnTextIndex, Query
import regex
import Record
from Missing import MV

from Lazy import LazyMap, LazyFilter, LazyCat


class NoBrainer:
    """ This is the default class that gets instanciated for records
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
    series of managable indexes to quickly search for objects
    (references in the metadata) that satify a search query.
    """

    _v_brains = NoBrainer

    def __init__(self, brains=None):

        self.schema = {}    # mapping from attribute name to column number
        self.names = ()     # sequence of column names
        self.indexes = {}
        
        self.data = BTree.BTree()
        self.uids = OIBTree.BTree()
        self.paths = IOBTree.BTree()

        if brains is not None:
            self._v_brains = brains
            
        self.useBrains(self._v_brains)


    def __getitem__(self, index):
        """ returns instances of self._v_brains, or whatever is passed 
        into self.useBrains.
        """
        
        r=self._v_result_class(self.data[index]).__of__(self.aq_parent)
        r.data_record_id_ = index
        return r



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
        for key, value in self.schema.items():
            scopy[key]=value
        scopy['data_record_id_']=len(self.schema.keys())

        mybrains.__theCircularGottaCoverUpABugRefOfJoy = mybrains
        mybrains.__record_schema__ = scopy

        self._v_brains = brains
        self._v_result_class=mybrains


    def addColumn(self, name, default_value=None):
        """ adds a row to the schema """
        
        schema = self.schema
        names = list(self.names)
        
        if not schema.has_key(name):
            if schema.values():
                schema[name] = max(schema.values())+1
            else:
                schema[name] = 0
            names.append(name)
            self.useBrains(self._v_brains)

        if default_value is None or default_value == '':
            default_value = MV

        for key in self.data.keys():
            rec = list(self.data[key])
            rec.append(default_value, name)
            self.data[key] = tuple(rec)

        self.names = tuple(names)
        self.schema = schema

        self.__changed__(1)    #why?

            
    def delColumn(self, name):
        """ deletes a row from the schema """
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

        # remove the column value from each record
        for key in self.data.keys():
            rec = list(self.data[key])
            rec.remove(rec[_index])
            self.data[key] = tuple(rec)
            

    def addIndex(self, name, type):
        """ add an index """
        if self.indexes.has_key(name):
            raise 'Index Exists', 'The index specified allready exists'
        
        if type == 'FieldIndex':
            self.indexes[name] = UnIndex.UnIndex(name)
        elif type == 'TextIndex':
            self.indexes[name] = UnTextIndex.UnTextIndex(name)

    def delIndex(self, name):
        """ delete an index """

        if not self.indexes.has_key(name):
            raise 'No Index', 'The index specified does not exist'

        indexes = self.indexes
        del indexes[name]
        self.indexes = indexes


    # the cataloging API

    def catalogObject(self, object, uid):
        """ adds an object to the Catalog
        'object' is the object to be cataloged
        'uid' is the unique Catalog identifier for this object
        """
        # store a record in the dataset that coresponds to the object
        data = self.data
        if data: i = data.keys()[-1] + 1  # find the next available
        else: i = 0                       # rid

        self.uids[uid] = i
        self.paths[i] = uid
        
        data[i] = self.recordify(object)

        for x in self.indexes.keys():
            if hasattr(self.indexes[x], 'index_object'):
                self.indexes[x].index_object(i, object)
        self.data = data
                                          

    def uncatalogObject(self, uid):
        """ Uncatalog and object from the Catalog.
        and 'uid' is a unique Catalog identifier

        Note, the uid must be the same as when the object was
        cataloged, otherwise it will not get unindexed """
        
        # un index the object

        rid = self.uids[uid]

        for x in self.indexes.keys():
            if hasattr(self.indexes[x], 'unindex_object'):
                self.indexes[x].unindex_object(rid)
        del self._data[rid]


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



    def _indexedSearch(self, args, sort_index, append, used):
        rs=None
        data=self.data
##        cid=self.id
        
        if used is None: used={}
        for i in self.indexes.keys():
            try:
                index = self.indexes[i]
                if hasattr(index,'_apply_index'):
                    r=index._apply_index(args)
                    if r is not None:
                        r,u=r
                        for name in u: used[name]=1
                        if rs is None: rs=r
                        else: rs=rs.intersection(r)
            except:
                return used

        if rs is None:
            if sort_index is None:
                rs=data.items()
                append(LazyMap(self.instantiate, rs))
            else:
                for k, intset in sort_index.items():
                    append((k,LazyMap(self.__getitem__, intset)))
        elif rs:
            if sort_index is None:
                append(LazyMap(self.__getitem__, rs))
            else:
                for k, intset in sort_index.items():
                    __traceback_info__=intset, intset.__class__
                    intset=intset.intersection(rs)
                    if intset: append((k,LazyMap(self.__getitem__, intset)))

        return used



    def searchResults(self, REQUEST=None, used=None,
                      query_map={
                          type(regex.compile('')): Query.Regex,
                          type([]): orify,
                          type(''): Query.String,
                          }, **kw):

        
        self.useBrains(self._v_brains)

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
                else: so=None
                if (type(so) is type('') and
                    lower(so) in ('reverse', 'descending')):
                    r.reverse()
                r=LazyCat(map(lambda i: i[1], r))

##        #################################################################
##        # Add unindexed search criteria:
##	# skey used to get the schema keys, but computed fields aren't in 
##	# there anymore.  instead they're in the data_dictionary.
##        skey=_data._data_dictionary.has_key
##        ukey=used.has_key
##        subqueries=[]
##	# join the previously together computed field names and reg names
##	allnames=list(_data._names)+list(_data._computed_fields)
##        for name in allnames:
##            try: v=kw[name]
##            except: v=kw
##            if v is not kw and (v or v==0) and not ukey(name) and skey(name):
##                used[name]=1
##		if name in _data._names:
##		    # use the integer key of the column
##		    key=_data._schema[name]
##		else:
##		    # it's a computed attribute, use its name.  Query.FieldTest
##		    # will figure it out.
##		    key=name
##                try: q=query_map[type(v)](v)
##                except: q=Query.Cmp(v)
##                subqueries.append(Query.FieldTest(key,q))

##        if subqueries:
##            if len(subqueries) > 1: query=apply(Query.And,tuple(subqueries))
##            else: query=subqueries[0]
##            r=LazyFilter(query,r)
##            try: data._len=atoi(kw['DP_CACHED_LENGTH'])
##            except: pass

        #################################################################
        # decorate results and return:
##        r._searchable_result_columns=self._searchable_result_columns

        return r


    __call__ = searchResults





