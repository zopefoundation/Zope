##############################################################################
#
# Copyright (c) 2002 Zope Corporation and Contributors.
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

from __future__ import nested_scopes

import os
import time
import unittest
import threading

from ZODB import DB
from ZODB.Transaction import Transaction
from ZODB.referencesf import referencesf
from ZODB.TimeStamp import TimeStamp
from ZODB.tests.MinPO import MinPO
from ZODB.tests.StorageTestBase import zodb_pickle
from Persistence import Persistent

import BDBStorage
if BDBStorage.is_available:
    from BDBStorage.BDBFullStorage import BDBFullStorage
    from BDBStorage.BDBMinimalStorage import BDBMinimalStorage
    from BDBStorage.BerkeleyBase import BerkeleyConfig
else:
    # Sigh
    class FakeBaseClass: pass
    BDBFullStorage = BDBMinimalStorage = FakeBaseClass

from BDBStorage import ZERO
from BDBStorage.tests.BerkeleyTestBase import BerkeleyTestBase

try:
    True, False
except NameError:
    True = 1
    False = 0


class C(Persistent):
    pass



class TestAutopackBase(BerkeleyTestBase):
    def _config(self):
        config = BerkeleyConfig()
        # Autopack every 3 seconds, 6 seconds into the past, no classic packs
        config.frequency = 3
        config.packtime = 6
        config.classicpack = 0
        return config

    def _wait_for_next_autopack(self):
        storage = self._storage
        # BAW: this uses a non-public interface
        packtime = storage._autopacker._nextcheck
        while packtime == storage._autopacker._nextcheck:
            time.sleep(1)

    def _mk_dbhome(self, dir):
        # Create the storage
        os.mkdir(dir)
        try:
            return self.ConcreteStorage(dir, config=self._config())
        except:
            self._zap_dbhome(dir)
            raise



class TestAutopack(TestAutopackBase):
    ConcreteStorage = BDBFullStorage

    def testAutopack(self):
        unless = self.failUnless
        raises = self.assertRaises
        storage = self._storage
        # Wait for an autopack operation to occur, then make three revisions
        # to an object.  Wait for the next autopack operation and make sure
        # all three revisions still exist.  Then sleep 10 seconds and wait for
        # another autopack operation.  Then verify that the first two
        # revisions have been packed away.
        oid = storage.new_oid()
        self._wait_for_next_autopack()
        revid1 = self._dostore(oid, data=MinPO(2112))
        revid2 = self._dostore(oid, revid=revid1, data=MinPO(2113))
        revid3 = self._dostore(oid, revid=revid2, data=MinPO(2114))
        self._wait_for_next_autopack()
        unless(storage.loadSerial(oid, revid1))
        unless(storage.loadSerial(oid, revid2))
        unless(storage.loadSerial(oid, revid3))
        # Should be enough time for the revisions to get packed away
        time.sleep(10)
        self._wait_for_next_autopack()
        # The first two revisions should now be gone, but the third should
        # still exist because it's the current revision, and we haven't done a
        # classic pack.
        raises(KeyError, self._storage.loadSerial, oid, revid1)
        raises(KeyError, self._storage.loadSerial, oid, revid2)
        unless(storage.loadSerial(oid, revid3))



