##############################################################################
#
# Copyright (c) 2001, 2002 Zope Corporation and Contributors.
# All Rights Reserved.
# 
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
# 
##############################################################################

# Test the operation of the CommitLog classes

import os
import errno
import unittest
from bsddb3Storage import CommitLog

# BAW: Lots of other things to check:
# - creating with a named directory
# - creating with an existing file via filename
# - creating with a file object with # incorrect mode or permissions
# - creating with a file object raising the two flavors of LogCorruptedError
# - The various forms of LogCorruptedError in PacklessLog.next()



class CreateCommitLogTest(unittest.TestCase):
    def checkCreateNoFile(self):
        unless = self.failUnless
        log = CommitLog.CommitLog()
        filename = log.get_filename()
        try:
            unless(os.path.exists(filename))
        finally:
            log.close(unlink=1)
            unless(not os.path.exists(filename))

    def checkCreateWithFilename(self):
        unless = self.failUnless
        filename = 'commit.log'
        log = CommitLog.CommitLog(filename)
        try:
            unless(os.path.exists(filename))
        finally:
            log.close(unlink=1)
            unless(not os.path.exists(filename))

    def checkCreateWithFileobj(self):
        filename = 'commit.log'
        fp = open(filename, 'w+b')
        try:
            self.assertRaises(CommitLog.TruncationError,
                              CommitLog.CommitLog, fp)
        finally:
            fp.close()
            self.failUnless(not os.path.exists(filename))

    def checkCloseDoesUnlink(self):
        log = CommitLog.CommitLog()
        filename = log.get_filename()
        log.close()
        self.failUnless(not os.path.exists(filename))

    def checkDel(self):
        log = CommitLog.CommitLog()
        filename = log.get_filename()
        del log
        self.failUnless(not os.path.exists(filename))



class BaseSetupTearDown(unittest.TestCase):
    def setUp(self):
        self._log = CommitLog.CommitLog()

    def tearDown(self):
        try:
            self._log.close(unlink=1)
        except OSError, e:
            if e.errno <> errno.ENOENT: raise



class CommitLogStateTransitionTest(BaseSetupTearDown):
    def checkProperStart(self):
        # BAW: best we can do is make sure we can start a new commit log
        self._log.start()

    def checkAppendSetsOpen(self):
        # BAW: Best we can do is assert that the state isn't START
        self._log._append('x', 'ignore')
        self.assertRaises(CommitLog.StateTransitionError, self._log.start)

    def checkPromiseSetsPromise(self):
        # BAW: Best we can do is assert that state isn't START
        self._log.promise()
        self.assertRaises(CommitLog.StateTransitionError, self._log.start)

    def checkBadDoublePromise(self):
        self._log.promise()
        self.assertRaises(CommitLog.StateTransitionError, self._log.promise)

    def checkFinishSetsStart(self):
        self._log.finish()
        # BAW: best we can do is make sure we can start a new commit log
        self._log.start()



# Wouldn't it be nice to have generators? :)
class Gen:
    def __init__(self):
        self.__counter = 0

    def __call__(self):
        try:
            return self[self.__counter]
        finally:
            self.__counter = self.__counter + 1

    def __getitem__(self, i):
        if 0 <= i < 10:
            return chr(i+65), i
        raise IndexError



class LowLevelStoreAndLoadTest(BaseSetupTearDown):
    def checkOneStoreAndLoad(self):
        eq = self.assertEqual
        self._log.start()
        self._log._append('x', 'ignore')
        self._log.promise()
        x, ignore = self._log._next()
        eq(x, 'x')
        eq(ignore, 'ignore')
        eq(self._log._next(), None)

    def checkTenStoresAndLoads(self):
        eq = self.assertEqual
        self._log.start()
        for k, v in Gen():
            self._log._append(k, v)
        self._log.promise()
        g = Gen()
        while 1:
            rec = self._log._next()
            if rec is None:
                break
            c, i = g()
            eq(rec[0], c)
            eq(rec[1], i)
        self.assertRaises(IndexError, g)
        


class PacklessLogTest(BaseSetupTearDown):
    def setUp(self):
        self._log = CommitLog.PacklessLog()
        self._log.start()

    def checkOneStoreAndLoad(self):
        eq = self.assertEqual
        self._log.write_object(oid=10, pickle='ignore')
        self._log.promise()
        oid, pickle = self._log.next()
        eq(oid, 10)
        eq(pickle, 'ignore')
        eq(self._log.next(), None)

    def checkTenStoresAndLoads(self):
        eq = self.assertEqual
        for k, v in Gen():
            self._log.write_object(v, k*10)
        self._log.promise()
        g = Gen()
        while 1:
            rec = self._log.next()
            if rec is None:
                break
            c, i = g()
            oid, pickle = rec
            eq(oid, i)
            eq(pickle, c*10)
        self.assertRaises(IndexError, g)



class FullLogTest(BaseSetupTearDown):
    def setUp(self):
        self._log = CommitLog.FullLog()
        self._log.start()

    def checkOneStoreAndLoad(self):
        eq = self.assertEqual
        oid = 10
        vid = 8
        nvrevid = 0
        pickle = 'ignore'
        prevrevid = 9
        self._log.write_object(oid, vid, nvrevid, pickle, prevrevid)
        self._log.promise()
        rec = self._log.next()
        self.failUnless(rec)
        key, rec = rec
        eq(key, 'x')
        eq(len(rec), 6)
        eq(rec, (oid, vid, nvrevid, '', pickle, prevrevid))
        eq(self._log.next(), None)

    def checkOtherWriteMethods(self):
        eq = self.assertEqual
        unless = self.failUnless
        oid = 10
        vid = 1
        nvrevid = 0
        lrevid = 8
        pickle = 'ignore'
        prevrevid = 9
        version = 'new-version'
        zero = '\0'*8
        self._log.write_nonversion_object(oid, lrevid, prevrevid)
        self._log.write_moved_object(oid, vid, nvrevid, lrevid, prevrevid)
        self._log.write_new_version(version, vid)
        self._log.write_discard_version(vid)
        self._log.promise()
        rec = self._log.next()
        unless(rec)
        key, rec = rec
        eq(key, 'o')
        eq(len(rec), 6)
        eq(rec, (oid, zero, zero, lrevid, None, prevrevid))
        rec = self._log.next()
        unless(rec)
        key, rec = rec
        eq(key, 'o')
        eq(len(rec), 6)
        eq(rec, (oid, vid, nvrevid, lrevid, None, prevrevid))
        rec = self._log.next()
        unless(rec)
        key, rec = rec
        eq(key, 'v')
        eq(len(rec), 2)
        eq(rec, (version, vid))
        rec = self._log.next()
        unless(rec)
        key, rec = rec
        eq(key, 'd')
        eq(len(rec), 1)
        eq(rec, (vid,))



def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(CreateCommitLogTest, 'check'))
    suite.addTest(unittest.makeSuite(CommitLogStateTransitionTest, 'check'))
    suite.addTest(unittest.makeSuite(LowLevelStoreAndLoadTest, 'check'))
    suite.addTest(unittest.makeSuite(PacklessLogTest, 'check'))
    suite.addTest(unittest.makeSuite(FullLogTest, 'check'))
    return suite



if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
