##############################################################################
#
# Copyright (c) 2001 Zope Corporation and Contributors.
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

# Basic test framework class for both the BDBFullStorage and BDBMinimalStorage
# Berkeley storages

import os
import errno
import shutil

from BDBStorage.BerkeleyBase import BerkeleyConfig
from ZODB.tests.StorageTestBase import StorageTestBase

DBHOME = 'test-db'



class BerkeleyTestBase(StorageTestBase):
    def _config(self):
        # Checkpointing just slows the tests down because we have to wait for
        # the thread to properly shutdown.  This can take up to 10 seconds, so
        # for the purposes of the test suite we shut off this thread.
        config = BerkeleyConfig()
        config.interval = 0
        return config

    def _envdir(self):
        return DBHOME

    def open(self):
        self._storage = self.ConcreteStorage(
            self._envdir(), config=self._config())

    def _zap_dbhome(self, dir=None):
        if dir is None:
            dir = self._envdir()
        # XXX Pre-Python 2.3 doesn't ignore errors if the first arg doesn't
        # exist, even if the second is True.
        try:
            shutil.rmtree(dir, 1)
        except OSError, e:
            if e.errno <> errno.ENOENT: raise

    def _mk_dbhome(self, dir=None):
        if dir is None:
            dir = self._get_envdir()
        os.mkdir(dir)
        try:
            return self.ConcreteStorage(dir, config=self._config())
        except:
            self._zap_dbhome()
            raise

    def setUp(self):
        StorageTestBase.setUp(self)
        self._zap_dbhome()
        self.open()

    def tearDown(self):
        StorageTestBase.tearDown(self)
        self._zap_dbhome()



class MinimalTestBase(BerkeleyTestBase):
    from BDBStorage import BDBMinimalStorage
    ConcreteStorage = BDBMinimalStorage.BDBMinimalStorage


class FullTestBase(BerkeleyTestBase):
    from BDBStorage import BDBFullStorage
    ConcreteStorage = BDBFullStorage.BDBFullStorage
