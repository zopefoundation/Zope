import os, sys, unittest

from ZTUtils import Iterator

class IteratorTests(unittest.TestCase):

    def testIterator0(self):
        it = Iterator(())
        assert not it.next(), "Empty iterator"

    def testIterator1(self):
        it = Iterator((1,))
        assert it.next() and not it.next(), "Single-element iterator"

    def testIterator2(self):
        it = Iterator('text')
        for c in 'text':
            assert it.next(), "Multi-element iterator"
        assert not it.next(), "Multi-element iterator"
        
def test_suite():
    return unittest.makeSuite(IteratorTests)

if __name__=='__main__':
    main()
