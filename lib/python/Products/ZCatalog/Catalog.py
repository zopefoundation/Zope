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

from Persistence import Persistent
import Acquisition
import ExtensionClass
from Products.PluginIndexes.TextIndex.Lexicon import Lexicon
from MultiMapping import MultiMapping
import Record
from Missing import MV
from zLOG import LOG, ERROR

from Lazy import LazyMap, LazyFilter, LazyCat
from CatalogBrains import AbstractCatalogBrain, NoBrainer

from BTrees.IIBTree import intersection, weightedIntersection, IISet
from BTrees.OIBTree import OIBTree
from BTrees.IOBTree import IOBTree
import BTrees.Length
from Products.PluginIndexes.common.randid import randid

import time, sys, types

class Catalog(Persistent, Acquisition.Implicit, ExtensionClass.Base):
    """ An Object Catalog

    An Object Catalog maintains a table of object metadata, and a
    series of manageable indexes to quickly search for objects
    (references in the metadata) that satisfy a search query.

    This class is not Zope specific, and can be used in any python
    program to build catalogs of objects.  Note that it does require
    the objects to be Persistent, and thus must be used with ZODB3.
    """

    _v_brains = NoBrainer

    def __init__(self, vocabulary=None, brains=None):
        # Catalogs no longer care about vocabularies and lexicons
        # so the vocabulary argument is ignored. (Casey)

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

        self.__len__=BTrees.Length.Length()
        self.clear()

        if brains is not None:
            self._v_brains = brains
            
        self.updateBrains()

    def clear(self):
        """ clear catalog """
        
        self.data  = IOBTree()  # mapping of rid to meta_data
        self.uids  = OIBTree()  # mapping of uid to rid
        self.paths = IOBTree()  # mapping of rid to uid

        # convert old-style Catalog object to new in-place
        try: self.__len__.set(0)
        except AttributeError: self.__len__=BTrees.Length.Length()

        for index in self.indexes.values():
            if hasattr(index, '__of__'): index=index.__of__(self)
            index.clear()

    def _convertBTrees(self, threshold=200):

        from BTrees.convert import convert

        if type(self.data) is not IOBTree:
            data=self.data
            self.data=IOBTree()
            convert(data, self.data, threshold)

            self.__len__=BTrees.Length.Length(len(data))

            uids=self.uids
            self.uids=OIBTree()
            convert(uids, self.uids, threshold)

            paths=self.paths
            self.paths=IOBTree()
            convert(paths, self.paths, threshold)


        for index in self.indexes.values():
            if hasattr(index, '__of__'): index=index.__of__(self)
            index._convertBTrees(threshold)

    def __len__(self):
        # NOTE, this is never called for new catalogs, since
        # each instance overrides this.
        return len(self.data)

    def updateBrains(self):
        self.useBrains(self._v_brains)

    def __getitem__(self, index, ttype=type(())):
        """
        Returns instances of self._v_brains, or whatever is passed 
        into self.useBrains.
        """
        if type(index) is ttype:
            # then it contains a score...
            normalized_score, score, key = index
            r=self._v_result_class(self.data[key]).__of__(self.aq_parent)
            r.data_record_id_ = key
            r.data_record_score_ = score
            r.data_record_normalized_score_ = normalized_score
        else:
            # otherwise no score, set all scores to 1
            r=self._v_result_class(self.data[index]).__of__(self.aq_parent)
            r.data_record_id_ = index
            r.data_record_score_ = 1
            r.data_record_normalized_score_ = 1
        return r

    def __setstate__(self, state):
        """ initialize your brains.  This method is called when the
        catalog is first activated (from the persistent storage) """
        Persistent.__setstate__(self, state)
        self.updateBrains()

    def useBrains(self, brains):
        """ Sets up the Catalog to return an object (ala ZTables) that
        is created on the fly from the tuple stored in the self.data
        Btree.
        """

        class mybrains(AbstractCatalogBrain, brains):
            pass
        
        scopy = self.schema.copy()

        scopy['data_record_id_']=len(self.schema.keys())
        scopy['data_record_score_']=len(self.schema.keys())+1
        scopy['data_record_normalized_score_']=len(self.schema.keys())+2

        mybrains.__record_schema__ = scopy

        self._v_brains = brains
        self._v_result_class = mybrains

    def addColumn(self, name, default_value=None):
        """
        adds a row to the meta data schema
        """
        
        schema = self.schema
        names = list(self.names)

        if schema.has_key(name):
            raise 'Column Exists', 'The column exists'

        if name[0] == '_':
            raise 'Invalid Meta-Data Name', \
                  'Cannot cache fields beginning with "_"'
        
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

        # new column? update the brain
        self.updateBrains()
            
        self.__changed__(1)    #why?
            
    def delColumn(self, name):
        """
        deletes a row from the meta data schema
        """
        names = list(self.names)
        _index = names.index(name)

        if not self.schema.has_key(name):
            LOG('Catalog', ERROR, ('delColumn attempted to delete '
                                   'nonexistent column %s.' % str(name)))
            return

        names.remove(name)

        # rebuild the schema
        i=0; schema = {}
        for name in names:
            schema[name] = i
            i = i + 1

        self.schema = schema
        self.names = tuple(names)

        # update the brain
        self.updateBrains()

        # remove the column value from each record
        for key in self.data.keys():
            rec = list(self.data[key])
            rec.remove(rec[_index])
            self.data[key] = tuple(rec)

    def addIndex(self, name, index_type):
        """Create a new index, given a name and a index_type.  

        Old format: index_type was a string, 'FieldIndex' 'TextIndex' or
        'KeywordIndex' is no longer valid; the actual index must be instantiated
        and passed in to addIndex.

        New format: index_type is the actual index object to be stored.

        """

        if self.indexes.has_key(name):
            raise 'Index Exists', 'The index specified already exists'

        if name.startswith('_'):
            raise 'Invalid Index Name', 'Cannot index fields beginning with "_"'
    
        if not name:
            raise 'Invalid Index Name', 'Name of index is empty'

        indexes = self.indexes

        if isinstance(index_type, types.StringType):
            raise TypeError,"""Catalog addIndex now requires the index type to
            be resolved prior to adding; create the proper index in the caller."""

        indexes[name] = index_type;

        self.indexes = indexes

    def delIndex(self, name):
        """ deletes an index """

        if not self.indexes.has_key(name):
            raise 'No Index', 'The index specified does not exist'

        indexes = self.indexes
        del indexes[name]
        self.indexes = indexes
        
    def getIndex(self, name):
        """ get an index wrapped in the catalog """
        return self.indexes[name].__of__(self)
        
    # the cataloging API

    def catalogObject(self, object, uid, threshold=None,idxs=[]):
        """ 
        Adds an object to the Catalog by iteratively applying it
        all indexes.

        'object' is the object to be cataloged

        'uid' is the unique Catalog identifier for this object

        """
        
        data = self.data

        # meta_data is stored as a tuple for efficiency
        newDataRecord = self.recordify(object)

        index=self.uids.get(uid, None)
        if index is not None:
            # old data
            
            if data.get(index, 0) != newDataRecord:
                # Update the meta-data, if necessary
                data[index] = newDataRecord
                
        else:
            # new data
            
            if type(data) is IOBTree:
                # New style, get radom id
                
                index=getattr(self, '_v_nextid', 0)
                if index%4000 == 0: index = randid()
                while not data.insert(index, newDataRecord):
                    index=randid()

                # We want ids to be somewhat random, but there are
                # advantages for having some ids generated
                # sequentially when many catalog updates are done at
                # once, such as when reindexing or bulk indexing.
                # We allocate ids sequentially using a volatile base,
                # so different threads get different bases. This
                # further reduces conflict and reduces churn in
                # here and it result sets when bulk indexing.
                self._v_nextid=index+1
            else:
                if data:
                    # find the next available unique id
                    index = data.keys()[-1] + 1
                else:
                    index=0
                data[index] = newDataRecord

            try: self.__len__.change(1)
            except AttributeError: pass # No managed length (old-style)
                    
            self.uids[uid] = index
            self.paths[index] = uid
            
        total = 0

        if idxs==[]: use_indexes = self.indexes.keys()
        else:        use_indexes = idxs

        for name in use_indexes:
            x = self.getIndex(name)
            if hasattr(x, 'index_object'):
                blah = x.index_object(index, object, threshold)
                total = total + blah
            else:
                LOG('Catalog', ERROR, ('catalogObject was passed '
                                       'bad index object %s.' % str(x)))

        return total

    def uncatalogObject(self, uid):
        """ 
        Uncatalog and object from the Catalog.  and 'uid' is a unique
        Catalog identifier

        Note, the uid must be the same as when the object was
        catalogued, otherwise it will not get removed from the catalog

        This method should not raise an exception if the uid cannot
        be found in the catalog.

        """
        data = self.data
        uids = self.uids
        paths = self.paths
        indexes = self.indexes.keys()
        rid = uids.get(uid, None)

        if rid is not None:
            for name in indexes:
                x = self.getIndex(name)
                if hasattr(x, 'unindex_object'):
                    x.unindex_object(rid)
            del data[rid]
            del paths[rid]
            del uids[uid]
            try: self.__len__.change(-1)
            except AttributeError: pass # No managed length
        else:
            LOG('Catalog', ERROR, ('uncatalogObject unsuccessfully '
                                   'attempted to uncatalog an object '
                                   'with a uid of %s. ' % uid))
            

    def uniqueValuesFor(self, name):
        """ return unique values for FieldIndex name """
        return self.getIndex(name).uniqueValues()

    def hasuid(self, uid):
        """ return the rid if catalog contains an object with uid """
        return self.uids.get(uid)

    def recordify(self, object):
        """ turns an object into a record tuple """
        record = []
        # the unique id is allways the first element
        for x in self.names:
            attr=getattr(object, x, MV)
            if(attr is not MV and callable(attr)): attr=attr()
            record.append(attr)
        return tuple(record)

    def instantiate(self, record):
        r=self._v_result_class(record[1])
        r.data_record_id_ = record[0]
        return r.__of__(self)


    def getMetadataForRID(self, rid):
        record = self.data[rid]
        result = {}
        for (key, pos) in self.schema.items():
            result[key] = record[pos]
        return result

    def getIndexDataForRID(self, rid):
        result = {}
        for name in self.indexes.keys():
            result[name] = self.getIndex(name).getEntryForObject(rid, "")
        return result
    
