##############################################################################
#
# Copyright (c) 2003 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Tests for the CacheManager.

$Id$
"""

import unittest

import ZODB

from App.CacheManager import CacheManager


class TestCacheManager(CacheManager):
    # Derived CacheManager that fakes enough of the DatabaseManager to
    # make it possible to test at least some parts of the CacheManager.

    def __init__(self, connection):
        self._p_jar = connection


class DummyConnection:

    def __init__(self, db, version=None):
        self.__db = db
        self.__version = version

    def db(self):
        return self.__db

    def getVersion(self):
        return self.__version


class DummyDB:

    def __init__(self, cache_size, vcache_size):
        self._set_sizes(cache_size, vcache_size)

    def _set_sizes(self, cache_size, vcache_size):
        self.__cache_size = cache_size
        self.__vcache_size = vcache_size

    def getCacheSize(self):
        return self.__cache_size

    def getVersionCacheSize(self):
        return self.__vcache_size


class CacheManagerTestCase(unittest.TestCase):

    def setUp(self):
        self.db = DummyDB(42, 24)
        self.connection = DummyConnection(self.db)
        self.manager = TestCacheManager(self.connection)

    def test_cache_size(self):
        self.assertEqual(self.manager.cache_size(), 42)
        self.db._set_sizes(12, 2)
        self.assertEqual(self.manager.cache_size(), 12)

    def test_version_cache_size(self):
        self.connection = DummyConnection(self.db, "my version")
        self.manager = TestCacheManager(self.connection)
        # perform test
        self.assertEqual(self.manager.cache_size(), 24)
        self.db._set_sizes(12, 2)
        self.assertEqual(self.manager.cache_size(), 2)


def test_suite():
    return unittest.makeSuite(CacheManagerTestCase)
