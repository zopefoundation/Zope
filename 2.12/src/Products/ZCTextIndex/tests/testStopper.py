##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Tests for the C version of the StopWordRemover."""

import unittest

from Products.ZCTextIndex import stopper


class StopperTest(unittest.TestCase):
    def test_process_typeerror(self):
        self.assertRaises(TypeError, stopper.process, 42, [])
        self.assertRaises(TypeError, stopper.process, {}, 42)
        self.assertRaises(TypeError, stopper.process, {})
        self.assertRaises(TypeError, stopper.process, {}, [], 'extra arg')

    def test_process_nostops(self):
        words = ['a', 'b', 'c', 'splat!']
        self.assertEqual(words, stopper.process({}, words))

    def test_process_somestops(self):
        d = {'b':1, 'splat!':1}
        words = ['a', 'b', 'c', 'splat!']
        self.assertEqual(['a', 'c'], stopper.process(d, words))

    def test_process_allstops(self):
        d = {'a':1, 'b':1, 'c':1, 'splat!':1}
        words = ['a', 'b', 'c', 'splat!']
        self.assertEqual([], stopper.process(d, words))


def test_suite():
    return unittest.makeSuite(StopperTest)

if __name__ == "__main__":
    unittest.main(defaultTest='test_suite')
