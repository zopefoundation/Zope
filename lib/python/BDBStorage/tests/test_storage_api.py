# Unit tests for basic storage functionality

import unittest

from ZODB import POSException

import BerkeleyTestBase
from BasicStorage import BasicStorage
from VersionStorage import VersionStorage
from TransactionalUndoStorage import TransactionalUndoStorage
from TransactionalUndoVersionStorage import TransactionalUndoVersionStorage
from PackableStorage import PackableStorage



class MinimalTest(BerkeleyTestBase.MinimalTestBase, BasicStorage):
    def checkLoadSerial(self):
        # This storage doesn't support versions, so we should get an exception
        self.assertRaises(POSException.Unsupported,
                          BasicStorage.checkLoadSerial,
                          self)

    def checkVersionedStoreAndLoad(self):
        # This storage doesn't support versions, so we should get an exception
        oid = self._storage.new_oid()
        self.assertRaises(POSException.Unsupported,
                          self._dostore,
                          oid, data=11, version='a version')


class FullTest(BerkeleyTestBase.FullTestBase, BasicStorage, VersionStorage,
               TransactionalUndoStorage, TransactionalUndoVersionStorage,
               PackableStorage):
    pass



def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(MinimalTest, 'check'))
    suite.addTest(unittest.makeSuite(FullTest, 'check'))
    return suite



if __name__ == '__main__':
    unittest.main(defaultTest='suite')
