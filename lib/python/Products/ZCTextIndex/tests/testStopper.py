"""Tests for the C version of the StopWordRemover."""

import unittest

from Products.ZCTextIndex import stopper


class StopperTest(unittest.TestCase):
    def test_constructor_empty(self):
        s = stopper.new()
        self.assertEqual(s.dict, {})

    def test_constructor_dict(self):
        d = {}
        s = stopper.new(d)
        self.assert_(s.dict is d)

    def test_constructor_error(self):
        self.assertRaises(TypeError, stopper.new, [])
        self.assertRaises(TypeError, stopper.new, {}, 'extra arg')

    def test_process_nostops(self):
        s = stopper.new()
        words = ['a', 'b', 'c', 'splat!']
        self.assertEqual(words, s.process(words))

    def test_process_somestops(self):
        s = stopper.new({'b':1, 'splat!':1})
        words = ['a', 'b', 'c', 'splat!']
        self.assertEqual(['a', 'c'], s.process(words))

    def test_process_allstops(self):
        s = stopper.new({'a':1, 'b':1, 'c':1, 'splat!':1})
        words = ['a', 'b', 'c', 'splat!']
        self.assertEqual([], s.process(words))


def test_suite():
    return unittest.makeSuite(StopperTest)

if __name__ == "__main__":
    unittest.main(defaultTest='test_suite')
