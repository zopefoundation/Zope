from UnIndex import UnIndex, MV, intSet
from types import ListType, TupleType

class UnKeywordIndex(UnIndex):
    """
    Like an UnIndex only it indexs sequences of items
    
    Searches match any keyword.
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
        """ Unindex the object with integer id 'i' """
        index = self._index
        unindex = self._unindex

        kws = unindex[i]
        if kws is None:
            return None
        
        for kw in kws:
            set = index.get(kw)
            if set is not None: set.remove(i)
        
        del unindex[i]
        
        self._index = index
        self._unindex = unindex









