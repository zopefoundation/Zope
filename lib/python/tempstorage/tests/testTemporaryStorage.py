import ZODB
from ZODB.tests.MinPO import MinPO
from tempstorage import TemporaryStorage
import sys, os, unittest, time

from ZODB.tests import StorageTestBase, BasicStorage, \
     Synchronization, ConflictResolution, \
     Corruption, RevisionStorage, MTStorage

from persistent import Persistent
import transaction
from ZODB.DB import DB
from ZODB.POSException import ReadConflictError

class TemporaryStorageTests(
    StorageTestBase.StorageTestBase,
##    RevisionStorage.RevisionStorage, # not a revision storage, but passes
    BasicStorage.BasicStorage,
    Synchronization.SynchronizedStorage,
    ConflictResolution.ConflictResolvingStorage,
    MTStorage.MTStorage,
    ):

    def open(self, **kwargs):
        self._storage = TemporaryStorage.TemporaryStorage('foo')

    def setUp(self):
        StorageTestBase.StorageTestBase.setUp(self)
        self.open()

    def tearDown(self):
        StorageTestBase.StorageTestBase.tearDown(self)

    def checkConflictCacheIsCleared(self):
        old_gcevery = TemporaryStorage.CONFLICT_CACHE_GCEVERY
        old_maxage  = TemporaryStorage.CONFLICT_CACHE_MAXAGE
        TemporaryStorage.CONFLICT_CACHE_GCEVERY = 5
        TemporaryStorage.CONFLICT_CACHE_MAXAGE =  5
        try:
            oid = self._storage.new_oid()
            self._dostore(oid, data=MinPO(5))
            time.sleep(TemporaryStorage.CONFLICT_CACHE_GCEVERY + 1)
            oid2 = self._storage.new_oid()
            self._dostore(oid2, data=MinPO(10))
            oid3 = self._storage.new_oid()
            self._dostore(oid3, data=MinPO(9))
            assert len(self._storage._conflict_cache) == 2
            time.sleep(TemporaryStorage.CONFLICT_CACHE_GCEVERY + 1)
            oid4 = self._storage.new_oid()
            self._dostore(oid4, data=MinPO(11))
            assert len(self._storage._conflict_cache) == 1

        finally:
            TemporaryStorage.CONFLICT_CACHE_GCEVERY = old_gcevery
            TemporaryStorage.CONFLICT_CACHE_MAXAGE =  old_maxage

    def doreadconflict(self, db, mvcc):
        tm1 = transaction.TransactionManager()
        conn = db.open(transaction_manager=tm1)
        r1 = conn.root()
        obj = MinPO('root')
        r1["p"] = obj
        obj = r1["p"]
        obj.child1 = MinPO('child1')
        tm1.get().commit()

        # start a new transaction with a new connection
        tm2 = transaction.TransactionManager()
        cn2 = db.open(transaction_manager=tm2)
        r2 = cn2.root()

        self.assertEqual(r1._p_serial, r2._p_serial)

        obj.child2 = MinPO('child2')
        tm1.get().commit()

        # resume the transaction using cn2
        obj = r2["p"]

        # An attempt to access obj.child1 should fail with an RCE
        # below if conn isn't using mvcc, because r2 was read earlier
        # in the transaction and obj was modified by the other
        # transaction.

        obj.child1 
        return obj

    def checkWithMVCCDoesntRaiseReadConflict(self):
        db = DB(self._storage)
        ob = self.doreadconflict(db, True)
        self.assertEquals(ob.__class__, MinPO)
        self.assertEquals(getattr(ob, 'child1', MinPO()).value, 'child1')
        self.failIf(getattr(ob, 'child2', None))

    def checkLoadEx(self):
        oid = self._storage.new_oid()
        self._dostore(oid, data=MinPO(1))
        loadp, loads  = self._storage.load(oid, 'whatever')
        exp, exs, exv = self._storage.loadEx(oid, 'whatever')
        self.assertEqual(loadp, exp)
        self.assertEqual(loads, exs)
        self.assertEqual(exv, '')
        

def test_suite():
    suite = unittest.makeSuite(TemporaryStorageTests, 'check')
    suite2 = unittest.makeSuite(Corruption.FileStorageCorruptTests, 'check')
    suite.addTest(suite2)
    return suite

def main():
    alltests=test_suite()
    runner = unittest.TextTestRunner(verbosity=9)
    runner.run(alltests)

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
