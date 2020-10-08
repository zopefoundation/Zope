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

import unittest


class BaseSequenceTest:

    def _compare(self, lseq, seq):
        self.assertEqual(len(lseq), len(seq))
        self.assertEqual(list(lseq), seq)

    def test_actual_result_count(self):
        lcat = self._createLSeq(list(range(10)))
        self.assertEqual(len(lcat), 10)
        self.assertEqual(lcat.actual_result_count, 10)

        lcat.actual_result_count = 20
        self.assertEqual(len(lcat), 10)
        self.assertEqual(lcat.actual_result_count, 20)


class TestLazyCat(unittest.TestCase, BaseSequenceTest):

    def _createLSeq(self, *sequences):
        from ZTUtils.Lazy import LazyCat
        return LazyCat(sequences)

    def _createLValues(self, seq):
        from ZTUtils.Lazy import LazyValues
        return LazyValues(seq)

    def test_empty(self):
        lcat = self._createLSeq([])
        self._compare(lcat, [])
        self.assertEqual(lcat.actual_result_count, 0)

    def test_repr(self):
        lcat = self._createLSeq([0, 1])
        self.assertEqual(repr(lcat), repr([0, 1]))

    def test_init_single(self):
        seq = list(range(10))
        lcat = self._createLSeq(seq)
        self._compare(lcat, seq)
        self.assertEqual(lcat.actual_result_count, 10)

    def test_add(self):
        seq1 = list(range(10))
        seq2 = list(range(10, 20))
        lcat1 = self._createLSeq(seq1)
        lcat2 = self._createLSeq(seq2)
        lcat = lcat1 + lcat2
        self._compare(lcat, list(range(20)))
        self.assertEqual(lcat.actual_result_count, 20)

    def test_add_after_getitem(self):
        seq1 = list(range(10))
        seq2 = list(range(10, 20))
        lcat1 = self._createLSeq(seq1)
        lcat2 = self._createLSeq(seq2)
        # turning lcat1 into a list will flatten it into _data and remove _seq
        list(lcat1)
        lcat = lcat1 + lcat2
        self._compare(lcat, list(range(20)))
        self.assertEqual(lcat.actual_result_count, 20)

    def test_init_multiple(self):
        from string import ascii_letters
        from string import hexdigits
        seq1 = list(range(10))
        seq2 = list(hexdigits)
        seq3 = list(ascii_letters)
        lcat = self._createLSeq(seq1, seq2, seq3)
        self._compare(lcat, seq1 + seq2 + seq3)

    def test_init_nested(self):
        from string import ascii_letters
        from string import hexdigits
        seq1 = list(range(10))
        seq2 = list(hexdigits)
        seq3 = list(ascii_letters)
        lcat = self._createLSeq(
            *[self._createLSeq(seq) for seq in (seq1, seq2, seq3)])
        self._compare(lcat, seq1 + seq2 + seq3)

    def test_slicing(self):
        from string import ascii_letters
        from string import hexdigits
        seq1 = list(range(10))
        seq2 = list(hexdigits)
        seq3 = list(ascii_letters)
        lcat = self._createLSeq(
            *[self._createLSeq(seq) for seq in (seq1, seq2, seq3)])
        self._compare(lcat[5:-5], seq1[5:] + seq2 + seq3[:-5])

    def test_length(self):
        # Unaccessed length
        lcat = self._createLSeq(list(range(10)))
        self.assertEqual(len(lcat), 10)
        self.assertEqual(lcat.actual_result_count, 10)

        # Accessed in the middle
        lcat = self._createLSeq(list(range(10)))
        lcat[4]
        self.assertEqual(len(lcat), 10)
        self.assertEqual(lcat.actual_result_count, 10)

        # Accessed after the lcat is accessed over the whole range
        lcat = self._createLSeq(list(range(10)))
        lcat[:]
        self.assertEqual(len(lcat), 10)
        self.assertEqual(lcat.actual_result_count, 10)

    def test_actual_result_count(self):
        # specify up-front
        lcat = self._createLSeq(list(range(10)))
        lcat.actual_result_count = 100

        self.assertEqual(len(lcat), 10)
        self.assertEqual(lcat.actual_result_count, 100)

        lvalues = self._createLValues([])
        self.assertEqual(len(lvalues), 0)
        self.assertEqual(lvalues.actual_result_count, 0)

        combined = lvalues + lcat
        self.assertEqual(len(combined), 10)
        self.assertEqual(combined.actual_result_count, 100)

        combined.actual_result_count = 5
        self.assertEqual(combined.actual_result_count, 5)


