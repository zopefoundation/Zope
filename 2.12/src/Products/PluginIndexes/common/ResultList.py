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

from BTrees.IIBTree import difference
from BTrees.IIBTree import IIBucket
from BTrees.IIBTree import weightedIntersection
from BTrees.IIBTree import weightedUnion
from BTrees.OOBTree import OOSet
from BTrees.OOBTree import union

class ResultList:

    def __init__(self, d, words, index):
        self._index = index

        if type(words) is not OOSet:
            words=OOSet(words)
        self._words = words

        if (type(d) is tuple):
            d = IIBucket((d,))
        elif type(d) is not IIBucket:
            d = IIBucket(d)

        self._dict=d
        self.__getitem__=d.__getitem__
        try: self.__nonzero__=d.__nonzero__
        except: pass
        self.get=d.get

    def __nonzero__(self):
        return not not self._dict

    def bucket(self):
        return self._dict

    def keys(self):
        return self._dict.keys()

    def has_key(self, key):
        return self._dict.has_key(key)

    def items(self):
        return self._dict.items()

    def __and__(self, x):
        return self.__class__(
            weightedIntersection(self._dict, x._dict)[1],
            union(self._words, x._words),
            self._index,
            )

    def and_not(self, x):
        return self.__class__(
            difference(self._dict, x._dict),
            self._words,
            self._index,
            )

    def __or__(self, x):
        return self.__class__(
            weightedUnion(self._dict, x._dict)[1],
            union(self._words, x._words),
            self._index,
            )
        # return self.__class__(result, self._words+x._words, self._index)

    def near(self, x):
        result = IIBucket()
        dict = self._dict
        xdict = x._dict
        xhas = xdict.has_key
        positions = self._index.positions
        for id, score in dict.items():
            if not xhas(id): continue
            p=(map(lambda i: (i,0), positions(id,self._words))+
               map(lambda i: (i,1), positions(id,x._words)))
            p.sort()
            d = lp = 9999
            li = None
            lsrc = None
            for i,src in p:
                if i is not li and src is not lsrc and li is not None:
                    d = min(d,i-li)
                li = i
                lsrc = src
            if d==lp: score = min(score,xdict[id]) # synonyms
            else: score = (score+xdict[id])/d
            result[id] = score

        return self.__class__(
            result, union(self._words, x._words), self._index)
