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

import os
import time
import unittest

from ZODB import DB
from ZODB.referencesf import referencesf
from ZODB.tests.MinPO import MinPO
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

from BDBStorage.tests.BerkeleyTestBase import BerkeleyTestBase

ZERO = '\0'*8

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



def test_suite():
    suite = unittest.TestSuite()
    suite.level = 2
    if BDBStorage.is_available:
        suite.addTest(unittest.makeSuite(TestAutopack))
        suite.addTest(unittest.makeSuite(TestAutomaticClassicPack))
        suite.addTest(unittest.makeSuite(TestMinimalPack))
    return suite



if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
