##############################################################################
#
# Copyright (c) 2001 Zope Corporation and Contributors. All Rights Reserved.
# 
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
# 
##############################################################################
import sys, os, unittest

import ZODB
from Products.Transience.Transience import TransientObjectContainer
from Products.Transience.TransientObject import TransientObject
import Products.Transience.TransientObject
import Products.Transience.Transience
from unittest import TestCase, TestSuite, TextTestRunner, makeSuite
import time as oldtime
import fauxtime

class TestTransientObject(TestCase):
    def setUp(self):
        Products.Transience.Transience.time = fauxtime
        Products.Transience.TransientObject.time = fauxtime
        self.errmargin = .20
        self.timeout = 60
        self.t = TransientObjectContainer('sdc', timeout_mins=self.timeout/60)

    def tearDown(self):
        Products.Transience.Transience.time = oldtime
        Products.Transience.TransientObject.time = oldtime
        self.t = None
        del self.t
        
    def test_id(self):
        t = self.t.new('xyzzy')
        assert t.getId() != 'xyzzy'
        assert t.getContainerKey() == 'xyzzy'

    def test_validate(self):
        t = self.t.new('xyzzy')
        assert t.isValid()
        t.invalidate()
        assert not t.isValid()

    def test_getLastAccessed(self):
        t = self.t.new('xyzzy')
        ft = fauxtime.time()
        assert t.getLastAccessed() <= ft

    def test_getCreated(self):
        t = self.t.new('xyzzy')
        ft = fauxtime.time()
        assert t.getCreated() <= ft

    def test_getLastModifiedUnset(self):
        t = self.t.new('xyzzy')
        assert t.getLastModified() == None

    def test_getLastModifiedSet(self):
        t = self.t.new('xyzzy')
        t['a'] = 1
        assert t.getLastModified() is not None

    def testSetLastModified(self):
        t = self.t.new('xyzzy')
        ft = fauxtime.time()
        t.setLastModified()
        assert t.getLastModified() is not None

    def test_setLastAccessed(self):
        t = self.t.new('xyzzy')
        ft = fauxtime.time()
        assert t.getLastAccessed() <= ft
        fauxtime.sleep(self.timeout)   # go to sleep past the granuarity
        ft2 = fauxtime.time()
        t.setLastAccessed()
        ft3 = fauxtime.time()
        assert t.getLastAccessed() <= ft3
        assert t.getLastAccessed() >= ft2

    def _genKeyError(self, t):
        return t.get('foobie')

    def _genLenError(self, t):
        return t.len()

    def test_dictionaryLike(self):
        t = self.t.new('keytest')
        t.update(data)
        assert t.keys() == data.keys()
        assert t.values() == data.values()
        assert t.items() == data.items()
        for k in data.keys():
            assert t.get(k) == data.get(k)
        assert t.get('foobie') is None
        self.assertRaises(AttributeError, self._genLenError, t)
        assert t.get('foobie',None) is None
        assert t.has_key('a') 
        assert not t.has_key('foobie') 
        t.clear()
        assert not len(t.keys()) 

    def test_TTWDictionary(self):
        t = self.t.new('mouthfultest')
        t.set('foo', 'bar')
        assert t['foo'] == 'bar'
        assert t.get('foo') == 'bar'
        t.set('foobie', 'blech')
        t.delete('foobie')
        assert t.get('foobie') is None 


def test_suite():
    testsuite = makeSuite(TestTransientObject, 'test')
    alltests = TestSuite((testsuite,))
    return alltests

data = {
    'a': 'a',
    1: 1,
    'Mary': 'no little lamb for you today!',
    'epoch': 999999999,
    'fauxtime': fauxtime
    }

if __name__ == '__main__':
    runner = TextTestRunner(verbosity=9)
    runner.run(test_suite())

