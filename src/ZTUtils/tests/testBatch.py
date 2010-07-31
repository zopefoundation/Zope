from unittest import TestCase, makeSuite

from ZTUtils import Batch

class BatchTests(TestCase):

    def testEmpty(self):
        '''Test empty Batch'''
        b = Batch([], 5)
        assert b.previous is None
        assert b.next is None
        assert len(b) == b.start == b.end == 0, (len(b), b.start, b.end)

    def testSingle(self):
        '''Test single Batch'''
        for bsize in range(1, 6):
            seq = range(bsize)
            b = Batch(seq, 5)
            assert b.previous is None
            assert b.next is None
            assert b.start == 1, b.start
            assert len(b) ==  b.end == bsize
            assert b.sequence_length == len(seq)
            for i in seq:
                assert b[i] == i, (b[i], i)
                neg = -1 - i
                assert b[neg] == (bsize + neg), (b[neg], (bsize + neg))

    def testOrphan(self):
        '''Test orphan collection'''
        for bsize in (6, 7):
            b = Batch(range(bsize), 5, orphan=3)
            assert b.next is None
            assert len(b) == bsize
            assert b[bsize - 1] == bsize - 1
            assert b.sequence_length == bsize
        b = Batch(range(8), 5)
        assert len(b) == 5
        assert b.sequence_length == 8
        assert len(b.next) == 3

    def testLengthEqualsSizePlusOrphans(self):
        '''Test limit case where batch length is equal to size + orphans'''
        for bsize, length in ((12,11), (13,12), (14,13), (15,10)):
            b = Batch(range(bsize), size=10, start=1, end=0, orphan=3, overlap=0)
            assert length == b.length
    
def test_suite():
    return makeSuite(BatchTests)
