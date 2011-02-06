##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
"""NBest

An NBest object remembers the N best-scoring items ever passed to its
.add(item, score) method.  If .add() is called M times, the worst-case
number of comparisons performed overall is M * log2(N).
"""

from bisect import bisect
from zope.interface import implements

from Products.ZCTextIndex.INBest import INBest

class NBest:
    implements(INBest)

    def __init__(self, N):
        "Build an NBest object to remember the N best-scoring objects."

        if N < 1:
            raise ValueError("NBest() argument must be at least 1")
        self._capacity = N

        # This does a very simple thing with sorted lists.  For large
        # N, a min-heap can be unboundedly better in terms of data
        # movement time.
        self._scores = []
        self._items = []

    def __len__(self):
        return len(self._scores)

    def capacity(self):
        return self._capacity

    def add(self, item, score):
        self.addmany([(item, score)])

    def addmany(self, sequence):
        scores, items, capacity = self._scores, self._items, self._capacity
        n = len(scores)
        for item, score in sequence:
            # When we're in steady-state, the usual case is that we're filled
            # to capacity, and that an incoming item is worse than any of
            # the best-seen so far.
            if n >= capacity and score <= scores[0]:
                continue
            i = bisect(scores, score)
            scores.insert(i, score)
            items.insert(i, item)
            if n == capacity:
                del items[0], scores[0]
            else:
                n += 1
        assert n == len(scores)

    def getbest(self):
        result = zip(self._items, self._scores)
        result.reverse()
        return result

    def pop_smallest(self):
        if self._scores:
            return self._items.pop(0), self._scores.pop(0)
        raise IndexError("pop_smallest() called on empty NBest object")