class TestLazyMap(TestLazyCat):

    def _createLSeq(self, *seq):
        return self._createLMap(lambda x: x, *seq)

    def _createLMap(self, mapfunc, *seq):
        from ZTUtils.Lazy import LazyMap
        totalseq = []
        for s in seq:
            totalseq.extend(s)
        return LazyMap(mapfunc, totalseq)

    def test_map(self):
        from string import ascii_letters
        from string import hexdigits
        seq1 = list(range(10))
        seq2 = list(hexdigits)
        seq3 = list(ascii_letters)

        def to_lower(x):
            return str(x).lower()

        lmap = self._createLMap(to_lower, seq1, seq2, seq3)
        self._compare(lmap, [str(x).lower() for x in (seq1 + seq2 + seq3)])

    def testMapFuncIsOnlyCalledAsNecessary(self):
        seq = list(range(10))
        count = [0]  # closure only works with list, and `nonlocal` in py3

        def func(x):
            count[0] += 1
            return x

        lmap = self._createLMap(func, seq)
        self.assertEqual(lmap[5], 5)
        self.assertEqual(count[0], 1)


class TestLazyFilter(TestLazyCat):

    def _createLSeq(self, *seq):
        return self._createLFilter(lambda x: True, *seq)

    def _createLFilter(self, filter, *seq):
        from ZTUtils.Lazy import LazyFilter
        totalseq = []
        for s in seq:
            totalseq.extend(s)
        return LazyFilter(filter, totalseq)

    def test_filter(self):
        from string import ascii_letters
        from string import hexdigits
        seq1 = list(range(10))
        seq2 = list(hexdigits)
        seq3 = list(ascii_letters)

        def is_alpha(x):
            return str(x).isalpha()

        lmap = self._createLFilter(is_alpha, seq1, seq2, seq3)
        self._compare(lmap, seq2[10:] + seq3)

    def test_length_with_filter(self):
        from string import ascii_letters
        lower_length = len([x for x in ascii_letters if x.islower()])

        # Unaccessed length
        lfilter = self._createLFilter(
            lambda x: x.islower(), list(ascii_letters))
        self.assertEqual(len(lfilter), lower_length)

        # Accessed in the middle
        lfilter = self._createLFilter(
            lambda x: x.islower(), list(ascii_letters))
        lfilter[13]
        self.assertEqual(len(lfilter), lower_length)

        # Accessed after the lcat is accessed over the whole range
        lfilter = self._createLFilter(
            lambda x: x.islower(), list(ascii_letters))
        lfilter[:]
        self.assertEqual(len(lfilter), lower_length)


class TestLazyMop(TestLazyCat):

    def _createLSeq(self, *seq):
        return self._createLMop(lambda x: x, *seq)

    def _createLMop(self, mapfunc, *seq):
        from ZTUtils.Lazy import LazyMop
        totalseq = []
        for s in seq:
            totalseq.extend(s)
        return LazyMop(mapfunc, totalseq)

    def test_mop(self):
        from string import ascii_letters
        from string import hexdigits
        seq1 = list(range(10))
        seq2 = list(hexdigits)
        seq3 = list(ascii_letters)

        def filter(x):
            if isinstance(x, int):
                raise ValueError
            return x.lower()

        lmop = self._createLMop(filter, seq1, seq2, seq3)
        self._compare(lmop, [str(x).lower() for x in (seq2 + seq3)])

    def test_length_with_filter(self):
        from string import ascii_letters
        letter_length = len(ascii_letters)
        seq = list(range(10)) + list(ascii_letters)

        def filter(x):
            if isinstance(x, int):
                raise ValueError
            return x.lower()

        # Unaccessed length
        lmop = self._createLMop(filter, seq)
        self.assertEqual(len(lmop), letter_length)

        # Accessed in the middle
        lmop = self._createLMop(filter, seq)
        lmop[26]
        self.assertEqual(len(lmop), letter_length)

        # Accessed after the lcat is accessed over the whole range
        lmop = self._createLMop(filter, ascii_letters)
        lmop[:]
        self.assertEqual(len(lmop), letter_length)


class TestLazyValues(unittest.TestCase, BaseSequenceTest):

    def _createLSeq(self, seq):
        from ZTUtils.Lazy import LazyValues
        return LazyValues(seq)

    def test_empty(self):
        lvals = self._createLSeq([])
        self._compare(lvals, [])

    def test_values(self):
        from string import ascii_letters
        seq = list(zip(ascii_letters, list(range(10))))
        lvals = self._createLSeq(seq)
        self._compare(lvals, list(range(10)))

    def test_slicing(self):
        from string import ascii_letters
        seq = list(zip(ascii_letters, list(range(10))))
        lvals = self._createLSeq(seq)
        self._compare(lvals[2:-2], list(range(2, 8)))