## This is the Catalog search engine. Most of the heavy lifting happens below

    def _indexedSearch(self, request, sort_index, append, used):
        """
        Iterate through the indexes, applying the query to each one.
        """
        rs = None             # resultset
        data = self.data

        # Indexes fulfill a fairly large contract here. We hand each
        # index the request mapping we are given (which may be composed 
        # of some combination of web request, kw mappings or plain old dicts)
        # and the index decides what to do with it. If the index finds work
        # for itself in the request, it returns the results and a tuple of
        # the attributes that were used. If the index finds nothing for it
        # to do then it returns None.
        
        # For hysterical reasons, if all indexes return None for a given
        # request (and no attributes were used) then we append all results
        # in the Catalog. This generally happens when the search values
        # in request are all empty strings or do not coorespond to any of
        # the indexes.
        
        # Note that if the indexes find query arguments, but the end result
        # is an empty sequence, we do nothing

        # If sort_index is None, this method should pass sequences of
        # catalog records to append().  The sequences will be concatenated
        # together to generate the result set.
        # If sort_index is not None, this method should instead pass pairs
        # to append(), each pair containing a sort key and a sequence of
        # catalog records.
        # In either case, the sequences may be lazified.

        if used is None:
            used = {}
        for i in self.indexes.keys():
            index = self.getIndex(i)
            _apply_index = getattr(index, "_apply_index", None)
            if _apply_index is None:
                continue
            r = _apply_index(request)

            if r is not None:
                r, u = r
                for name in u:
                    used[name] = 1
                w, rs = weightedIntersection(rs, r)

        if rs is None:
            # None of the indexes found anything to do with the request
            # We take this to mean that the query was empty (an empty filter)
            # and so we return everything in the catalog
            if sort_index is None:
                rs = data.items()
                append(LazyMap(self.instantiate, rs, len(self)))
            else:
                self._build_sorted_results(data, sort_index, append)
        elif rs:
            # We got some results from the indexes.
            # Sort and convert to sequences.
            if sort_index is None and hasattr(rs, 'values'):
                # having a 'values' means we have a data structure with
                # scores.  Build a new result set, sort it by score, reverse
                # it, compute the normalized score, and Lazify it.
                rset = rs.byValue(0) # sort it by score
                max = float(rset[0][0])
                
                # Here we define our getter function inline so that
                # we can conveniently store the max value as a default arg
                # and make the normalized score computation lazy
                def getScoredResult(item, max=max, self=self):
                    """
                    Returns instances of self._v_brains, or whatever is passed 
                    into self.useBrains.
                    """
                    score, key = item
                    r=self._v_result_class(self.data[key])\
                          .__of__(self.aq_parent)
                    r.data_record_id_ = key
                    r.data_record_score_ = score
                    r.data_record_normalized_score_ = int(100. * score / max)
                    return r
                
                # Lazify the results
                append(LazyMap(getScoredResult, rset))
                    
            elif sort_index is None and not hasattr(rs, 'values'):
                # no scores?  Just Lazify.
                if hasattr(rs, 'keys'):
                    rs = rs.keys() 
                append(LazyMap(self.__getitem__, rs))
            else:
                # sort.  If there are scores, then this block is not
                # reached, therefore 'sort-on' does not happen in the
                # context of a text index query.  This should probably
                # sort by relevance first, then the 'sort-on' attribute.
                self._build_sorted_results(rs,sort_index,append)

        #print 'ZCatalog search used', used.keys()
        return used

    def _build_sorted_results(self,rs,sort_index,append):
        # This function will .append pairs where the first item
        # in the pair is a sort key, and the second item in the
        # pair is a sequence of results which share the same
        # sort key. Later on the list to which these things
        # are .append()ed will be .sort()ed, and the first element
        # of each pair stripped.
        #
        # The two 'for' loops in here contribute a significant
        # proportion of the time to perform an indexed search.
        # Try to avoid all non-local attribute lookup inside
        # those loops.
        _lazymap = LazyMap
        _intersection = intersection
        _self__getitem__ = self.__getitem__
        _None = None
        if (len(rs) > (len(sort_index) * 4)):
            # The result set is much larger than the sorted index,
            # so iterate over the sorted index for speed.

            try:
                intersection(rs, IISet(()))
            except TypeError:
                # rs is not an object in the IIBTree family.
                # Try to turn rs into an IISet.
                if hasattr(rs, 'keys'):
                    rs = rs.keys()
                rs = IISet(rs)

            for k, intset in sort_index.items():
                # We have an index that has a set of values for
                # each sort key, so we intersect with each set and
                # get a sorted sequence of the intersections.
                intset = _intersection(rs, intset)
                if intset:
                    keys = getattr(intset, 'keys', _None)
                    if keys is not _None:
                        # Is this ever true?
                        intset = keys()
                    append((k, _lazymap(_self__getitem__, intset)))
                    # Note that sort keys are unique.
        else:
            # Iterate over the result set.
            if hasattr(rs, 'keys'):
                rs = rs.keys()
            _sort_index_keyForDocument = sort_index.keyForDocument
            _keyerror = KeyError
            for did in rs:
                try:
                    key = _sort_index_keyForDocument(did)
                except _keyerror:
                    # This document is not in the sort key index.
                    # skip it.
                    pass
                else:
                    # We want the sort keys to be unique so that
                    # .sort()ing the list does not involve comparing
                    # _lazymap objects, which is slow. To ensure
                    # uniqueness the first element of each pair is
                    # actually a tuple of:
                    # (real sort key, some unique number)
                    lm = _lazymap(_self__getitem__, [did])
                    key = key, id(lm)
                    append((key,lm))

    def _get_sort_attr(self, attr, kw):
        """Helper function to find sort-on or sort-order."""
        # There are three different ways to find the attribute:
        # 1. kw[sort-attr]
        # 2. self.sort-attr
        # 3. kw[sort_attr]
        # kw may be a dict or an ExtensionClass MultiMapping, which
        # differ in what get() returns with no default value.
        name = "sort-%s" % attr
        val = kw.get(name, None)
        if val is not None:
            return val
        val = getattr(self, name, None)
        if val is not None:
            return val
        return kw.get("sort_%s" % attr, None)


    def _getSortIndex(self, args):
        """Returns a search index object or None."""
        sort_index_name = self._get_sort_attr("on", args)
        if sort_index_name is not None:
            # self.indexes is always a dict, so get() w/ 1 arg works
            sort_index = self.indexes.get(sort_index_name)
            if sort_index is None:
                raise CatalogError, 'Unknown sort_on index'
            else:
                if not hasattr(sort_index, 'keyForDocument'):
                    raise CatalogError(
                        'The index chosen for sort_on is not capable of being'
                        ' used as a sort index.'
                        )
            return sort_index
        else:
            return None


    def searchResults(self, REQUEST=None, used=None, _merge=1, **kw):
        if REQUEST is None and not kw:
            # Try to acquire request if we get no args for bw compat
            REQUEST = getattr(self, 'REQUEST', None)
        args = CatalogSearchArgumentsMap(REQUEST, kw)
        sort_index = self._getSortIndex(args)
        # Perform searches with indexes and sort_index
        r = []
        used = self._indexedSearch(args, sort_index, r.append, used)
        if not _merge:
            # Postpone merging and sorting.  This provides a way to
            # efficiently sort results merged from multiple queries
            # or multiple catalogs.
            return r
        else:
            has_sort_keys = 0
            reverse = 0
            if sort_index is not None:
                has_sort_keys = 1
                order = self._get_sort_attr("order", args)
                if (isinstance(order, types.StringType) and
                    order.lower() in ('reverse', 'descending')):
                    reverse = 1
            return mergeResults(r, has_sort_keys, reverse)

    __call__ = searchResults


