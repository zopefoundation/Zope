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

import sys
sys.path.insert(0, '.')
try:
    from ZPublisher.HTTPRangeSupport import parseRange, optimizeRanges
except ImportError:
    sys.path[0]='../..'
    from ZPublisher.HTTPRangeSupport import parseRange, optimizeRanges

import unittest

class TestRangeHeaderParse(unittest.TestCase):

    # Utility methods
    def expectNone(self, header):
        result = parseRange(header)
        self.failUnless(result is None, 'Expected None, got %s' % `result`)
    
    def expectSets(self, header, sets):
        result = parseRange(header)
        self.failUnless(result == sets,
            'Expected %s, got %s' % (`sets`, `result`))

    # Syntactically incorrect headers
    def testGarbage(self):
        self.expectNone('kjahskjhdfkgkjbnbb ehgdk dsahg wlkjew lew\n =lkdskue')

    def testIllegalSpec(self):
        self.expectNone('notbytes=0-1000')

    def testNoSets(self):
        self.expectNone('bytes=')

    def testEmptySets(self):
        self.expectNone('bytes=,,,')

    def testIllegalRange(self):
        self.expectNone('bytes=foo-bar')

    def testAlmostIntegers(self):
        self.expectNone('bytes=1.0-2.0')

    def testEndLowerThanStart(self):
        self.expectNone('bytes=5-4')

    # Correct headers
    def testSimpleRange(self):
        self.expectSets('bytes=2-20', [(2, 21)])

    def testSimpleRangeAndEmpty(self):
        self.expectSets('bytes=,2-20,', [(2, 21)])

    def testSuffixRange(self):
        self.expectSets('bytes=-100', [(-100, None)])

    def testOpenEnded(self):
        self.expectSets('bytes=100-', [(100, None)])
       
    def testStartEqualsEnd(self):
        self.expectSets('bytes=100-100', [(100, 101)])
       
    def testMultiple(self):
        self.expectSets('bytes=-100,,1-2,20-', 
            [(-100, None), (1, 3), (20, None)])

    def testFirstByte(self):
        self.expectSets('bytes=0-0', [(0, 1)])

    def testNegativeZero(self):
        self.expectSets('bytes=-0', [(sys.maxint, None)])


class TestOptimizeRanges(unittest.TestCase):

    def expectSets(self, sets, size, expect):
        result = optimizeRanges(sets, size)
        self.failUnless(result == expect,
            'Expected %s, got %s' % (`expect`, `result`))

    def testExpandOpenEnd(self):
        self.expectSets([(1, 2), (5, None)], 50, [(1, 2), (5, 50)])

    def testMakeAbsolute(self):
        self.expectSets([(1, 2), (-5, None)], 50, [(1, 2), (45, 50)])

    def testNoOverlapInOrder(self):
        self.expectSets([(1, 5), (1000, 2000), (3000, None)], 5000,
            [(1, 5), (1000, 2000), (3000, 5000)])

    def testNoOverlapOutOfOrder(self):
        self.expectSets([(1000, 2000), (3000, None), (1, 5)], 5000,
            [(1, 5), (1000, 2000), (3000, 5000)])
       
    def testOverlapInOrder(self):
        self.expectSets([(1, 10), (8, 20), (25, None)], 5000,
            [(1, 20), (25, 5000)])

    def testOverlapOutOfOrder(self):
        self.expectSets([(25, 50), (8, None), (1, 10)], 5000,
            [(1, 5000)])

    def testAdjacentInOrder(self):
        self.expectSets([(1, 10), (10, 20), (25, 50)], 5000,
            [(1, 10), (10, 20), (25, 50)])

    def testAdjacentOutOfOrder(self):
        self.expectSets([(-5, None), (40, 45)], 50, [(40, 45), (45, 50)])

    def testOverLapAndOverflow(self):
        # Note that one endpoint lies beyond the end.
        self.expectSets([(-5, None), (40, 100)], 50, [(40, 50)])

    def testRemoveUnsatisfiable(self):
        self.expectSets([(sys.maxint, None), (10, 20)], 50, [(10, 20)])


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestRangeHeaderParse, 'test'))
    suite.addTest(unittest.makeSuite(TestOptimizeRanges, 'test'))
    return suite

def main():
    unittest.TextTestRunner().run(test_suite())

def debug():
    test_suite().debug()

def pdebug():
    import pdb
    pdb.run('debug()')
   
if __name__=='__main__':
    if len(sys.argv) > 1:
        globals()[sys.argv[1]]()
    else:
        main()

