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
__doc__='''$Id: Lazy.py,v 1.6 2001/11/28 15:51:09 matt Exp $'''
__version__='$Revision: 1.6 $'[11:-2]


class Lazy:

    # Allow (reluctantly) access to unprotected attributes
    __allow_access_to_unprotected_subobjects__=1

    def __repr__(self): return `list(self)`
    
    def __len__(self):

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
        try:
            for base in other.__class__.__bases__:
                if base.__name__ == 'Lazy':
                    break
            else:
                raise TypeError
        except:
            raise TypeError, "Can not concatenate objects. Both must be lazy sequences."

        if self.__class__.__name__ == 'LazyCat':
            if hasattr(self, '_seq'):
                seq = self._seq
            else:
                seq = [self._data]
        else:
            seq = [self]

        if other.__class__.__name__ == 'LazyCat':
            if hasattr(other, '_seq'):
                seq = seq + other._seq
            else:
                seq.append(other._data)
        else:
            seq.append(other)

        return LazyCat(seq)
    
    def __getslice__(self,i1,i2):
        r=[]
        for i in xrange(i1,i2):
            try: r.append(self[i])
            except IndexError: return r
        return r

    slice=__getslice__

class LazyCat(Lazy):
    # Lazy concatenation of one or more sequences.  Should be handy
    # for accessing small parts of big searches.
    
    def __init__(self, sequences, length=None):
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

class LazyMap(Lazy):
    # Act like a sequence, but get data from a filtering process.
    # Don't access data until necessary

    def __init__(self, func, seq, length=None):
        self._seq=seq
        self._data=[]
        self._func=func
        if length is not None: self._len=length
        else: self._len = len(seq)

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

        func=self._func
        while i > ind:
            try:
                ind=ind+1
                data.append(func(s[ind]))
            except IndexError:
                del self._func
                del self._seq
                raise IndexError, index
        return data[i]

class LazyFilter(Lazy):
    # Act like a sequence, but get data from a filtering process.
    # Don't access data until necessary

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
    # Don't access data until necessary

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
