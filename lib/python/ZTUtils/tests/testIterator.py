import os, sys, unittest

from ZTUtils import Iterator

try:
    iter
    do_piter_test = 1
except NameError:
    do_piter_test = 0

class IteratorTests(unittest.TestCase):

    def testIterator0(self):
        it = Iterator(())
        assert not it.next(), "Empty iterator"

    def testIterator1(self):
        it = Iterator((1,))
        assert it.next() and not it.next(), "Single-element iterator"

    def testIteratorMany(self):
        it = Iterator('text')
        for c in 'text':
            assert it.next(), "Multi-element iterator"
        assert not it.next(), "Multi-element iterator"

    def testStart(self):
        for size in range(4):
            it = Iterator(range(size+1))
            it.next()
            assert it.start, "Start true on element 1 of %s" % (size + 1)
            el = 1
            while it.next():
                el = el + 1
                assert not it.start, (
                    "Start false on element %s of %s" % (el, size+1))

    def testEnd(self):
        for size in range(4):
            size = size + 1
            it = Iterator(range(size))
            el = 0
            while it.next():
                el = el + 1
                if el == size:
                    assert it.end, "End true on element %s" % size
                else:
                    assert not it.end, (
                        "End false on element %s of %s" % (el, size))

    def testIndex(self):
        it = Iterator(range(5))
        for el in range(5):
            assert it.next(), "Iterator stopped too soon"
            assert it.index == el, "Incorrect index"
            assert it.number() == el + 1, "Incorrect number"
            assert it.item == el, "Incorrect item"

    def testFirstLast(self):
        it = Iterator([1])
        it.next()
        assert it.first() == it.last() == 1, "Bad first/last on singleton"
        four = range(4)
        for a in 2,3:
            for b in four:
                for c in four:
                    s = 'a' * a + 'b' * b + 'c' * c
                    it = Iterator(s)
                    it.next()
                    assert it.first(), "First element not first()"
                    last = s[0]
                    lastlast = it.last()
                    while it.next():
                        assert ((it.item != last) == it.first()), (
                            "first() error")
                        assert ((it.item != last) == lastlast), (
                            "last() error" % (it.item,
                            last, lastlast))
                        last = it.item
                        lastlast = it.last()
                    assert lastlast, "Last element not last()"
                    
    if do_piter_test:
        def testIterOfIter(self):
            for i in range(4):
                r = range(i)
                it1 = Iterator(r)
                it2 = Iterator(iter(r))
                while it1.next() and it2.next():
                    assert it1.item == it2.item, "Item mismatch with iter()"
                    assert it1.index == it2.index, (
                        "Index mismatch with iter()")
                assert not (it1.next() or it2.next()), (
                    "Length mismatch with iter()")

        def testIterIter(self):
            wo_iter = map(lambda x:(x, x), range(4))
            for i in range(4):
                r = range(i)
                w_iter = []
                it = Iterator(r)
                for x in it:
                    w_iter.append((x, it.index))
                assert w_iter == wo_iter[:i], (
                    "for-loop failure on full iterator")
            it = Iterator(range(4))
            it.next(); it.next(); it.next()
            w_iter = []
            for x in it:
                w_iter.append((x, it.index))
            assert w_iter == wo_iter[2:], "for-loop failure on half iteration"

def test_suite():
    return unittest.makeSuite(IteratorTests)

if __name__=='__main__':
    main()
