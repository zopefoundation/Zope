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
# FOR A PARTICULAR PURPOSE.
#
##############################################################################

"""NBest Interface.

An NBest object remembers the N best-scoring items ever passed to its
.add(item, score) method.  If .add() is called M times, the worst-case
number of comparisons performed overall is M * log2(N).
"""


from zope.interface import Interface

class INBest(Interface):
    """Interface for an N-Best chooser."""

    def add(item, score):
        """Record that item 'item' has score 'score'.  No return value.

        The N best-scoring items are remembered, where N was passed to
        the constructor.  'item' can by anything.  'score' should be
        a number, and larger numbers are considered better.
        """

    def addmany(sequence):
        """Like "for item, score in sequence: self.add(item, score)".

        This is simply faster than calling add() len(seq) times.
        """

    def getbest():
        """Return the (at most) N best-scoring items as a sequence.

        The return value is a sequence of 2-tuples, (item, score), with
        the largest score first.  If .add() has been called fewer than
        N times, this sequence will contain fewer than N pairs.
        """

    def pop_smallest():
        """Return and remove the (item, score) pair with lowest score.

        If len(self) is 0, raise IndexError.

        To be cleaer, this is the lowest score among the N best-scoring
        seen so far.  This is most useful if the capacity of the NBest
        object is never exceeded, in which case  pop_smallest() allows
        using the object as an ordinary smallest-in-first-out priority
        queue.
        """

    def __len__():
        """Return the number of (item, score) pairs currently known.

        This is N (the value passed to the constructor), unless .add()
        has been called fewer than N times.
        """

    def capacity():
        """Return the maximum number of (item, score) pairs.

        This is N (the value passed to the constructor).
        """
