if __name__=='__main__':
    import sys
    sys.path.insert(0, '../../..')
    sys.path.insert(0, '..')

import ZODB
from Products.TemporaryFolder import TemporaryStorage
import sys, os, unittest

from ZODB.tests import StorageTestBase, BasicStorage, \
     Synchronization, ConflictResolution, \
     Corruption, RevisionStorage

class TemporaryStorageTests(
    StorageTestBase.StorageTestBase,
    RevisionStorage.RevisionStorage, # not actually a revision storage, but..
    BasicStorage.BasicStorage,
    Synchronization.SynchronizedStorage,
    ConflictResolution.ConflictResolvingStorage,
    ):

    def open(self, **kwargs):
        self._storage = TemporaryStorage.TemporaryStorage('foo')

    def setUp(self):
        self.open()
        StorageTestBase.StorageTestBase.setUp(self)

    def tearDown(self):
        StorageTestBase.StorageTestBase.tearDown(self)

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
