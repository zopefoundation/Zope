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

######################################################################
# Sequence batching support

from . import util


__allow_access_to_unprotected_subobjects__ = {'batch': 1}
__roles__ = None


class batch(util.Base):
    """Create a sequence batch"""

    def __init__(self, sequence, size, start=0, end=0,
                 orphan=3, overlap=0):

        start = start + 1

        start, end, sz = opt(start, end, size, orphan, sequence)

        self._last = end - 1
        self._first = start - 1

        self._sequence = sequence
        self._size = size
        self._start = start
        self._end = end
        self._orphan = orphan
        self._overlap = overlap

    def previous_sequence(self):
        return self._first

    def previous_sequence_end_number(self):
        start, end, spam = opt(0, self._start - 1 + self._overlap,
                               self._size, self._orphan, self._sequence)
        return end

    def previous_sequence_start_number(self):
        start, end, spam = opt(0, self._start - 1 + self._overlap,
                               self._size, self._orphan, self._sequence)
        return start

    def previous_sequence_end_item(self):
        start, end, spam = opt(0, self._start - 1 + self._overlap,
                               self._size, self._orphan, self._sequence)
        return self._sequence[end - 1]

    def previous_sequence_start_item(self):
        start, end, spam = opt(0, self._start - 1 + self._overlap,
                               self._size, self._orphan, self._sequence)
        return self._sequence[start - 1]

    def next_sequence_end_number(self):
        start, end, spam = opt(self._end + 1 - self._overlap, 0,
                               self._size, self._orphan, self._sequence)
        return end

    def next_sequence_start_number(self):
        start, end, spam = opt(self._end + 1 - self._overlap, 0,
                               self._size, self._orphan, self._sequence)
        return start

    def next_sequence_end_item(self):
        start, end, spam = opt(self._end + 1 - self._overlap, 0,
                               self._size, self._orphan, self._sequence)
        return self._sequence[end - 1]

    def next_sequence_start_item(self):
        start, end, spam = opt(self._end + 1 - self._overlap, 0,
                               self._size, self._orphan, self._sequence)
        return self._sequence[start - 1]

    def next_sequence(self):
        try:
            self._sequence[self._end]
        except IndexError:
            return 0
        else:
            return 1

    def __getitem__(self, index):
        if index > self._last:
            raise IndexError(index)
        return self._sequence[index + self._first]


def opt(start, end, size, orphan, sequence):
    if size < 1:
        if start > 0 and end > 0 and end >= start:
            size = end + 1 - start
        else:
            size = 7

    if start > 0:
        try:
            sequence[start - 1]
        except Exception:
            start = len(sequence)

        if end > 0:
            if end < start:
                end = start
        else:
            end = start + size - 1
            try:
                sequence[end + orphan - 1]
            except Exception:
                end = len(sequence)
    elif end > 0:
        try:
            sequence[end - 1]
        except Exception:
            end = len(sequence)
        start = end + 1 - size
        if start - 1 < orphan:
            start = 1
    else:
        start = 1
        end = start + size - 1
        try:
            sequence[end + orphan - 1]
        except Exception:
            end = len(sequence)
    return start, end, size
