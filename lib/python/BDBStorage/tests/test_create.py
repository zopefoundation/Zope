# Unit test for database creation

import os
import errno
import unittest



class DBHomeTest(unittest.TestCase):
    def setUp(self):
        import Minimal
        from ZODB import DB
        from BTree import BTree

        self._dbhome = 'test-db'
        os.mkdir(self._dbhome)

        self._storage = Minimal.Minimal(self._dbhome)
        self._db = DB(self._storage)
        self._conn = self._db.open()
        self._root = self._conn.root()

    def tearDown(self):
        for file in os.listdir(self._dbhome):
            os.unlink(os.path.join(self._dbhome, file))
        os.removedirs(self._dbhome)

    def checkDBHomeExists(self):
        """Database creation with an explicit db_home create the directory"""
        assert os.path.isdir(self._dbhome)



def suite():
    suite = unittest.TestSuite()
    suite.addTest(DBHomeTest('checkDBHomeExists'))
    return suite
