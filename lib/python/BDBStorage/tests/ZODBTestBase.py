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

# Base class for unit tests at the ZODB layer

import os

from ZODB import DB
from BDBStorage.tests.BerkeleyTestBase import BerkeleyTestBase

DBHOME = 'test-db'



class ZODBTestBase(BerkeleyTestBase):
    def setUp(self):
        BerkeleyTestBase.setUp(self)
        self._db = None
        try:
            self._db = DB(self._storage)
            self._conn = self._db.open()
            self._root = self._conn.root()
        except:
            self.tearDown()
            raise

    def _close(self):
        if self._db is not None:
            self._db.close()
            self._db = self._storage = self._conn = self._root = None

    def tearDown(self):
        # If the tests exited with any uncommitted objects, they'll blow up
        # subsequent tests because the next transaction commit will try to
        # commit those object.  But they're tied to closed databases, so
        # that's broken.  Aborting the transaction now saves us the headache.
        try:
            get_transaction().abort()
            self._close()
        finally:
            BerkeleyTestBase.tearDown(self)
