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
"""Batch class, for iterating over a sequence in batches
"""

from ExtensionClass import Base

class LazyPrevBatch(Base):
    def __of__(self, parent):
        return Batch(parent._sequence, parent._size,
                     parent.first - parent._size + parent.overlap, 0,
                     parent.orphan, parent.overlap)

class LazyNextBatch(Base):
    def __of__(self, parent):
        try: parent._sequence[parent.end]
        except IndexError: return None
        return Batch(parent._sequence, parent._size,
                     parent.end - parent.overlap, 0,
                     parent.orphan, parent.overlap)

class LazySequenceLength(Base):
    def __of__(self, parent):
        parent.sequence_length = l = len(parent._sequence)
        return l

class Batch(Base):
    """Create a sequence batch"""
    __allow_access_to_unprotected_subobjects__ = 1

    previous = LazyPrevBatch()
    next = LazyNextBatch()
    sequence_length = LazySequenceLength()

    def __init__(self, sequence, size, start=0, end=0,
                 orphan=0, overlap=0):
        '''Encapsulate "sequence" in batches of "size".

        Arguments: "start" and "end" are 0-based indexes into the
        sequence.  If the next batch would contain no more than
        "orphan" elements, it is combined with the current batch.
        "overlap" is the number of elements shared by adjacent
        batches.  If "size" is not specified, it is computed from
        "start" and "end".  Failing that, it is 7.

        Attributes: Note that the "start" attribute, unlike the
        argument, is a 1-based index (I know, lame).  "first" is the
        0-based index.  "length" is the actual number of elements in
        the batch.

        "sequence_length" is the length of the original, unbatched, sequence
        '''

        start = start + 1

        start,end,sz = opt(start,end,size,orphan,sequence)

        self._sequence = sequence
        self.size = sz
        self._size = size
        self.start = start
        self.end = end
        self.orphan = orphan
        self.overlap = overlap
        self.first = max(start - 1, 0)
        self.length = self.end - self.first
        if self.first == 0:
            self.previous = None


    def __getitem__(self, index):
        if index < 0:
            if index + self.end < self.first: raise IndexError, index
            return self._sequence[index + self.end]

        if index >= self.length: raise IndexError, index
        return self._sequence[index+self.first]

    def __len__(self):
        return self.length

def opt(start,end,size,orphan,sequence):
    if size < 1:
        if start > 0 and end > 0 and end >= start:
            size=end+1-start
        else: size=7

    if start > 0:

        try: sequence[start-1]
        except IndexError: start=len(sequence)

        if end > 0:
            if end < start: end=start
        else:
            end=start+size-1
            try: sequence[end+orphan]
            except IndexError: end=len(sequence)
    elif end > 0:
        try: sequence[end-1]
        except IndexError: end=len(sequence)
        start=end+1-size
        if start - 1 < orphan: start=1
    else:
        start=1
        end=start+size-1
        try: sequence[end+orphan-1]
        except IndexError: end=len(sequence)
    return start,end,size
