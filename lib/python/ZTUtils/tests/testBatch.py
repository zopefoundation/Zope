import os, sys
execfile(os.path.join(sys.path[0], 'framework.py'))

import string
from ZTUtils import Batch

class BatchTests(unittest.TestCase):

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
            for i in seq:
                assert b[i] == i, (b[i], i)
                neg = -1 - i
                assert b[neg] == (bsize + neg), (b[neg], (bsize + neg)) 

    def testOrphan(self):
        '''Test orphan collection'''
        for bsize in (6, 7):
            b = Batch(range(bsize), 5)
            assert b.next is None
            assert len(b) == bsize
        b = Batch(range(8), 5)
        assert len(b) == 5
        assert len(b.next) == 3
        
        
def test_suite():
    return unittest.makeSuite(BatchTests)

if __name__=='__main__':
    main()
