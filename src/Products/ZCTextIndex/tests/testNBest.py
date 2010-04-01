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

from unittest import TestCase, TestSuite, main, makeSuite

from Products.ZCTextIndex.NBest import NBest

class NBestTest(TestCase):

    def testConstructor(self):
        self.assertRaises(ValueError, NBest, 0)
        self.assertRaises(ValueError, NBest, -1)

        for n in range(1, 11):
            nb = NBest(n)
            self.assertEqual(len(nb), 0)
            self.assertEqual(nb.capacity(), n)

    def testOne(self):
        nb = NBest(1)
        nb.add('a', 0)
        self.assertEqual(nb.getbest(), [('a', 0)])

        nb.add('b', 1)
        self.assertEqual(len(nb), 1)
        self.assertEqual(nb.capacity(), 1)
        self.assertEqual(nb.getbest(), [('b', 1)])

        nb.add('c', -1)
        self.assertEqual(len(nb), 1)
        self.assertEqual(nb.capacity(), 1)
        self.assertEqual(nb.getbest(), [('b', 1)])

        nb.addmany([('d', 3), ('e', -6), ('f', 5), ('g', 4)])
        self.assertEqual(len(nb), 1)
        self.assertEqual(nb.capacity(), 1)
        self.assertEqual(nb.getbest(), [('f', 5)])

    def testMany(self):
        import random
        inputs = [(-i, i) for i in range(50)]

        reversed_inputs = inputs[:]
        reversed_inputs.reverse()

        # Test the N-best for a variety of n (1, 6, 11, ... 50).
        for n in range(1, len(inputs)+1, 5):
            expected = inputs[-n:]
            expected.reverse()

            random_inputs = inputs[:]
            random.shuffle(random_inputs)

            for source in inputs, reversed_inputs, random_inputs:
                # Try feeding them one at a time.
                nb = NBest(n)
                for item, score in source:
                    nb.add(item, score)
                self.assertEqual(len(nb), n)
                self.assertEqual(nb.capacity(), n)
                self.assertEqual(nb.getbest(), expected)

                # And again in one gulp.
                nb = NBest(n)
                nb.addmany(source)
                self.assertEqual(len(nb), n)
                self.assertEqual(nb.capacity(), n)
                self.assertEqual(nb.getbest(), expected)

                for i in range(1, n+1):
                    self.assertEqual(nb.pop_smallest(), expected[-i])
                self.assertRaises(IndexError, nb.pop_smallest)

def test_suite():
    return makeSuite(NBestTest)

if __name__=='__main__':
    main(defaultTest='test_suite')
