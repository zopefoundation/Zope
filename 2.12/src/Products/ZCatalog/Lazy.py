##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
__doc__='''$Id$'''
__version__='$Revision: 1.9 $'[11:-2]

from itertools import islice, count


class Lazy:

    # Allow (reluctantly) access to unprotected attributes
    __allow_access_to_unprotected_subobjects__=1

    def __repr__(self): return `list(self)`

    def __len__(self):
        # This is a worst-case len, subclasses should try to do better
        try: return self._len
        except AttributeError: pass

        l=len(self._data)
        while 1:
            try:
                self[l]
                l=l+1
            except:
                self._len=l
                return l
                

    def __add__(self, other):
        if not isinstance(other, Lazy):
            raise TypeError(
                "Can not concatenate objects. Both must be lazy sequences.")
        return LazyCat([self, other])

    def __getslice__(self,i1,i2):
        r=[]
        for i in islice(count(i1), i2-i1):
            try: r.append(self[i])
            except IndexError: return r
        return r

    slice=__getslice__

class LazyCat(Lazy):
    # Lazy concatenation of one or more sequences.  Should be handy
    # for accessing small parts of big searches.

    def __init__(self, sequences, length=None):
        if len(sequences) < 100:
            # Optimize structure of LazyCats to avoid nesting
            # We don't do this for large numbers of input sequences
            # to make instantiation faster instead
            flattened_seq = []
            for s in sequences:
                if isinstance(s, LazyCat):
                    # If one of the sequences passed is itself a LazyCat, add
                    # its base sequences rather than nest LazyCats
                    flattened_seq.extend(s._seq)
                else:
                    flattened_seq.append(s)
            sequences = flattened_seq
        self._seq=sequences
        self._data=[]
        self._sindex=0
        self._eindex=-1
        if length is not None: self._len=length

    def __getitem__(self,index):

        data=self._data
        try: seq=self._seq
        except AttributeError: return data[index]

        i=index
        if i < 0: i=len(self)+i
        if i < 0: raise IndexError, index

        ind=len(data)
        if i < ind: return data[i]
        ind=ind-1

        sindex=self._sindex
        try: s=seq[sindex]
        except: raise IndexError, index
        eindex=self._eindex
        while i > ind:
            try:
                eindex=eindex+1
                v=s[eindex]
                data.append(v)
                ind=ind+1
            except IndexError:
                self._sindex=sindex=sindex+1
                try: s=self._seq[sindex]
                except:
                    del self._seq
                    del self._sindex
                    del self._eindex
                    raise IndexError, index
                self._eindex=eindex=-1
        self._eindex=eindex
        return data[i]
        
    def __len__(self):
        # Make len of LazyCat only as expensive as the lens 
        # of its underlying sequences
        try:
            return self._len
        except:
            try:
                l = 0
                for s in self._seq:
                    l += len(s)
            except AttributeError:
                l = len(self._data)
            self._len = l
            return l

class LazyMap(Lazy):
    # Act like a sequence, but get data from a filtering process.
    # Don't access data until necessary

    def __init__(self, func, seq, length=None):
        self._seq = seq
        self._data = {}
        self._func = func
        if length is not None:
            self._len = length
        else:
            self._len = len(seq)

    def __getitem__(self, index):
        data = self._data
        if index in data:
            return data[index]
        value = data[index] = self._func(self._seq[index])
        return value

class LazyFilter(Lazy):
    # Act like a sequence, but get data from a filtering process.
    # Don't access data until necessary. Only data for which test(data) 
    # returns true will be considered part of the set.

    def __init__(self, test, seq):
        self._seq=seq
        self._data=[]
        self._eindex=-1
        self._test=test

    def __getitem__(self,index):

        data=self._data
        try: s=self._seq
        except AttributeError: return data[index]

        i=index
        if i < 0: i=len(self)+i
        if i < 0: raise IndexError, index

        ind=len(data)
        if i < ind: return data[i]
        ind=ind-1

        test=self._test
        e=self._eindex
        while i > ind:
            try:
                e=e+1
                v=s[e]
                if test(v):
                    data.append(v)
                    ind=ind+1
            except IndexError:
                del self._test
                del self._seq
                del self._eindex
                raise IndexError, index
        self._eindex=e
        return data[i]

class LazyMop(Lazy):
    # Act like a sequence, but get data from a filtering process.
    # Don't access data until necessary.  If the filter raises an exception
    # for a given item, then that item isn't included in the sequence.
    
    def __init__(self, test, seq):
        self._seq=seq
        self._data=[]
        self._eindex=-1
        self._test=test

    def __getitem__(self,index):

        data=self._data
        try: s=self._seq
        except AttributeError: return data[index]

        i=index
        if i < 0: i=len(self)+i
        if i < 0: raise IndexError, index

        ind=len(data)
        if i < ind: return data[i]
        ind=ind-1

        test=self._test
        e=self._eindex
        while i > ind:
            try:
                e=e+1
                v=s[e]
                try:
                    v=test(v)
                    data.append(v)
                    ind=ind+1
                except: pass
            except IndexError:
                del self._test
                del self._seq
                del self._eindex
                raise IndexError, index
        self._eindex=e
        return data[i]

class LazyValues(Lazy):
    """Given a sequence of two tuples typically (key, value) act as
    though we are just a list of the values lazily"""
    
    def __init__(self, seq):
        self._seq = seq
    
    def __len__(self):
        return len(self._seq)
    
    def __getitem__(self, index):
        return self._seq[index][1]
    
    def __getslice__(self, start, end):
        return self.__class__(self._seq[start:end])
        
    slice = __getslice__
