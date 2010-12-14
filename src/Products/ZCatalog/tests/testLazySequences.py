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
"""Unittests for Lazy sequence classes

$Id$"""

import unittest

class BaseSequenceTest(unittest.TestCase):
    def _compare(self, lseq, seq):
        self.assertEqual(len(lseq), len(seq))
        self.assertEqual(list(lseq), seq)


class TestLazyCat(BaseSequenceTest):
    def _createLSeq(self, *sequences):
        from Products.ZCatalog.Lazy import LazyCat
        return LazyCat(sequences)

    def testEmpty(self):
        lcat = self._createLSeq([])
        self._compare(lcat, [])

    def testSingleSequence(self):
        seq = range(10)
        lcat = self._createLSeq(seq)
        self._compare(lcat, seq)

    def testMultipleSequences(self):
        from string import hexdigits, letters
        seq1 = range(10)
        seq2 = list(hexdigits)
        seq3 = list(letters)
        lcat = self._createLSeq(seq1, seq2, seq3)
        self._compare(lcat, seq1 + seq2 + seq3)

    def testNestedLazySequences(self):
        from string import hexdigits, letters
        seq1 = range(10)
        seq2 = list(hexdigits)
        seq3 = list(letters)
        lcat = apply(self._createLSeq,
            [self._createLSeq(seq) for seq in (seq1, seq2, seq3)])
        self._compare(lcat, seq1 + seq2 + seq3)

    def testSlicedSequences(self):
        from string import hexdigits, letters
        seq1 = range(10)
        seq2 = list(hexdigits)
        seq3 = list(letters)
        lcat = apply(self._createLSeq,
            [self._createLSeq(seq) for seq in (seq1, seq2, seq3)])
        self._compare(lcat[5:-5], seq1[5:] + seq2 + seq3[:-5])    

    def testConsistentLength(self):
        # Unaccessed length
        lcat = self._createLSeq(range(10))
        self.assertEqual(len(lcat), 10)

        # Accessed in the middle
        lcat = self._createLSeq(range(10))
        lcat[4]
        self.assertEqual(len(lcat), 10)

        # Accessed after the lcat is accessed over the whole range
        lcat = self._createLSeq(range(10))
        lcat[:]
        self.assertEqual(len(lcat), 10)


class TestLazyMap(TestLazyCat):
    def _createLSeq(self, *seq):
        return self._createLMap(lambda x: x, *seq)

    def _createLMap(self, mapfunc, *seq):
        from Products.ZCatalog.Lazy import LazyMap
        totalseq = []
        for s in seq:
            totalseq.extend(s)
        return LazyMap(mapfunc, totalseq)

    def testMap(self):
        from string import hexdigits, letters
        seq1 = range(10)
        seq2 = list(hexdigits)
        seq3 = list(letters)
        filter = lambda x: str(x).lower()
        lmap = self._createLMap(filter, seq1, seq2, seq3)
        self._compare(lmap, [str(x).lower() for x in (seq1 + seq2 + seq3)])

    def testMapFuncIsOnlyCalledAsNecessary(self):
        seq = range(10)
        count = [0]     # closure only works with list, and `nonlocal` in py3
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
        from Products.ZCatalog.Lazy import LazyFilter
        totalseq = []
        for s in seq:
            totalseq.extend(s)
        return LazyFilter(filter, totalseq)

    def testFilter(self):
        from string import hexdigits, letters
        seq1 = range(10)
        seq2 = list(hexdigits)
        seq3 = list(letters)
        filter = lambda x: str(x).isalpha()
        lmap = self._createLFilter(filter, seq1, seq2, seq3)
        self._compare(lmap, seq2[10:] + seq3)

    def testConsistentLengthWithFilter(self):
        from string import letters

        # Unaccessed length
        lfilter = self._createLFilter(lambda x: x.islower(), list(letters))
        self.assertEqual(len(lfilter), 26)

        # Accessed in the middle
        lfilter = self._createLFilter(lambda x: x.islower(), list(letters))
        lfilter[13]
        self.assertEqual(len(lfilter), 26)

        # Accessed after the lcat is accessed over the whole range
        lfilter = self._createLFilter(lambda x: x.islower(), list(letters))
        lfilter[:]
        self.assertEqual(len(lfilter), 26)


class TestLazyMop(TestLazyCat):
    def _createLSeq(self, *seq):
        return self._createLMop(lambda x: x, *seq)

    def _createLMop(self, mapfunc, *seq):
        from Products.ZCatalog.Lazy import LazyMop
        totalseq = []
        for s in seq:
            totalseq.extend(s)
        return LazyMop(mapfunc, totalseq)

    def testMop(self):
        from string import hexdigits, letters
        seq1 = range(10)
        seq2 = list(hexdigits)
        seq3 = list(letters)
        def filter(x):
           if isinstance(x, int):
              raise ValueError
           return x.lower()
        lmop = self._createLMop(filter, seq1, seq2, seq3)
        self._compare(lmop, [str(x).lower() for x in (seq2 + seq3)])

    def testConsistentLengthWithMop(self):
        from string import letters
        
        seq = range(10) + list(letters)
        def filter(x):
           if isinstance(x, int):
              raise ValueError
           return x.lower()

        # Unaccessed length
        lmop = self._createLMop(filter, seq)
        self.assertEqual(len(lmop), 52)

        # Accessed in the middle
        lmop = self._createLMop(filter, seq)
        lmop[26]
        self.assertEqual(len(lmop), 52)

        # Accessed after the lcat is accessed over the whole range
        lmop = self._createLMop(filter, letters)
        lmop[:]
        self.assertEqual(len(lmop), 52)


class TestLazyValues(BaseSequenceTest):
    def _createLValues(self, seq):
        from Products.ZCatalog.Lazy import LazyValues
        return LazyValues(seq)

    def testEmpty(self):
        lvals = self._createLValues([])
        self._compare(lvals, [])

    def testValues(self):
        from string import letters
        seq = zip(letters, range(10))
        lvals = self._createLValues(seq)
        self._compare(lvals, range(10))

    def testSlice(self):
        from string import letters
        seq = zip(letters, range(10))
        lvals = self._createLValues(seq)
        self._compare(lvals[2:-2], range(2, 8))


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestLazyCat))
    suite.addTest(unittest.makeSuite(TestLazyMap))
    suite.addTest(unittest.makeSuite(TestLazyFilter))
    suite.addTest(unittest.makeSuite(TestLazyMop))
    suite.addTest(unittest.makeSuite(TestLazyValues))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
