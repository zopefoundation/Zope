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

# Basic test framework class for both the Full and Minimal Berkeley storages

import os
import errno
from ZODB.tests.StorageTestBase import StorageTestBase

DBHOME = 'test-db'



class BerkeleyTestBase(StorageTestBase):
    def _zap_dbhome(self, dir):
        # If the tests exited with any uncommitted objects, they'll blow up
        # subsequent tests because the next transaction commit will try to
        # commit those object.  But they're tied to closed databases, so
        # that's broken.  Aborting the transaction now saves us the headache.
        try:
            for file in os.listdir(dir):
                os.unlink(os.path.join(dir, file))
            os.removedirs(dir)
        except OSError, e:
            if e.errno <> errno.ENOENT:
                raise

    def _mk_dbhome(self, dir):
        os.mkdir(dir)
        try:
            return self.ConcreteStorage(dir)
        except:
            self._zap_dbhome(dir)
            raise

    def setUp(self):
        StorageTestBase.setUp(self)
        self._zap_dbhome(DBHOME)
        self._storage = self._mk_dbhome(DBHOME)

    def tearDown(self):
        StorageTestBase.tearDown(self)
        self._zap_dbhome(DBHOME)



class MinimalTestBase(BerkeleyTestBase):
    from bsddb3Storage import Minimal
    ConcreteStorage = Minimal.Minimal


class FullTestBase(BerkeleyTestBase):
    from bsddb3Storage import Full
    ConcreteStorage = Full.Full
