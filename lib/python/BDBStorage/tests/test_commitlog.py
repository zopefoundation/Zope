# Test the operation of the CommitLog classes

import os
import errno
import unittest
from bsddb3Storage import CommitLog

# BAW: Lots of other things to check:
# - creating with a named directory
# - creating with an existing file via filename
# - creating with a file object with # incorrect mode or permissions
# - creating with a file object raising the two flavors of LogCorruptedError
# - The various forms of LogCorruptedError in PacklessLog.next()



class CreateCommitLogTest(unittest.TestCase):
    def checkCreateNoFile(self):
        log = CommitLog.CommitLog()
        filename = log.get_filename()
        try:
            assert os.path.exists(filename)
        finally:
            log.close(unlink=1)
            assert not os.path.exists(filename)

    def checkCreateWithFilename(self):
        filename = 'commit.log'
        log = CommitLog.CommitLog(filename)
        try:
            assert os.path.exists(filename)
        finally:
            log.close(unlink=1)
            assert not os.path.exists(filename)

    def checkCreateWithFileobj(self):
        filename = 'commit.log'
        fp = open(filename, 'w+b')
        try:
            self.assertRaises(CommitLog.TruncationError,
                              CommitLog.CommitLog, fp)
        finally:
            fp.close()
            assert not os.path.exists(filename)

    def checkCloseDoesUnlink(self):
        log = CommitLog.CommitLog()
        filename = log.get_filename()
        log.close()
        assert not os.path.exists(filename)

    def checkDel(self):
        log = CommitLog.CommitLog()
        filename = log.get_filename()
        del log
        assert not os.path.exists(filename)



class BaseSetupTearDown(unittest.TestCase):
    def setUp(self):
        self._log = CommitLog.CommitLog()

    def tearDown(self):
        try:
            self._log.close(unlink=1)
        except OSError, e:
            if e.errno <> errno.ENOENT: raise



class CommitLogStateTransitionTest(BaseSetupTearDown):
    def checkProperStart(self):
        # BAW: best we can do is make sure we can start a new commit log
        self._log.start()

    def checkAppendSetsOpen(self):
        # BAW: Best we can do is assert that the state isn't START
        self._log._append('x', 'ignore')
        self.assertRaises(CommitLog.StateTransitionError, self._log.start)

    def checkPromiseSetsPromise(self):
        # BAW: Best we can do is assert that state isn't START
        self._log.promise()
        self.assertRaises(CommitLog.StateTransitionError, self._log.start)

    def checkBadDoublePromise(self):
        self._log.promise()
        self.assertRaises(CommitLog.StateTransitionError, self._log.promise)

    def checkFinishSetsStart(self):
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
            self.__counter = self.__counter + 1

    def __getitem__(self, i):
        if 0 <= i < 10:
            return chr(i+65), i
        raise IndexError



class LowLevelStoreAndLoadTest(BaseSetupTearDown):
    def checkOneStoreAndLoad(self):
        self._log.start()
        self._log._append('x', 'ignore')
        self._log.promise()
        x, ignore = self._log._next()
        assert x == 'x' and ignore == 'ignore'
        assert None == self._log._next()

    def checkTenStoresAndLoads(self):
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
        self._log.write_object(oid=10, pickle='ignore')
        self._log.promise()
        oid, pickle = self._log.next()
        assert oid == 10 and pickle == 'ignore'
        assert None == self._log.next()

    def checkTenStoresAndLoads(self):
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



def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(CreateCommitLogTest, 'check'))
    suite.addTest(unittest.makeSuite(CommitLogStateTransitionTest, 'check'))
    suite.addTest(unittest.makeSuite(LowLevelStoreAndLoadTest, 'check'))
    suite.addTest(unittest.makeSuite(PacklessLogTest, 'check'))
    suite.addTest(unittest.makeSuite(FullLogTest, 'check'))
    return suite



if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
