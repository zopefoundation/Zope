# Unit test for database creation

import os
import errno
import unittest



class BaseFramework(unittest.TestCase):
    def setUp(self):
        from ZODB import DB

        self._dbhome = 'test-db'
        os.mkdir(self._dbhome)

        try:
            self._storage = self.ConcreteStorage(self._dbhome)
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
    

class TestMixin:
    def checkDBHomeExists(self):
        assert os.path.isdir(self._dbhome)



class MinimalBaseFramework(BaseFramework):
    import Minimal
    ConcreteStorage = Minimal.Minimal


class MinimalDBHomeTest(MinimalBaseFramework, TestMixin):
    pass



class FullBaseFramework(BaseFramework):
    import Full
    ConcreteStorage = Full.Full

class FullDBHomeTest(FullBaseFramework, TestMixin):
    pass



def suite():
    suite = unittest.TestSuite()
    suite.addTest(MinimalDBHomeTest('checkDBHomeExists'))
    suite.addTest(FullDBHomeTest('checkDBHomeExists'))
    return suite



if __name__ == '__main__':
    unittest.main(defaultTest='suite')
