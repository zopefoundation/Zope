import unittest
import Testing
import Zope2
Zope2.startup()

import os
import shutil
import time
import transaction
import tempfile
import ZODB

from OFS.Application import Application
from Products.PythonScripts.PythonScript import manage_addPythonScript
from ZODB.FileStorage import FileStorage

class HistoryTests(unittest.TestCase):

    def setUp(self):
        # set up a zodb
        # we can't use DemoStorage here 'cos it doesn't support History
        self.dir = tempfile.mkdtemp()
        self.s = FileStorage(os.path.join(self.dir,'testHistory.fs'),create=True)
        self.connection = ZODB.DB(self.s).open()
        r = self.connection.root()
        a = Application()
        r['Application'] = a
        self.root = a
        # create a python script
        manage_addPythonScript(a,'test')
        self.ps = ps = a.test
        # commit some changes
        ps.write('return 1')
        t = transaction.get()
        # undo note made by Application instantiation above.
        t.description = None 
        t.note('Change 1')
        t.commit()
        time.sleep(0.02) # wait at least one Windows clock tick
        ps.write('return 2')
        t = transaction.get()
        t.note('Change 2')
        t.commit()
        time.sleep(0.02) # wait at least one Windows clock tick
        ps.write('return 3')
        t = transaction.get()
        t.note('Change 3')
        t.commit()

    def tearDown(self):
        # get rid of ZODB
        transaction.abort()
        self.connection.close()
        self.s.close()
        del self.root
        del self.connection
        del self.s
        shutil.rmtree(self.dir)
        
    def test_manage_change_history(self):
        r = self.ps.manage_change_history()
        self.assertEqual(len(r),3) # three transactions
        for i in range(3):
            entry = r[i]
            # check no new keys show up without testing
            self.assertEqual(len(entry.keys()),6)
            # the transactions are in newest-first order
            self.assertEqual(entry['description'],'Change %i' % (3-i))
            self.failUnless('key' in entry) 
            # lets not assume the size will stay the same forever
            self.failUnless('size' in entry) 
            self.failUnless('tid' in entry) 
            self.failUnless('time' in entry) 
            if i:
                # check times are increasing
                self.failUnless(entry['time']<r[i-1]['time'])
            self.assertEqual(entry['user_name'],'')

    def test_manage_historyCopy(self):
        # we assume this works 'cos it's tested above
        r = self.ps.manage_change_history()
        # now we do the copy
        self.ps.manage_historyCopy(
            keys=[r[2]['key']]
                  )
        # do a commit, just like ZPublisher would
        transaction.commit()
        # check the body is as it should be, we assume (hopefully not foolishly)
        # that all other attributes will behave the same
        self.assertEqual(self.ps._body,
                         'return 1\n')
                                
def test_suite():
    suite = unittest.TestSuite()
    suite.addTest( unittest.makeSuite( HistoryTests ) )
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
