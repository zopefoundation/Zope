# Test creation of a brand new database, and insertion of root objects.

import unittest
from test_create import DBHomeTest



class NewInsertsTest(DBHomeTest):
    def checkIsEmpty(self):
        """Checks that a newly created database is empty"""
        assert not self._root.has_key('names')

    def checkNewInserts(self):
        from BTree import BTree

        self._root['names'] = names = BTree()
        names['Warsaw'] = 'Barry'
        names['Hylton'] = 'Jeremy'
        get_transaction().commit()



def suite():
    suite = unittest.TestSuite()
    suite.addTest(NewInsertsTest('checkIsEmpty'))
    suite.addTest(NewInsertsTest('checkNewInserts'))
    return suite
