# Unit tests for basic storage functionality

import unittest

from ZODB import POSException

import BerkeleyTestBase
from ZODB.tests.BasicStorage import BasicStorage
from ZODB.tests.RevisionStorage import RevisionStorage
from ZODB.tests.VersionStorage import VersionStorage
from ZODB.tests.TransactionalUndoStorage import TransactionalUndoStorage
from ZODB.tests.TransactionalUndoVersionStorage import \
     TransactionalUndoVersionStorage
from ZODB.tests.PackableStorage import PackableStorage
from ZODB.tests.HistoryStorage import HistoryStorage
from ZODB.tests.IteratorStorage import IteratorStorage
from ZODB.tests import ConflictResolution



class MinimalTest(BerkeleyTestBase.MinimalTestBase, BasicStorage):

    def checkVersionedStoreAndLoad(self):
        # This storage doesn't support versions, so we should get an exception
        oid = self._storage.new_oid()
        self.assertRaises(POSException.Unsupported,
                          self._dostore,
                          oid, data=11, version='a version')


class FullTest(BerkeleyTestBase.FullTestBase, BasicStorage,
               RevisionStorage, VersionStorage,
               TransactionalUndoStorage,
               TransactionalUndoVersionStorage, PackableStorage,
               HistoryStorage, IteratorStorage,
               ConflictResolution.ConflictResolvingStorage,
               ConflictResolution.ConflictResolvingTransUndoStorage):
    pass



def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(MinimalTest, 'check'))
    suite.addTest(unittest.makeSuite(FullTest, 'check'))
    return suite



if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