class TestAutomaticClassicPack(TestAutopackBase):
    ConcreteStorage = BDBFullStorage

    def _config(self):
        config = BerkeleyConfig()
        # Autopack every 3 seconds, 6 seconds into the past, no classic packs
        config.frequency = 3
        config.packtime = 6
        config.classicpack = 1
        return config

    def testAutomaticClassicPack(self):
        unless = self.failUnless
        raises = self.assertRaises
        storage = self._storage
        # Wait for an autopack operation to occur, then make three revisions
        # to an object.  Wait for the next autopack operation and make sure
        # all three revisions still exist.  Then sleep 10 seconds and wait for
        # another autopack operation.  Then verify that the first two
        # revisions have been packed away.
        oid = storage.new_oid()
        self._wait_for_next_autopack()
        revid1 = self._dostore(oid, data=MinPO(2112))
        revid2 = self._dostore(oid, revid=revid1, data=MinPO(2113))
        revid3 = self._dostore(oid, revid=revid2, data=MinPO(2114))
        self._wait_for_next_autopack()
        unless(storage.loadSerial(oid, revid1))
        unless(storage.loadSerial(oid, revid2))
        unless(storage.loadSerial(oid, revid3))
        # Should be enough time for the revisions to get packed away
        time.sleep(10)
        self._wait_for_next_autopack()
        # The first two revisions should now be gone, but the third should
        # still exist because it's the current revision, and we haven't done a
        # classic pack.
        raises(KeyError, storage.loadSerial, oid, revid1)
        raises(KeyError, storage.loadSerial, oid, revid2)
        raises(KeyError, storage.loadSerial, oid, revid3)

    def testCycleUnreachable(self):
        unless = self.failUnless
        raises = self.assertRaises
        storage = self._storage
        db = DB(storage)
        conn = db.open()
        root = conn.root()
        self._wait_for_next_autopack()
        # Store an object that's reachable from the root
        obj1 = C()
        obj2 = C()
        obj1.obj = obj2
        obj2.obj = obj1
        root.obj = obj1
        txn = get_transaction()
        txn.note('root -> obj1 <-> obj2')
        txn.commit()
        oid1 = obj1._p_oid
        oid2 = obj2._p_oid
        assert oid1 and oid2 and oid1 <> oid2
        self._wait_for_next_autopack()
        unless(storage.load(ZERO, ''))
        unless(storage.load(oid1, ''))
        unless(storage.load(oid2, ''))
        # Now unlink it, which should still leave obj1 and obj2 alive
        del root.obj
        txn = get_transaction()
        txn.note('root -X-> obj1 <-> obj2')
        txn.commit()
        unless(storage.load(ZERO, ''))
        unless(storage.load(oid1, ''))
        unless(storage.load(oid2, ''))
        # Do an explicit full pack to right now to collect all the old
        # revisions and the cycle.
        storage.pack(time.time(), referencesf)
        # And it should be packed away
        unless(storage.load(ZERO, ''))
        raises(KeyError, storage.load, oid1, '')
        raises(KeyError, storage.load, oid2, '')



class TestMinimalPack(TestAutopackBase):
    ConcreteStorage = BDBMinimalStorage

    def _config(self):
        config = BerkeleyConfig()
        # Autopack every 3 seconds
        config.frequency = 3
        return config

    def testRootUnreachable(self):
        unless = self.failUnless
        raises = self.assertRaises
        storage = self._storage
        db = DB(storage)
        conn = db.open()
        root = conn.root()
        self._wait_for_next_autopack()
        # Store an object that's reachable from the root
        obj = C()
        obj.value = 999
        root.obj = obj
        txn = get_transaction()
        txn.note('root -> obj')
        txn.commit()
        oid = obj._p_oid
        assert oid
        self._wait_for_next_autopack()
        unless(storage.load(ZERO, ''))
        unless(storage.load(oid, ''))
        # Now unlink it
        del root.obj
        txn = get_transaction()
        txn.note('root -X-> obj')
        txn.commit()
        # The object should be gone due to reference counting
        unless(storage.load(ZERO, ''))
        raises(KeyError, storage.load, oid, '')

    def testCycleUnreachable(self):
        unless = self.failUnless
        raises = self.assertRaises
        storage = self._storage
        db = DB(storage)
        conn = db.open()
        root = conn.root()
        self._wait_for_next_autopack()
        # Store an object that's reachable from the root
        obj1 = C()
        obj2 = C()
        obj1.obj = obj2
        obj2.obj = obj1
        root.obj = obj1
        txn = get_transaction()
        txn.note('root -> obj1 <-> obj2')
        txn.commit()
        oid1 = obj1._p_oid
        oid2 = obj2._p_oid
        assert oid1 and oid2 and oid1 <> oid2
        self._wait_for_next_autopack()
        unless(storage.load(ZERO, ''))
        unless(storage.load(oid1, ''))
        unless(storage.load(oid2, ''))
        # Now unlink it, which should still leave obj1 and obj2 alive
        del root.obj
        txn = get_transaction()
        txn.note('root -X-> obj1 <-> obj2')
        txn.commit()
        unless(storage.load(ZERO, ''))
        unless(storage.load(oid1, ''))
        unless(storage.load(oid2, ''))
        # But the next autopack should collect both obj1 and obj2
        self._wait_for_next_autopack()
        # And it should be packed away
        unless(storage.load(ZERO, ''))
        raises(KeyError, storage.load, oid1, '')
        raises(KeyError, storage.load, oid2, '')



class RaceConditionBase(BerkeleyTestBase):
    def setUp(self):
        BerkeleyTestBase.setUp(self)
        self._cv = threading.Condition()
        self._storage.cv = self._cv

    def tearDown(self):
        # clean up any outstanding transactions
        get_transaction().abort()



