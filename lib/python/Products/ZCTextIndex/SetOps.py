##############################################################################
#
# Copyright (c) 2001, 2002 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################

"""SetOps -- Weighted intersections and unions applied to many inputs."""

from BTrees.IIBTree import IIBTree, weightedIntersection, weightedUnion

from Products.ZCTextIndex.NBest import NBest

def mass_weightedIntersection(L):
    "A list of (mapping, weight) pairs -> their weightedIntersection IIBTree."
    L = [(map, weight) for (map, weight) in L if map is not None]
    if not L:
        return IIBTree()
    # Intersect with smallest first.
    L.sort(lambda x, y: cmp(len(x[0]), len(y[0])))
    x, w = L[0]
    dummy, result = weightedUnion(IIBTree(), x, 1, w)
    for x, w in L[1:]:
        dummy, result = weightedIntersection(result, x, 1, w)
    return result

def mass_weightedUnion(L):
    "A list of (mapping, weight) pairs -> their weightedUnion IIBTree."
    if not L:
        return IIBTree()
    if len(L) == 1:
        # Have to do a union in order to get the input's values
        # multiplied by the weight.
        x, weight = L[0]
        dummy, result = weightedUnion(IIBTree(), x, 1, weight)
        return result
    # Balance unions as closely as possible, smallest to largest.
    assert len(L) > 1
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
