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
import sys, os, time, random, unittest

if __name__ == "__main__":
    sys.path.insert(0, '../../..')

import ZODB
from Products.Transience.Transience import TransientObjectContainer,\
     MaxTransientObjectsExceeded
from Products.Transience.TransientObject import TransientObject
import Products.Transience.Transience
import Products.Transience.TransientObject
from ExtensionClass import Base
from unittest import TestCase, TestSuite, TextTestRunner, makeSuite
import time as oldtime
import fauxtime

class TestBase(TestCase):
    def setUp(self):
        Products.Transience.Transience.time = fauxtime
        Products.Transience.TransientObject.time = fauxtime
        self.errmargin = .20
        self.timeout = 60
        self.t = TransientObjectContainer('sdc', timeout_mins=self.timeout/60)

    def tearDown(self):
        self.t = None
        Products.Transience.Transience.time = oldtime
        Products.Transience.TransientObject.time = oldtime

class TestTransientObjectContainer(TestBase):
    def testGetItemFails(self):
        self.assertRaises(KeyError, self._getitemfail)

    def _getitemfail(self):
        return self.t[10]

    def testGetReturnsDefault(self):
        assert self.t.get(10) == None
        assert self.t.get(10, 'foo') == 'foo'

    def testSetItemGetItemWorks(self):
        self.t[10] = 1
        a = self.t[10]
        assert a == 1, `a`

    def testReplaceWorks(self):
        self.t[10] = 1
        assert self.t[10] == 1
        self.t[10] = 2
        assert self.t[10] == 2

    def testHasKeyWorks(self):
        self.t[10] = 1
        assert self.t.has_key(10)

    def testValuesWorks(self):
        for x in range(10, 110):
            self.t[x] = x
        v = self.t.values()
        v.sort()
        assert len(v) == 100
        i = 10
        for x in v:
            assert x == i
            i = i + 1

    def testKeysWorks(self):
        for x in range(10, 110):
            self.t[x] = x
        v = self.t.keys()
        v.sort()
        assert len(v) == 100
        i = 10
        for x in v:
            assert x == i
            i = i + 1

    def testItemsWorks(self):
        for x in range(10, 110):
            self.t[x] = x
        v = self.t.items()
        v.sort()
        assert len(v) == 100
        i = 10
        for x in v:
            assert x[0] == i
            assert x[1] == i
            i = i + 1

    def testDeleteInvalidKeyRaisesKeyError(self):
        self.assertRaises(KeyError, self._deletefail)

    def _deletefail(self):
        del self.t[10]

    def donttestDeleteNoChildrenWorks(self):
        self.t[5] = 6
        self.t[2] = 10
        self.t[6] = 12
        self.t[1] = 100
        self.t[3] = 200
        self.t[10] = 500
        self.t[4] = 99
        del self.t[4]
        assert lsubtract(self.t.keys(), [1,2,3,5,6,10]) == [], `self.t.keys()`

    def donttestDeleteOneChildWorks(self):
        self.t[5] = 6
        self.t[2] = 10
        self.t[6] = 12
        self.t[1] = 100
        self.t[3] = 200
        self.t[10] = 500
        self.t[4] = 99
        del self.t[3]
        assert lsubtract(self.t.keys(), [1,2,4,5,6,10]) == [], `self.t.keys()`

    def donttestDeleteTwoChildrenNoInorderSuccessorWorks(self):
        self.t[5] = 6
        self.t[2] = 10
        self.t[6] = 12
        self.t[1] = 100
        self.t[3] = 200
        self.t[10] = 500
        self.t[4] = 99
        del self.t[2]
        assert lsubtract(self.t.keys(),[1,3,4,5,6,10])==[], `self.t.keys()`

    def donttestDeleteTwoChildrenInorderSuccessorWorks(self):
        self.t[5] = 6
        self.t[2] = 10
        self.t[6] = 12
        self.t[1] = 100
        self.t[3] = 200
        self.t[10] = 500
        self.t[4] = 99
        self.t[2.5] = 150
        del self.t[2]
        assert lsubtract(self.t.keys(),[1,2.5,3,4,5,6,10])==[], `self.t.keys()`

    def donttestDeleteRootWorks(self):
        self.t[5] = 6
        self.t[2] = 10
        self.t[6] = 12
        self.t[1] = 100
        self.t[3] = 200
        self.t[10] = 500
        self.t[4] = 99
        self.t[2.5] = 150
        del self.t[5]
        assert lsubtract(self.t.keys(),[1,2,2.5,3,4,6,10])==[], `self.t.keys()`

    def testRandomNonOverlappingInserts(self):
        added = {}
        r = range(10, 110)
        for x in r:
            k = random.choice(r)
            if not added.has_key(k):
                self.t[k] = x
                added[k] = 1
        addl = added.keys()
        addl.sort()
        assert lsubtract(self.t.keys(),addl)==[], `self.t.keys()`

    def testRandomOverlappingInserts(self):
        added = {}
        r = range(10, 110)
        for x in r:
            k = random.choice(r)
            self.t[k] = x
            added[k] = 1
        addl = added.keys()
        addl.sort()
        assert lsubtract(self.t.keys(), addl) ==[]

    def testRandomDeletes(self):
        r = range(10, 1010)
        added = []
        for x in r:
            k = random.choice(r)
            self.t[k] = x
            added.append(k)
        deleted = []
        for x in r:
            k = random.choice(r)
            if self.t.has_key(k):
                del self.t[k]
                deleted.append(k)
                if self.t.has_key(k):
                    print "had problems deleting %s" % k
        badones = []
        for x in deleted:
            if self.t.has_key(x):
                badones.append(x)
        assert badones == [], (badones, added, deleted)

    def testTargetedDeletes(self):
        r = range(10, 1010)
        for x in r:
            k = random.choice(r)
            self.t[k] = x
        for x in r:
            try:
                del self.t[x]
            except KeyError:
                pass
        assert self.t.keys() == [], `self.t.keys()`

    def testPathologicalRightBranching(self):
        r = range(10, 1010)
        for x in r:
            self.t[x] = 1
        assert list(self.t.keys()) == r, (self.t.keys(), r)
        map(self.t.__delitem__, r)
        assert list(self.t.keys()) == [], self.t.keys()

    def testPathologicalLeftBranching(self):
        r = range(10, 1010)
        revr = r[:]
        revr.reverse()
        for x in revr:
            self.t[x] = 1
        assert list(self.t.keys()) == r, (self.t.keys(), r)
        map(self.t.__delitem__, revr)
        assert list(self.t.keys()) == [], self.t.keys()

    def donttestSuccessorChildParentRewriteExerciseCase(self):
        add_order = [
            85, 73, 165, 273, 215, 142, 233, 67, 86, 166, 235, 225, 255,
            73, 175, 171, 285, 162, 108, 28, 283, 258, 232, 199, 260,
            298, 275, 44, 261, 291, 4, 181, 285, 289, 216, 212, 129,
            243, 97, 48, 48, 159, 22, 285, 92, 110, 27, 55, 202, 294,
            113, 251, 193, 290, 55, 58, 239, 71, 4, 75, 129, 91, 111,
            271, 101, 289, 194, 218, 77, 142, 94, 100, 115, 101, 226,
            17, 94, 56, 18, 163, 93, 199, 286, 213, 126, 240, 245, 190,
            195, 204, 100, 199, 161, 292, 202, 48, 165, 6, 173, 40, 218,
            271, 228, 7, 166, 173, 138, 93, 22, 140, 41, 234, 17, 249,
            215, 12, 292, 246, 272, 260, 140, 58, 2, 91, 246, 189, 116,
            72, 259, 34, 120, 263, 168, 298, 118, 18, 28, 299, 192, 252,
            112, 60, 277, 273, 286, 15, 263, 141, 241, 172, 255, 52, 89,
            127, 119, 255, 184, 213, 44, 116, 231, 173, 298, 178, 196,
            89, 184, 289, 98, 216, 115, 35, 132, 278, 238, 20, 241, 128,
            179, 159, 107, 206, 194, 31, 260, 122, 56, 144, 118, 283,
            183, 215, 214, 87, 33, 205, 183, 212, 221, 216, 296, 40,
            108, 45, 188, 139, 38, 256, 276, 114, 270, 112, 214, 191,
            147, 111, 299, 107, 101, 43, 84, 127, 67, 205, 251, 38, 91,
            297, 26, 165, 187, 19, 6, 73, 4, 176, 195, 90, 71, 30, 82,
            139, 210, 8, 41, 253, 127, 190, 102, 280, 26, 233, 32, 257,
            194, 263, 203, 190, 111, 218, 199, 29, 81, 207, 18, 180,
            157, 172, 192, 135, 163, 275, 74, 296, 298, 265, 105, 191,
            282, 277, 83, 188, 144, 259, 6, 173, 81, 107, 292, 231,
            129, 65, 161, 113, 103, 136, 255, 285, 289, 1
            ]
        delete_order = [
            276, 273, 12, 275, 2, 286, 127, 83, 92, 33, 101, 195,
            299, 191, 22, 232, 291, 226, 110, 94, 257, 233, 215, 184,
            35, 178, 18, 74, 296, 210, 298, 81, 265, 175, 116, 261,
            212, 277, 260, 234, 6, 129, 31, 4, 235, 249, 34, 289, 105,
            259, 91, 93, 119, 7, 183, 240, 41, 253, 290, 136, 75, 292,
            67, 112, 111, 256, 163, 38, 126, 139, 98, 56, 282, 60, 26,
            55, 245, 225, 32, 52, 40, 271, 29, 252, 239, 89, 87, 205,
            213, 180, 97, 108, 120, 218, 44, 187, 196, 251, 202, 203,
            172, 28, 188, 77, 90, 199, 297, 282, 141, 100, 161, 216,
            73, 19, 17, 189, 30, 258
            ]
        for x in add_order:
            self.t[x] = 1
        for x in delete_order:
            try: del self.t[x]
            except KeyError:
                if self.t.has_key(x): assert 1==2,"failed to delete %s" % x

    def testChangingTimeoutWorks(self):
        # 1 minute
        for x in range(10, 110):
            self.t[x] = x
        fauxtime.sleep(self.timeout * (self.errmargin+1))
        assert len(self.t.keys()) == 0, len(self.t.keys())

        # 2 minutes
        self.t._setTimeout(self.timeout/60*2)
        self.t._reset()
        for x in range(10, 110):
            self.t[x] = x
        fauxtime.sleep(self.timeout)
        assert len(self.t.keys()) == 100, len(self.t.keys())
        fauxtime.sleep(self.timeout * (self.errmargin+1))
        assert len(self.t.keys()) == 0, len(self.t.keys())

        # 3 minutes
        self.t._setTimeout(self.timeout/60*3)
        self.t._reset()
        for x in range(10, 110):
            self.t[x] = x
        fauxtime.sleep(self.timeout)
        assert len(self.t.keys()) == 100, len(self.t.keys())
        fauxtime.sleep(self.timeout)
        assert len(self.t.keys()) == 100, len(self.t.keys())
        fauxtime.sleep(self.timeout * (self.errmargin+1))
        assert len(self.t.keys()) == 0, len(self.t.keys())


    def testItemsGetExpired(self):
        for x in range(10, 110):
            self.t[x] = x
        # these items will time out while we sleep
        fauxtime.sleep(self.timeout * (self.errmargin+1))
        for x in range(110, 210):
            self.t[x] = x
        assert len(self.t.keys()) == 100, len(self.t.keys())
        # we should still have 100 - 199
        for x in range(110, 210):
            assert self.t[x] == x
        # but we shouldn't have 0 - 100
        for x in range(10, 110):
            try: self.t[x]
            except KeyError: pass
            else: assert 1 == 2, x

    def testChangingTimeoutWorks(self):
        # 1 minute
        for x in range(10, 110):
            self.t[x] = x
        fauxtime.sleep(self.timeout * (self.errmargin+1))
        assert len(self.t.keys()) == 0, len(self.t.keys())

        # 2 minutes
        self.t._setTimeout(self.timeout/60*2)
        self.t._reset()
        for x in range(10, 110):
            self.t[x] = x
        fauxtime.sleep(self.timeout)
        assert len(self.t.keys()) == 100, len(self.t.keys())
        fauxtime.sleep(self.timeout * (self.errmargin+1))
        assert len(self.t.keys()) == 0, len(self.t.keys())

        # 3 minutes
        self.t._setTimeout(self.timeout/60*3)
        self.t._reset()
        for x in range(10, 110):
            self.t[x] = x
        fauxtime.sleep(self.timeout)
        assert len(self.t.keys()) == 100, len(self.t.keys())
        fauxtime.sleep(self.timeout)
        assert len(self.t.keys()) == 100, len(self.t.keys())
        fauxtime.sleep(self.timeout * (self.errmargin+1))
        assert len(self.t.keys()) == 0, len(self.t.keys())

    def testGetDelaysTimeout(self):
        for x in range(10, 110):
            self.t[x] = x
        # current bucket will become old after we sleep for a while.
        fauxtime.sleep(self.timeout/2)
        # these items will be added to the new current bucket by getitem
        for x in range(10, 110):
            self.t.get(x)
        fauxtime.sleep(self.timeout/2)
        assert len(self.t.keys()) == 100, len(self.t.keys())
        for x in range(10, 110):
            assert self.t[x] == x

    def testSetItemDelaysTimeout(self):
        for x in range(10, 110):
            self.t[x] = x
        # current bucket will become old after we sleep for a while.
        fauxtime.sleep(self.timeout/2)
        # these items will be added to the new current bucket by setitem
        for x in range(10, 110):
            self.t[x] = x + 1
        fauxtime.sleep(self.timeout/2)
        assert len(self.t.keys()) == 100, len(self.t.keys())
        for x in range(10, 110):
            assert self.t[x] == x + 1

    def testLen(self):
        added = {}
        r = range(10, 1010)
        for x in r:
            k = random.choice(r)
            self.t[k] = x
            added[k] = x
        addl = added.keys()
        addl.sort()
        assert len(self.t) == len(addl), len(self.t)

    def testResetWorks(self):
        self.t[10] = 1
        self.t._reset()
        assert not self.t.get(10)

    def testGetTimeoutMinutesWorks(self):
        assert self.t.getTimeoutMinutes() == self.timeout / 60
        self.t._setTimeout(10)
        assert self.t.getTimeoutMinutes() == 10

    def test_new(self):
        t = self.t.new('foobieblech')
        assert issubclass(t.__class__, TransientObject)

    def _dupNewItem(self):
        t = self.t.new('foobieblech')

    def test_newDupFails(self):
        t = self.t.new('foobieblech')
        self.assertRaises(KeyError, self._dupNewItem)

    def test_new_or_existing(self):
        t = self.t.new('foobieblech')
        t['hello'] = "Here I am!"
        t2 = self.t.new_or_existing('foobieblech')
        assert t2['hello'] == "Here I am!"

    def test_getId(self):
        assert self.t.getId() == 'sdc'

    def testSubobjectLimitWorks(self):
        self.t = TransientObjectContainer('a', timeout_mins=self.timeout/60,
                                          limit=10)
        self.assertRaises(MaxTransientObjectsExceeded, self._maxOut)

    def testUnlimitedSubobjectLimitWorks(self):
        self._maxOut()

    def _maxOut(self):
        for x in range(11):
            self.t.new(str(x))


def lsubtract(l1, l2):
    l1=list(l1)
    l2=list(l2)
    l = filter(lambda x, l1=l1: x not in l1, l2)
    l = l + filter(lambda x, l2=l2: x not in l2, l1)
    return l

def test_suite():
    testsuite = makeSuite(TestTransientObjectContainer, 'test')
    #testsuite = makeSuite(TestBase, 'test')
    alltests = TestSuite((testsuite,))
    return alltests

if __name__ == '__main__':
    runner = TextTestRunner(verbosity=9)
    runner.run(test_suite())
