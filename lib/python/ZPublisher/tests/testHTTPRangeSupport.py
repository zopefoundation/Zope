##############################################################################
# 
# Zope Public License (ZPL) Version 1.0
# -------------------------------------
# 
# Copyright (c) Digital Creations.  All rights reserved.
# 
# This license has been certified as Open Source(tm).
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
# 
# 1. Redistributions in source code must retain the above copyright
#    notice, this list of conditions, and the following disclaimer.
# 
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions, and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
# 
# 3. Digital Creations requests that attribution be given to Zope
#    in any manner possible. Zope includes a "Powered by Zope"
#    button that is installed by default. While it is not a license
#    violation to remove this button, it is requested that the
#    attribution remain. A significant investment has been put
#    into Zope, and this effort will continue if the Zope community
#    continues to grow. This is one way to assure that growth.
# 
# 4. All advertising materials and documentation mentioning
#    features derived from or use of this software must display
#    the following acknowledgement:
# 
#      "This product includes software developed by Digital Creations
#      for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
#    In the event that the product being advertised includes an
#    intact Zope distribution (with copyright and license included)
#    then this clause is waived.
# 
# 5. Names associated with Zope or Digital Creations must not be used to
#    endorse or promote products derived from this software without
#    prior written permission from Digital Creations.
# 
# 6. Modified redistributions of any form whatsoever must retain
#    the following acknowledgment:
# 
#      "This product includes software developed by Digital Creations
#      for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
#    Intact (re-)distributions of any official Zope release do not
#    require an external acknowledgement.
# 
# 7. Modifications are encouraged but must be packaged separately as
#    patches to official Zope releases.  Distributions that do not
#    clearly separate the patches from the original work must be clearly
#    labeled as unofficial distributions.  Modifications which do not
#    carry the name Zope may be packaged in any form, as long as they
#    conform to all of the clauses above.
# 
# 
# Disclaimer
# 
#   THIS SOFTWARE IS PROVIDED BY DIGITAL CREATIONS ``AS IS'' AND ANY
#   EXPRESSED OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
#   IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
#   PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL DIGITAL CREATIONS OR ITS
#   CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
#   SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
#   LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF
#   USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#   ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
#   OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT
#   OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
#   SUCH DAMAGE.
# 
# 
# This software consists of contributions made by Digital Creations and
# many individuals on behalf of Digital Creations.  Specific
# attributions are listed in the accompanying credits file.
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
            [(1, 20), (25, 50)])

    def testAdjacentOutOfOrder(self):
        self.expectSets([(-5, None), (40, 45)], 50, [(40, 50)])

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

