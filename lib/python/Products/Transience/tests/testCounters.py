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

import os
from unittest import TestCase, TestSuite, makeSuite
from ZODB.POSException import ConflictError
from ZODB.FileStorage import FileStorage
from ZODB.DB import DB
import transaction

from Products.Transience.Transience import Length2, Increaser

# Test pattern is copied from BTrees/tests/testConflict.py

class Base(TestCase):
    storage = None

    def setUp(self):
        pass

    def tearDown(self):
        transaction.abort()
        if self.storage is not None:
            self.storage.close()
            self.storage.cleanup()

    def openDB(self):
        n = 'fs_tmp__%s' % os.getpid()
        self.storage = FileStorage(n)
        self.db = DB(self.storage)

class TestLength2(Base):

    def testConflict(self):
        # Set up database connections to provoke conflict.
        self.openDB()
        length = Length2(0)

        r1 = self.db.open().root()
        r1['ob'] = length
        transaction.commit()

        r2 = self.db.open(synch=False).root()
        copy = r2['ob']
        # The following ensures that copy is loaded.
        self.assertEqual(copy(),0)

        # First transaction.
        length.increment(10)
        length.decrement(1)
        transaction.commit()

        # Second transaction.
        length = copy
        length.increment(20)
        length.decrement(2)
        transaction.commit()

        self.assertEqual(length(), 10+20-max(1,2))

class TestIncreaser(Base):

    def testConflict(self):

        # Set up database connections to provoke conflict.
        self.openDB()
        increaser = Increaser(0)

        r1 = self.db.open().root()
        r1['ob'] = increaser
        transaction.commit()

        r2 = self.db.open(synch=False).root()
        copy = r2['ob']
        # The following ensures that copy is loaded.
        self.assertEqual(copy(),0)

        # First transaction.
        increaser.set(10)
        transaction.commit()


        # Second transaction.
        increaser = copy
        increaser.set(20)
        transaction.commit()

        self.assertEqual(increaser(), 20)

def test_suite():
    suite = TestSuite()
    suite.addTest(makeSuite(TestLength2))
    suite.addTest(makeSuite(TestIncreaser))
    return suite
