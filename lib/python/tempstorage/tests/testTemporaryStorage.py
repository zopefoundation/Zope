import ZODB
from ZODB.tests.MinPO import MinPO
from tempstorage import TemporaryStorage
import sys, os, unittest, time

from ZODB.tests import StorageTestBase, BasicStorage, \
     Synchronization, ConflictResolution, \
     Corruption, RevisionStorage, MTStorage

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