# Subclass which does ugly things to _dopack so we can actually test the race
# condition.  We need to store a new object in the database between the
# _mark() call and the _sweep() call.
class SynchronizedFullStorage(BDBFullStorage):
    # XXX Cut and paste copy from BDBFullStorage, except where indicated
    def _dopack(self, t, gc=True):
        # t is a TimeTime, or time float, convert this to a TimeStamp object,
        # using an algorithm similar to what's used in FileStorage.  We know
        # that our transaction ids, a.k.a. revision ids, are timestamps.
        #
        # BAW: should a pack time in the future be a ValueError?  We'd have to
        # worry about clock skew, so for now, we just set the pack time to the
        # minimum of t and now.
        packtime = min(t, time.time())
        t0 = TimeStamp(*(time.gmtime(packtime)[:5] + (packtime % 60,)))
        packtid = `t0`
        # Collect all revisions of all objects earlier than the pack time.
        self._lock_acquire()
        try:
            self._withtxn(self._collect_revs, packtid)
        finally:
            self._lock_release()
        # Collect any objects with refcount zero.
        self._lock_acquire()
        try:
            self._withtxn(self._collect_objs)
        finally:
            self._lock_release()
        # If we're not doing a classic pack, we're done.
        if not gc:
            return
        # Do a mark and sweep for garbage collection.  Calculate the set of
        # objects reachable from the root.  Anything else is a candidate for
        # having all their revisions packed away.  The set of reachable
        # objects lives in the _packmark table.
        self._lock_acquire()
        try:
            self._withtxn(self._mark, packtid)
        finally:
            self._lock_release()
        # XXX thread coordination code start
        self.cv.acquire()
        self.cv.notify()
        self.cv.wait()
        # XXX thread coordination code stop
        #
        # Now perform a sweep, using oidqueue to hold all object ids for
        # objects which are not root reachable as of the pack time.
        self._lock_acquire()
        try:
            self._withtxn(self._sweep, packtid)
        finally:
            self._lock_release()
        # Once again, collect any objects with refcount zero due to the mark
        # and sweep garbage collection pass.
        self._lock_acquire()
        try:
            self._withtxn(self._collect_objs)
        finally:
            self._lock_release()
        # XXX thread coordination code start
        self.cv.notify()
        self.cv.release()
        # XXX thread coordination code stop


class FullPackThread(threading.Thread):
    def __init__(self, storage):
        threading.Thread.__init__(self)
        self._storage = storage

    def run(self):
        self._storage.autopack(time.time(), gc=True)


class TestFullClassicPackRaceCondition(RaceConditionBase):
    ConcreteStorage = SynchronizedFullStorage

    def testRaceCondition(self):
        unless = self.failUnless
        storage = self._storage
        db = DB(storage)
        conn = db.open()
        root = conn.root()
        # Start by storing a root reachable object.
        obj1 = C()
        obj1.value = 888
        root.obj1 = obj1
        txn = get_transaction()
        txn.note('root -> obj1')
        txn.commit()
        # Now, start a transaction, store an object, but don't yet complete
        # the transaction.  This will ensure that the second object has a tid
        # < packtime, but it won't be root reachable yet.
        obj2 = C()
        t = Transaction()
        storage.tpc_begin(t)
        obj2sn = storage.store('\0'*7 + '\2', ZERO, zodb_pickle(obj2), '', t)
        # Now, acquire the condvar lock and start a thread that will do a
        # pack, up to the _sweep call.  Wait for the _mark() call to
        # complete.
        now = time.time()
        while now == time.time():
            time.sleep(0.5)
        self._cv.acquire()
        packthread = FullPackThread(storage)
        packthread.start()
        self._cv.wait()
        # Now that the _mark() has finished, complete the transaction, which
        # links the object to root.
        root.obj2 = obj2
        rootsn = storage.getSerial(ZERO)
        rootsn = storage.store(ZERO, rootsn, zodb_pickle(root), '', t)
        storage.tpc_vote(t)
        storage.tpc_finish(t)
        # And notify the pack thread that it can do the sweep and collect
        self._cv.notify()
        self._cv.wait()
        # We're done with the condvar and the thread
        self._cv.release()
        packthread.join()
        # Now make sure that all the interesting objects are still available
        rootsn = storage.getSerial(ZERO)
        obj1sn = storage.getSerial('\0'*7 + '\1')
        obj2sn = storage.getSerial('\0'*7 + '\2')
        # obj1 revision was written before the second revision of the root
        unless(obj1sn < rootsn)
        unless(rootsn == obj2sn)
        unless(obj1sn < obj2sn)



