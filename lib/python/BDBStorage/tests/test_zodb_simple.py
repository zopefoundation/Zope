##############################################################################
#
# Copyright (c) 2001, 2002 Zope Corporation and Contributors.
# All Rights Reserved.
# 
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
# 
##############################################################################

# Test some simple ZODB level stuff common to both the Minimal and Full
# storages, like transaction aborts and commits, changing objects, etc.
# Doesn't test undo, versions, or packing.

import time
import unittest
# Import this here and now so that import failures properly cause the test
# suite to ignore these tests.
import bsddb3

from ZODBTestBase import ZODBTestBase
from Persistence import PersistentMapping



class CommitAndRead:
    def checkCommit(self):
        self.failUnless(not self._root)
        names = self._root['names'] = PersistentMapping()
        names['Warsaw'] = 'Barry'
        names['Hylton'] = 'Jeremy'
        get_transaction().commit()

    def checkReadAfterCommit(self):
        eq = self.assertEqual
        self.checkCommit()
        names = self._root['names']
        eq(names['Warsaw'], 'Barry')
        eq(names['Hylton'], 'Jeremy')
        self.failUnless(names.get('Drake') is None)

    def checkAbortAfterRead(self):
        self.checkReadAfterCommit()
        names = self._root['names']
        names['Drake'] = 'Fred'
        get_transaction().abort()

    def checkReadAfterAbort(self):
        self.checkAbortAfterRead()
        names = self._root['names']
        self.failUnless(names.get('Drake') is None)

    def checkChangingCommits(self):
        self.checkReadAfterAbort()
        now = time.time()
        # Make sure the last timestamp was more than 3 seconds ago
        timestamp = self._root.get('timestamp')
        if timestamp is None:
            timestamp = self._root['timestamp'] = 0
            get_transaction().commit()
        self.failUnless(now > timestamp + 3)
        self._root['timestamp'] = now
        time.sleep(3)



class MinimalCommitAndRead(ZODBTestBase, CommitAndRead):
    from bsddb3Storage import Minimal
    ConcreteStorage = Minimal.Minimal


class FullCommitAndRead(ZODBTestBase, CommitAndRead):
    from bsddb3Storage import Full
    ConcreteStorage = Full.Full



def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(MinimalCommitAndRead, 'check'))
    suite.addTest(unittest.makeSuite(FullCommitAndRead, 'check'))
    return suite



if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