class CatalogError(Exception): pass

class CatalogSearchArgumentsMap:
    """Multimap catalog arguments coming simultaneously from keywords 
    and request.
    
    Values that are empty strings are treated as non-existent. This is
    to ignore empty values, thereby ignoring empty form fields to be 
    consistent with hysterical behavior.
    """
    
    def __init__(self, request, keywords):
        self.request = request or {}
        self.keywords = keywords or {}
        
    def __getitem__(self, key):
        marker = []
        v = self.keywords.get(key, marker)
        if v is marker or v == '':
            v = self.request[key]
        if v == '':
            raise KeyError(key)
        return v
            
    def get(self, key, default=None):
        try:
            v = self[key]
        except KeyError:
            return default
        else:
            return v
            
    def has_key(self, key):
        try:
            self[key]
        except KeyError:
            return 0
        else:
            return 1
        
        
def mergeResults(r, has_sort_keys, reverse):
    """Sort/merge sub-results, generating a flat sequence.

    The contents of r depend on whether has_sort_keys is set.
    If not has_sort_keys, r contains sequences of records.
    If has_sort_keys, r contains pairs of (sort_key, sequence)
    and now we have to sort the results.
    """
    if not r:
        return LazyCat(r)
    elif len(r) == 1:
        if not has_sort_keys:
            return r[0]
        else:
            return r[0][1]
    else:
        if not has_sort_keys:
            # Note that the length of the final sequence is not
            # the same as the length of r, since r may contain
            # sequences of different sizes.
            return LazyCat(r)
        else:
            r.sort()
            if reverse:
                r.reverse()
            size = 0
            tmp = []
            for i in r:
                elt = i[1]
                tmp.append(elt)
                size += len(elt)
            return LazyCat(tmp, size)
    
