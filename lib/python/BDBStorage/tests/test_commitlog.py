# Test the operation of the CommitLog classes

import os
import unittest
import CommitLog

# BAW: Lots of other things to check:
# - creating with a named directory
# - creating with an existing file via filename
# - creating with a file object with # incorrect mode or permissions
# - creating with a file object raising the two flavors of LogCorruptedError
# - The various forms of LogCorruptedError in PacklessLog.next()



class CreateCommitLogTest(unittest.TestCase):
    def checkCreateNoFile(self):
        """Commit log creation with auto-generation of log file"""
        log = CommitLog.CommitLog()
        filename = log.get_filename()
        assert os.path.exists(filename)
        os.unlink(filename)

    def checkCreateWithFilename(self):
        """Commit log creation with named file"""
        filename = 'commit.log'
        log = CommitLog.CommitLog(filename)
        assert os.path.exists(filename)
        os.unlink(filename)

    def checkCreateWithFileobj(self):
        """Commit log use of existing file object"""
        filename = 'commit.log'
        fp = open(filename, 'w+b')
        self.assertRaises(CommitLog.TruncationError,
                          CommitLog.CommitLog, fp)
        os.unlink(filename)



class CloseCommitLogTest(unittest.TestCase):
    def setUp(self):
        self._log = CommitLog.CommitLog()
        self._filename = self._log.get_filename()

    def tearDown(self):
        if self._filename:
            os.unlink(self._filename)

    def checkDel(self):
        """CommitLog.__del__()"""
        del self._log
        assert os.path.exists(self._filename)

    def checkCloseDefaults(self):
        """CommitLog.close(), same as CommitLog.__del__()"""
        self._log.close()
        assert os.path.exists(self._filename)

    def checkCloseWithUnlink(self):
        """CommitLog.close(unlink=1)"""
        self._log.close(unlink=1)
        assert not os.path.exists(self._filename)
        self._filename = None



class BaseSetupTearDown(unittest.TestCase):
    def setUp(self):
        self._log = CommitLog.CommitLog()

    def tearDown(self):
        self._log.close(unlink=1)



class CommitLogStateTransitionTest(BaseSetupTearDown):
    def checkProperStart(self):
        """Newly created log file initializes state to START"""
        # BAW: best we can do is make sure we can start a new commit log
        self._log.start()

    def checkAppendSetsOpen(self):
        """First append sets log file state to OPEN"""
        # BAW: Best we can do is assert that the state isn't START
        self._log._append('x', 'ignore')
        self.assertRaises(CommitLog.StateTransitionError, self._log.start)

    def checkPromiseSetsPromise(self):
        """Promising from START or OPEN sets state to PROMISE"""
        # BAW: Best we can do is assert that state isn't START
        self._log.promise()
        self.assertRaises(CommitLog.StateTransitionError, self._log.start)

    def checkBadDoublePromise(self):
        """Promising an already promised transaction fails"""
        self._log.promise()
        self.assertRaises(CommitLog.StateTransitionError, self._log.promise)

    def checkFinishSetsStart(self):
        """Finishing sets state to START"""
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
            self.__counter += 1

    def __getitem__(self, i):
        if 0 <= i < 10:
            return chr(i+65), i
        raise IndexError



class LowLevelStoreAndLoadTest(BaseSetupTearDown):
    def checkOneStoreAndLoad(self):
        """Low-level storing one record and reading it back"""
        self._log.start()
        self._log._append('x', 'ignore')
        self._log.promise()
        x, ignore = self._log._next()
        assert x == 'x' and ignore == 'ignore'
        assert None == self._log._next()

    def checkTenStoresAndLoads(self):
        """Low-level storing ten records and reading them back"""
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
            assert rec[0] == c and rec[1] == i
        self.assertRaises(IndexError, g)
        


