# Test creation of a brand new database, and insertion of root objects.

import unittest

from ZODBTestBase import ZODBTestBase
from Persistence import PersistentMapping
        


class InsertMixin:
    def checkIsEmpty(self):
        assert not self._root.has_key('names')

    def checkNewInserts(self):
        self._root['names'] = names = PersistentMapping()
        names['Warsaw'] = 'Barry'
        names['Hylton'] = 'Jeremy'
        get_transaction().commit()



class FullNewInsertsTest(ZODBTestBase, InsertMixin):
    from bsddb3Storage import Full
    ConcreteStorage = Full.Full


class MinimalNewInsertsTest(ZODBTestBase, InsertMixin):
    from bsddb3Storage import Minimal
    ConcreteStorage = Minimal.Minimal



def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(MinimalNewInsertsTest, 'check'))
    suite.addTest(unittest.makeSuite(FullNewInsertsTest, 'check'))
    return suite



if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
