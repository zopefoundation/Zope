##############################################################################
#
# Copyright (c) 2002 Zope Corporation and Contributors.
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

import os
import time
import unittest

from ZODB.tests.MinPO import MinPO
from bsddb3Storage.Full import Full
from bsddb3Storage.BerkeleyBase import BerkeleyConfig
from bsddb3Storage.tests.BerkeleyTestBase import BerkeleyTestBase



class TestAutopackBase(BerkeleyTestBase):
    def _config(self):
        config = BerkeleyConfig()
        # Autopack every 3 seconds, 6 seconds into the past, no classic packs
        config.frequency = 3
        config.packtime = 6
        config.classicpack = 0
        return config

    def _wait_for_next_autopack(self):
        storage = self._storage
        # BAW: this uses a non-public interface
        packtime = storage._autopacker._nextpack
        while packtime == storage._autopacker._nextpack:
            time.sleep(1)
        
    def _mk_dbhome(self, dir):
        # Create the storage
        os.mkdir(dir)
        try:
            return Full(dir, config=self._config())
        except:
            self._zap_dbhome(dir)
            raise



class TestAutopack(TestAutopackBase):
    def checkAutopack(self):
        unless = self.failUnless
        raises = self.assertRaises
        storage = self._storage
        # Wait for an autopack operation to occur, then make three revisions
        # to an object.  Wait for the next autopack operation and make sure
        # all three revisions still exist.  Then sleep 10 seconds and wait for
        # another autopack operation.  Then verify that the first two
        # revisions have been packed away.
        oid = storage.new_oid()
        self._wait_for_next_autopack()
        revid1 = self._dostore(oid, data=MinPO(2112))
        revid2 = self._dostore(oid, revid=revid1, data=MinPO(2113))
        revid3 = self._dostore(oid, revid=revid2, data=MinPO(2114))
        self._wait_for_next_autopack()
        unless(storage.loadSerial(oid, revid1))
        unless(storage.loadSerial(oid, revid2))
        unless(storage.loadSerial(oid, revid3))
        # Should be enough time for the revisions to get packed away
        time.sleep(10)
        self._wait_for_next_autopack()
        # The first two revisions should now be gone, but the third should
        # still exist because it's the current revision, and we haven't done a
        # classic pack.
        raises(KeyError, self._storage.loadSerial, oid, revid1)
        raises(KeyError, self._storage.loadSerial, oid, revid2)
        unless(storage.loadSerial(oid, revid3))



class TestAutomaticClassicPack(TestAutopackBase):
    def _config(self):
        config = BerkeleyConfig()
        # Autopack every 3 seconds, 6 seconds into the past, no classic packs
        config.frequency = 3
        config.packtime = 6
        config.classicpack = 1
        return config

    def checkAutomaticClassicPack(self):
        unless = self.failUnless
        raises = self.assertRaises
        storage = self._storage
        # Wait for an autopack operation to occur, then make three revisions
        # to an object.  Wait for the next autopack operation and make sure
        # all three revisions still exist.  Then sleep 10 seconds and wait for
        # another autopack operation.  Then verify that the first two
        # revisions have been packed away.
        oid = storage.new_oid()
        self._wait_for_next_autopack()
        revid1 = self._dostore(oid, data=MinPO(2112))
        revid2 = self._dostore(oid, revid=revid1, data=MinPO(2113))
        revid3 = self._dostore(oid, revid=revid2, data=MinPO(2114))
        self._wait_for_next_autopack()
        unless(storage.loadSerial(oid, revid1))
        unless(storage.loadSerial(oid, revid2))
        unless(storage.loadSerial(oid, revid3))
        # Should be enough time for the revisions to get packed away
        time.sleep(10)
        self._wait_for_next_autopack()
        # The first two revisions should now be gone, but the third should
        # still exist because it's the current revision, and we haven't done a
        # classic pack.
        raises(KeyError, self._storage.loadSerial, oid, revid1)
        raises(KeyError, self._storage.loadSerial, oid, revid2)
        raises(KeyError, self._storage.loadSerial, oid, revid3)



def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestAutopack, 'check'))
    suite.addTest(unittest.makeSuite(TestAutomaticClassicPack, 'check'))
    return suite



if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
