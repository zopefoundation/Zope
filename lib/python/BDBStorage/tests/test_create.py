# Unit test for database creation

import os
import unittest
import BerkeleyTestBase    



class TestMixin:
    def checkDBHomeExists(self):
        assert os.path.isdir(BerkeleyTestBase.DBHOME)


class MinimalCreateTest(BerkeleyTestBase.BerkeleyTestBase,
                        BerkeleyTestBase.MinimalTestBase,
                        TestMixin):
    pass


class FullCreateTest(BerkeleyTestBase.BerkeleyTestBase,
                     BerkeleyTestBase.FullTestBase,
                     TestMixin):
    pass



def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(MinimalCreateTest, 'check'))
    suite.addTest(unittest.makeSuite(FullCreateTest, 'check'))
    return suite



if __name__ == '__main__':
    unittest.main(defaultTest='suite')
