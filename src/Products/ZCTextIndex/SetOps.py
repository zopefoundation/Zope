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

"""SetOps -- Weighted intersections and unions applied to many inputs."""

from BTrees.IIBTree import IIBucket
from BTrees.IIBTree import weightedIntersection
from BTrees.IIBTree import weightedUnion

from Products.ZCTextIndex.NBest import NBest

def mass_weightedIntersection(L):
    "A list of (mapping, weight) pairs -> their weightedIntersection IIBucket."
    L = [(x, wx) for (x, wx) in L if x is not None]
    if len(L) < 2:
        return _trivial(L)
    # Intersect with smallest first.  We expect the input maps to be
    # IIBuckets, so it doesn't hurt to get their lengths repeatedly
    # (len(Bucket) is fast; len(BTree) is slow).
    L.sort(lambda x, y: cmp(len(x[0]), len(y[0])))
    (x, wx), (y, wy) = L[:2]
    dummy, result = weightedIntersection(x, y, wx, wy)
    for x, wx in L[2:]:
        dummy, result = weightedIntersection(result, x, 1, wx)
    return result

def mass_weightedUnion(L):
    "A list of (mapping, weight) pairs -> their weightedUnion IIBucket."
    if len(L) < 2:
        return _trivial(L)
    # Balance unions as closely as possible, smallest to largest.
    merge = NBest(len(L))
    for x, weight in L:
        merge.add((x, weight), len(x))
    while len(merge) > 1:
        # Merge the two smallest so far, and add back to the queue.
        (x, wx), dummy = merge.pop_smallest()
        (y, wy), dummy = merge.pop_smallest()
        dummy, z = weightedUnion(x, y, wx, wy)
        merge.add((z, 1), len(z))
    (result, weight), dummy = merge.pop_smallest()
    return result

def _trivial(L):
    # L is empty or has only one (mapping, weight) pair.  If there is a
    # pair, we may still need to multiply the mapping by its weight.
    assert len(L) <= 1
    if len(L) == 0:
        return IIBucket()
    [(result, weight)] = L
    if weight != 1:
        dummy, result = weightedUnion(IIBucket(), result, 0, weight)
    return result
