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
    def _zap_dbhome(self):
        # If the tests exited with any uncommitted objects, they'll blow up
        # subsequent tests because the next transaction commit will try to
        # commit those object.  But they're tied to closed databases, so
        # that's broken.  Aborting the transaction now saves us the headache.
        try:
            for file in os.listdir(DBHOME):
                os.unlink(os.path.join(DBHOME, file))
            os.removedirs(DBHOME)
        except OSError, e:
            if e.errno <> errno.ENOENT: raise

    def setUp(self):
        StorageTestBase.setUp(self)
        self._zap_dbhome()
        os.mkdir(DBHOME)
        try:
            self._storage = self.ConcreteStorage(DBHOME)
        except:
            self._zap_dbhome()
            raise

    def tearDown(self):
        StorageTestBase.tearDown(self)
        self._zap_dbhome()



class MinimalTestBase(BerkeleyTestBase):
    from bsddb3Storage import Minimal
    ConcreteStorage = Minimal.Minimal


class FullTestBase(BerkeleyTestBase):
    from bsddb3Storage import Full
    ConcreteStorage = Full.Full


class AutopackTestBase(BerkeleyTestBase):
    from bsddb3Storage import Autopack
    ConcreteStorage = Autopack.Autopack
