# Run tests against the official storage API as described in
# http://www.zope.org/Documentation/Developer/Models/ZODB/ZODB_Architecture_Storage_Interface_Info.html

import os
import errno
import pickle
import unittest
import test_create

from ZODB import utils
from ZODB.Transaction import Transaction
from ZODB.POSException import StorageTransactionError

DBHOME = 'test-db'
ZERO = '\0'*8



class StorageAPI(test_create.BaseFramework):
    def setUp(self):
        # A simpler setUp() than the base class since we don't need the DB
        # object, the connection, or the root.
        self._dbhome = DBHOME
        os.mkdir(self._dbhome)

        try:
            self._storage = self.ConcreteStorage(self._dbhome)
        except:
            self.tearDown()
            raise
        self._transaction = Transaction()

    def checkBasics(self):
        self._storage.tpc_begin(self._transaction)
        # This should simply return
        self._storage.tpc_begin(self._transaction)
        # Aborting is easy
        self._storage.tpc_abort(self._transaction)
        # Test a few expected exceptions when we're doing operations giving a
        # different Transaction object than the one we've begun on.
        self._storage.tpc_begin(self._transaction)
        self.assertRaises(
            StorageTransactionError,
            self._storage.store,
            0, 0, 0, 0, Transaction())
        self.assertRaises(
            StorageTransactionError,
            self._storage.abortVersion,
            0, Transaction())
        self.assertRaises(
            StorageTransactionError,
            self._storage.commitVersion,
            0, 1, Transaction())
        self.assertRaises(
            StorageTransactionError,
            self._storage.store,
            0, 1, 2, 3, Transaction())

    def checkNonVersionStore(self, oid=None, revid=None, version=None):
        # Some objects to store
        if oid is None:
            oid = self._storage.new_oid()
        if revid is None:
            revid = ZERO
        data = pickle.dumps(7)
        if version is None:
            version = ''
        # Start the transaction, store an object, and be sure the revision id
        # is different than what we passed.
        self._storage.tpc_begin(self._transaction)
        newrevid = self._storage.store(oid, revid, data, version,
                                       self._transaction)
        assert newrevid <> revid
        # Finish the transaction.
        self._storage.tpc_vote(self._transaction)
        self._storage.tpc_finish(self._transaction)

    def checkLen(self):
        # The length of the database ought to grow by one each time
        assert len(self._storage) == 0
        self.checkNonVersionStore()
        assert len(self._storage) == 1
        self.checkNonVersionStore()
        assert len(self._storage) == 2

    def checkNonVersionStoreAndLoad(self):
        oid = self._storage.new_oid()
        self.checkNonVersionStore(oid)
        data, revid = self._storage.load(oid, '')
        assert revid == ZERO
        value = pickle.loads(data)
        assert value == 7



class FullStorageAPI(StorageAPI):
    import Full
    ConcreteStorage = Full.Full


class MinimalStorageAPI(StorageAPI):
    import Minimal
    ConcreteStorage = Minimal.Minimal



def suite():
    suite = unittest.TestSuite()
    # Minimal storage tests
    suite.addTest(MinimalStorageAPI('checkBasics'))
    suite.addTest(MinimalStorageAPI('checkNonVersionStore'))
    suite.addTest(MinimalStorageAPI('checkLen'))
    suite.addTest(MinimalStorageAPI('checkNonVersionStoreAndLoad'))
    # Full storage tests
    suite.addTest(FullStorageAPI('checkBasics'))
    suite.addTest(FullStorageAPI('checkNonVersionStore'))
    suite.addTest(FullStorageAPI('checkLen'))
    suite.addTest(FullStorageAPI('checkNonVersionStoreAndLoad'))
    return suite



if __name__ == '__main__':
    unittest.main(defaultTest='suite')
