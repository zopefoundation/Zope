from UnIndex import UnIndex, MV, intSet
from types import ListType, TupleType
from zLOG import LOG, ERROR

class UnKeywordIndex(UnIndex):

    meta_type = 'Keyword Index'
    
    """Like an UnIndex only it indexes sequences of items
    
    Searches match any keyword.

    This should have an _apply_index that returns a relevance score
    """

    def index_object(self, i, obj, threshold=None):
        """ index an object 'obj' with integer id 'i'"""

        index = self._index
        unindex = self._unindex

        id = self.id

        try:
            kws=getattr(obj, id)
            if callable(kws):
                kws = kws()
        except:
            kws = [MV] 
        
        # index each item in the sequence
        for kw in kws:
            set = index.get(kw)
            if set is None:
                index[kw] = set = intSet()
            set.insert(i)
        
        unindex[i] = kws

        self._index = index
        self._unindex = unindex

        return 1
    

    def unindex_object(self, i):
        """ carefully unindex the object with integer id 'i' and do not
        fail if it does not exist """
        index = self._index
        unindex = self._unindex

        kws = unindex.get(i, None)
        if kws is None:
            LOG('UnKeywordIndex', ERROR,('unindex_object was called with bad '
                                         'integer id %s' % str(i)))
        for kw in kws:
            set = index.get(kw, None)
            if set is not None:
                set.remove(i)
            else:
                LOG('UnKeywordIndex', ERROR, ('unindex_object could not '
                                              'remove %s from set'
                                              % str(i)))
        del unindex[i]
        
        self._index = index
        self._unindex = unindex

