# Unit test for database creation

import os
import errno
import unittest



class MinimalBaseFramework(unittest.TestCase):
    def setUp(self):
        import Minimal
        from ZODB import DB

        self._dbhome = 'test-db'
        os.mkdir(self._dbhome)

        try:
            self._storage = Minimal.Minimal(self._dbhome)
            self._db = DB(self._storage)
            self._conn = self._db.open()
            self._root = self._conn.root()
        except:
            self.tearDown()
            raise

    def tearDown(self):
        for file in os.listdir(self._dbhome):
            os.unlink(os.path.join(self._dbhome, file))
        os.removedirs(self._dbhome)



class FullBaseFramework(unittest.TestCase):
    def setUp(self):
        import Full
        from ZODB import DB

        self._dbhome = 'test-db'
        os.mkdir(self._dbhome)

        try:
            self._storage = Full.Full(self._dbhome)
            self._db = DB(self._storage)
            self._conn = self._db.open()
            self._root = self._conn.root()
        except:
            self.tearDown()
            raise

    def tearDown(self):
        for file in os.listdir(self._dbhome):
            os.unlink(os.path.join(self._dbhome, file))
        os.removedirs(self._dbhome)



class MinimalDBHomeTest(MinimalBaseFramework):
    def checkDBHomeExists(self):
        """Minimal: Database creation w/ explicit db_home"""
        assert os.path.isdir(self._dbhome)



class FullDBHomeTest(FullBaseFramework):
    def checkDBHomeExists(self):
        """Full: Database creation w/ explicit db_home"""
        assert os.path.isdir(self._dbhome)



def suite():
    suite = unittest.TestSuite()
    suite.addTest(MinimalDBHomeTest('checkDBHomeExists'))
    suite.addTest(FullDBHomeTest('checkDBHomeExists'))
    return suite



if __name__ == '__main__':
    unittest.main(defaultTest='suite')
