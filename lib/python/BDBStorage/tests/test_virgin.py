# Test creation of a brand new database, and insertion of root objects.

import unittest
import test_create



class FullNewInsertsTest(test_create.FullBaseFramework):
    def checkIsEmpty(self):
        """Full: Newly created database should be empty"""
        assert not self._root.has_key('names')

    def checkNewInserts(self):
        """Full: Commiting on a newly created database"""
        from Persistence import PersistentMapping

        self._root['names'] = names = PersistentMapping()
        names['Warsaw'] = 'Barry'
        names['Hylton'] = 'Jeremy'
        get_transaction().commit()



class MinimalNewInsertsTest(test_create.MinimalBaseFramework):
    def checkIsEmpty(self):
        """Minimal: Newly created database is empty"""
        assert not self._root.has_key('names')

    def checkNewInserts(self):
        """Minimal: Committing on a newly created database"""
        from Persistence import PersistentMapping

        self._root['names'] = names = PersistentMapping()
        names['Warsaw'] = 'Barry'
        names['Hylton'] = 'Jeremy'
        get_transaction().commit()



def suite():
    suite = unittest.TestSuite()
    suite.addTest(MinimalNewInsertsTest('checkIsEmpty'))
    suite.addTest(MinimalNewInsertsTest('checkNewInserts'))
    suite.addTest(FullNewInsertsTest('checkIsEmpty'))
    suite.addTest(FullNewInsertsTest('checkNewInserts'))
    return suite



if __name__ == '__main__':
    unittest.main(defaultTest='suite')