# Subclass which does ugly things to _dopack so we can actually test the race
# condition.  We need to storage a new object in the database between the
# _mark() call and the _sweep() call.
class SynchronizedMinimalStorage(BDBMinimalStorage):
    # XXX Cut and paste copy from BDBMinimalStorage, except where indicated
    def _dopack(self):
        # Do a mark and sweep for garbage collection.  Calculate the set of
        # objects reachable from the root.  Anything else is a candidate for
        # having all their revisions packed away.  The set of reachable
        # objects lives in the _packmark table.
        self._lock_acquire()
        try:
            self._withtxn(self._mark)
        finally:
            self._lock_release()
        # XXX thread coordination code start
        self.cv.acquire()
        self.cv.notify()
        self.cv.wait()
        # XXX thread coordination code stop
        #
        # Now perform a sweep, using oidqueue to hold all object ids for
        # objects which are not root reachable as of the pack time.
        self._lock_acquire()
        try:
            self._withtxn(self._sweep)
        finally:
            self._lock_release()
        # Once again, collect any objects with refcount zero due to the mark
        # and sweep garbage collection pass.
        self._lock_acquire()
        try:
            self._withtxn(self._collect_objs)
        finally:
            self._lock_release()
        # XXX thread coordination code start
        self.cv.notify()
        self.cv.release()
        # XXX thread coordination code stop


class MinimalPackThread(threading.Thread):
    def __init__(self, storage):
        threading.Thread.__init__(self)
        self._storage = storage

    def run(self):
        self._storage.pack(time.time(), referencesf)


class TestMinimalClassicPackRaceCondition(RaceConditionBase):
    ConcreteStorage = SynchronizedMinimalStorage

    def testRaceCondition(self):
        unless = self.failUnless
        storage = self._storage
        db = DB(storage)
        conn = db.open()
        root = conn.root()
        # Start by storing a root reachable object.
        obj1 = C()
        obj1.value = 888
        root.obj1 = obj1
        txn = get_transaction()
        txn.note('root -> obj1')
        txn.commit()
        # Now, start a transaction, store an object, but don't yet complete
        # the transaction.  This will ensure that the second object has a tid
        # < packtime, but it won't be root reachable yet.
        obj2 = C()
        t = Transaction()
        storage.tpc_begin(t)
        obj2sn = storage.store('\0'*7 + '\2', ZERO, zodb_pickle(obj2), '', t)
        # Now, acquire the condvar lock and start a thread that will do a
        # pack, up to the _sweep call.  Wait for the _mark() call to
        # complete.
        now = time.time()
        while now == time.time():
            time.sleep(0.5)
        self._cv.acquire()
        packthread = MinimalPackThread(storage)
        packthread.start()
        self._cv.wait()
        # Now that the _mark() has finished, complete the transaction, which
        # links the object to root.
        root.obj2 = obj2
        rootsn = storage.getSerial(ZERO)
        rootsn = storage.store(ZERO, rootsn, zodb_pickle(root), '', t)
        storage.tpc_vote(t)
        storage.tpc_finish(t)
        # And notify the pack thread that it can do the sweep and collect
        self._cv.notify()
        self._cv.wait()
        # We're done with the condvar and the thread
        self._cv.release()
        packthread.join()
        # Now make sure that all the interesting objects are still available
        rootsn = storage.getSerial(ZERO)
        obj1sn = storage.getSerial('\0'*7 + '\1')
        obj2sn = storage.getSerial('\0'*7 + '\2')
        # obj1 revision was written before the second revision of the root
        unless(obj1sn < rootsn)
        unless(rootsn == obj2sn)
        unless(obj1sn < obj2sn)



def test_suite():
    suite = unittest.TestSuite()
    suite.level = 2
    if BDBStorage.is_available:
        suite.addTest(unittest.makeSuite(TestAutopack))
        suite.addTest(unittest.makeSuite(TestAutomaticClassicPack))
        suite.addTest(unittest.makeSuite(TestMinimalPack))
        suite.addTest(unittest.makeSuite(TestFullClassicPackRaceCondition))
        suite.addTest(unittest.makeSuite(TestMinimalClassicPackRaceCondition))
    return suite



if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