class PacklessLogTest(BaseSetupTearDown):
    def setUp(self):
        self._log = CommitLog.PacklessLog()
        self._log.start()

    def checkOneStoreAndLoad(self):
        """PacklessLog: API for one object"""
        self._log.write_object(oid=10, pickle='ignore')
        self._log.promise()
        oid, pickle = self._log.next()
        assert oid == 10 and pickle == 'ignore'
        assert None == self._log.next()

    def checkTenStoresAndLoads(self):
        """PacklessLog: API storing ten objects and reading them back"""
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
            assert oid == i and pickle == c*10
        self.assertRaises(IndexError, g)



class FullLogTest(BaseSetupTearDown):
    def setUp(self):
        self._log = CommitLog.FullLog()
        self._log.start()

    def checkOneStoreAndLoad(self):
        """FullLog: API for one object"""
        oid = 10
        vid = 8
        nvrevid = 0
        pickle = 'ignore'
        prevrevid = 9
        self._log.write_object(oid, vid, nvrevid, pickle, prevrevid)
        self._log.promise()
        rec = self._log.next()
        assert rec
        key, rec = rec
        assert key == 'o' and len(rec) == 6
        assert rec[0] == oid and rec[1] == vid and rec[2] == nvrevid
        assert rec[3] == '' and rec[4] == pickle and rec[5] == prevrevid
        assert None == self._log.next()

    def checkOtherWriteMethods(self):
        """FullLog: check other write_*() methods"""
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
        assert rec
        key, rec = rec
        assert key == 'o' and len(rec) == 6
        assert rec[0] == oid and rec[1] == zero and rec[2] == zero
        assert rec[3] == lrevid and rec[4] == '' and rec[5] == prevrevid
        rec = self._log.next()
        assert rec
        key, rec = rec
        assert key == 'o' and len(rec) == 6
        assert rec[0] == oid and rec[1] == vid and rec[2] == nvrevid
        assert rec[3] == lrevid and rec[4] == '' and rec[5] == prevrevid
        rec = self._log.next()
        assert rec
        key, rec = rec
        assert key == 'v' and len(rec) == 2
        assert rec[0] == version and rec[1] == vid
        rec = self._log.next()
        assert rec
        key, rec = rec
        assert key == 'd' and len(rec) == 1
        assert rec[0] == vid



def suite():
    suite = unittest.TestSuite()
    # Creation
    suite.addTest(CreateCommitLogTest('checkCreateNoFile'))
    suite.addTest(CreateCommitLogTest('checkCreateWithFilename'))
    suite.addTest(CreateCommitLogTest('checkCreateWithFileobj'))
    # Closing
    suite.addTest(CloseCommitLogTest('checkDel'))
    suite.addTest(CloseCommitLogTest('checkCloseDefaults'))
    suite.addTest(CloseCommitLogTest('checkCloseWithUnlink'))
    # State transitions
    suite.addTest(CommitLogStateTransitionTest('checkProperStart'))
    suite.addTest(CommitLogStateTransitionTest('checkAppendSetsOpen'))
    suite.addTest(CommitLogStateTransitionTest('checkPromiseSetsPromise'))
    suite.addTest(CommitLogStateTransitionTest('checkBadDoublePromise'))
    suite.addTest(CommitLogStateTransitionTest('checkFinishSetsStart'))
    # Base class for storing and loading
    suite.addTest(LowLevelStoreAndLoadTest('checkOneStoreAndLoad'))
    suite.addTest(LowLevelStoreAndLoadTest('checkTenStoresAndLoads'))
    # PacklessLog API
    suite.addTest(PacklessLogTest('checkOneStoreAndLoad'))
    suite.addTest(PacklessLogTest('checkTenStoresAndLoads'))
    # FullLog API
    suite.addTest(FullLogTest('checkOneStoreAndLoad'))
    suite.addTest(FullLogTest('checkOtherWriteMethods'))
    return suite



if __name__ == '__main__':
    unittest.main(defaultTest='suite')
