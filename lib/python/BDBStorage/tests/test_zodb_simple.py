# Test some simple ZODB level stuff common to both the Minimal and Full
# storages, like transaction aborts and commits, changing objects, etc.
# Doesn't test undo, versions, or packing.

import os
import errno
import time
import unittest

DBHOME = 'test-db'



class CommitAndRead(unittest.TestCase):
    # Never tear down the test framework since we want the database support
    # files to persist.  MasterSetup will take care of cleaning things up when
    # we're done.
    def setUp(self):
        from ZODB import DB

        self._dbhome = DBHOME
        try:
            os.mkdir(self._dbhome)
        except OSError, e:
            if e.errno <> errno.EEXIST: raise

        try:
            self._storage = self.ConcreteStorage(self._dbhome)
            self._db = DB(self._storage)
            self._conn = self._db.open()
            self._root = self._conn.root()
        except:
            self.tearDown()
            raise

    def tearDown(self):
        for file in os.listdir(DBHOME):
            os.unlink(os.path.join(DBHOME, file))
        os.removedirs(DBHOME)
        
    def checkCommit(self):
        from Persistence import PersistentMapping

        assert not self._root
        names = self._root['names'] = PersistentMapping()
        names['Warsaw'] = 'Barry'
        names['Hylton'] = 'Jeremy'
        get_transaction().commit()

    def checkReadAfterCommit(self):
        self.checkCommit()
        names = self._root['names']
        assert names['Warsaw'] == 'Barry'
        assert names['Hylton'] == 'Jeremy'
        assert names.get('Drake') is None

    def checkAbortAfterRead(self):
        self.checkReadAfterCommit()
        names = self._root['names']
        names['Drake'] = 'Fred'
        get_transaction().abort()

    def checkReadAfterAbort(self):
        self.checkAbortAfterRead()
        names = self._root['names']
        assert names.get('Drake') is None

    def checkChangingCommits(self):
        self.checkReadAfterAbort()
        now = time.time()
        # Make sure the last timestamp was more than 3 seconds ago
        timestamp = self._root.get('timestamp')
        if timestamp is None:
            timestamp = self._root['timestamp'] = 0
            get_transaction().commit()
        assert now > timestamp + 3
        self._root['timestamp'] = now
        time.sleep(3)



class MinimalCommitAndRead(CommitAndRead):
    import Minimal
    ConcreteStorage = Minimal.Minimal


class FullCommitAndRead(CommitAndRead):
    import Full
    ConcreteStorage = Full.Full



def suite():
    suite = unittest.TestSuite()
    # On the Minimal storage
    suite.addTest(MinimalCommitAndRead('checkCommit'))
    suite.addTest(MinimalCommitAndRead('checkReadAfterCommit'))
    suite.addTest(MinimalCommitAndRead('checkAbortAfterRead'))
    suite.addTest(MinimalCommitAndRead('checkReadAfterCommit'))
    for i in range(5):
        suite.addTest(MinimalCommitAndRead('checkChangingCommits'))
    # On the Full storage
    suite.addTest(FullCommitAndRead('checkCommit'))
    suite.addTest(FullCommitAndRead('checkReadAfterCommit'))
    suite.addTest(FullCommitAndRead('checkAbortAfterRead'))
    suite.addTest(FullCommitAndRead('checkReadAfterCommit'))
    for i in range(5):
        suite.addTest(FullCommitAndRead('checkChangingCommits'))
    return suite



if __name__ == '__main__':
    unittest.main(defaultTest='suite')
