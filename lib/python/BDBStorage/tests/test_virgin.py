# Test creation of a brand new database, and insertion of root objects.

import unittest
import test_create



class BaseInsertMixin:
    def checkIsEmpty(self):
        assert not self._root.has_key('names')

    def checkNewInserts(self):
        from Persistence import PersistentMapping

        self._root['names'] = names = PersistentMapping()
        names['Warsaw'] = 'Barry'
        names['Hylton'] = 'Jeremy'
        get_transaction().commit()



class FullNewInsertsTest(test_create.FullBaseFramework, BaseInsertMixin):
    pass


class MinimalNewInsertsTest(test_create.MinimalBaseFramework, BaseInsertMixin):
    pass



def suite():
    suite = unittest.TestSuite()
    suite.addTest(MinimalNewInsertsTest('checkIsEmpty'))
    suite.addTest(MinimalNewInsertsTest('checkNewInserts'))
    suite.addTest(FullNewInsertsTest('checkIsEmpty'))
    suite.addTest(FullNewInsertsTest('checkNewInserts'))
    return suite



if __name__ == '__main__':
    unittest.main(defaultTest='suite')
