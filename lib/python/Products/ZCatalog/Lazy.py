##############################################################################
# 
# Zope Public License (ZPL) Version 0.9.7
# ---------------------------------------
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
__doc__='''$Id: Lazy.py,v 1.3 2001/01/15 16:29:23 petrilli Exp $'''
__version__='$Revision: 1.3 $'[11:-2]


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
        for i in range(i1,i2):
            try: r.append(self[i])
            except IndexError: return r
        return r

    slice=__getslice__

class LazyCat(Lazy):
    # Lazy concatenation of one or more sequences.  Should be handy
    # for accessing small parts of big searches.
    
    def __init__(self, sequences):
        self._seq=sequences
        self._data=[]
        self._sindex=0
        self._eindex=-1

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

    def __init__(self,func,seq):
        self._seq=seq
        self._len=len(seq)
        self._data=[]
        self._func=func

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

    def __init__(self,test,seq):
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

    def __init__(self,test,seq):
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
