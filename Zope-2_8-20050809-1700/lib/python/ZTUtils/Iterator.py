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
"""Iterator class

Unlike the builtin iterators of Python 2.2+, these classes are
designed to maintain information about the state of an iteration.
The Iterator() function accepts either a sequence or a Python
iterator.  The next() method fetches the next item, and returns
true if it succeeds.

$Id$
"""

class Iterator:
    '''Simple Iterator class'''

    __allow_access_to_unprotected_subobjects__ = 1

    nextIndex = 0
    def __init__(self, seq):
        self.seq = seq
        if iterInner._supports(seq, self):
            self._inner = iterInner
            self._prep_next = iterInner.prep_next
            return
        raise TypeError, "Iterator does not support %s" % `seq`

    def __getattr__(self, name):
        try:
            inner = getattr(self._inner, 'it_' + name)
        except AttributeError:
            raise AttributeError, name
        return inner(self)

    def next(self):
        if not (hasattr(self, '_next') or self._prep_next(self)):
            return 0
        self.index = i = self.nextIndex
        self.nextIndex = i+1
        self._advance(self)
        return 1

    def _advance(self, it):
        self.item = self._next
        del self._next
        del self.end
        self._advance = self._inner.advance
        self.start = 1

    def number(self): return self.nextIndex

    def even(self): return not self.index % 2

    def odd(self): return self.index % 2

    def parity(self):
        if self.index % 2:
            return 'odd'
        return 'even'

    def letter(self, base=ord('a'), radix=26):
        index = self.index
        s = ''
        while 1:
            index, off = divmod(index, radix)
            s = chr(base + off) + s
            if not index: return s

    def Letter(self):
        return self.letter(base=ord('A'))

    def Roman(self, rnvalues=(
                    (1000,'M'),(900,'CM'),(500,'D'),(400,'CD'),
                    (100,'C'),(90,'XC'),(50,'L'),(40,'XL'),
                    (10,'X'),(9,'IX'),(5,'V'),(4,'IV'),(1,'I')) ):
        n = self.index + 1
        s = ''
        for v, r in rnvalues:
            rct, n = divmod(n, v)
            s = s + r * rct
        return s

    def roman(self):
        return self.Roman().lower()

    def first(self, name=None):
        if self.start: return 1
        return not self.same_part(name, self._last, self.item)

    def last(self, name=None):
        if self.end: return 1
        return not self.same_part(name, self.item, self._next)

    def length(self):
        return len(self.seq)

    def same_part(self, name, ob1, ob2):
        if name is None:
            return ob1 == ob2
        no = []
        return getattr(ob1, name, no) == getattr(ob2, name, no) is not no

    def __iter__(self):
        return IterIter(self)

class InnerBase:
    '''Base Inner class for Iterators'''
    # Prep sets up ._next and .end
    def prep_next(self, it):
        it.next = self.no_next
        it.end = 1
        return 0

    # Advance knocks them down
    def advance(self, it):
        it._last = it.item
        it.item = it._next
        del it._next
        del it.end
        it.start = 0

    def no_next(self, it):
        return 0

    def it_end(self, it):
        if hasattr(it, '_next'):
            return 0
        return not self.prep_next(it)

class IterInner(InnerBase):
    '''Iterator inner class for objects with Python iterators'''

    def _supports(self, ob, it):
        try:
            it.iter = iter(ob)
            return 1
        except:
            return 0

    def prep_next(self, it):
        try:
            it._next = it.iter.next()
        except StopIteration:
            it._prep_next = self.no_next
            it.end = 1
            return 0
        it.end = 0
        return 1

class IterIter:
    def __init__(self, it):
        self.it = it
        self.skip = it.nextIndex > 0 and not it.end
    def next(self):
        it = self.it
        if self.skip:
            self.skip = 0
            return it.item
        if it.next():
            return it.item
        raise StopIteration

iterInner = IterInner()
