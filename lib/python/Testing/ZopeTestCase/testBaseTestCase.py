##############################################################################
#
# Copyright (c) 2005 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Tests the base.TestCase class

NOTE: This is *not* an example TestCase. Do not
use this file as a blueprint for your own tests!

See testPythonScript.py and testShoppingCart.py for
example test cases. See testSkeleton.py for a quick
way of getting started.

$Id$
"""

import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

import transaction

from Testing.ZopeTestCase import base
from Testing.ZopeTestCase import utils
from Testing.ZopeTestCase import connections

from AccessControl import getSecurityManager
from AccessControl.SecurityManagement import newSecurityManager


class HookTest(base.TestCase):

    def setUp(self):
        self._called = []
        base.TestCase.setUp(self)

    def beforeSetUp(self):
        self._called.append('beforeSetUp')
        base.TestCase.beforeSetUp(self)

    def _setup(self):
        self._called.append('_setup')
        base.TestCase._setup(self)

    def afterSetUp(self):
        self._called.append('afterSetUp')
        base.TestCase.afterSetUp(self)

    def beforeTearDown(self):
        self._called.append('beforeTearDown')
        base.TestCase.beforeTearDown(self)

    def beforeClose(self):
        self._called.append('beforeClose')
        base.TestCase.beforeClose(self)

    def afterClear(self):
        self._called.append('afterClear')
        base.TestCase.afterClear(self)

    def assertHooks(self, sequence):
        self.assertEqual(self._called, sequence)


class TestTestCase(HookTest):

    def testSetUp(self):
        self.assertHooks(['beforeSetUp', '_setup', 'afterSetUp'])

    def testTearDown(self):
        self._called = []
        self.tearDown()
        self.assertHooks(['beforeTearDown', 'beforeClose', 'afterClear'])

    def testAppOpensConnection(self):
        self.assertEqual(connections.count(), 1)
        self._app()
        self.assertEqual(connections.count(), 2)

    def testClearCallsCloseHook(self):
        self._called = []
        self._clear(1)
        self.assertHooks(['beforeClose', 'afterClear'])

    def testClearSkipsCloseHook(self):
        self._called = []
        self._clear()
        self.assertHooks(['afterClear'])

    def testClearAbortsTransaction(self):
        self.assertEqual(len(self.getObjectsInTransaction()), 0)
        self.app.foo = 1
        self.assertEqual(len(self.getObjectsInTransaction()), 1)
        self._clear()
        self.assertEqual(len(self.getObjectsInTransaction()), 0)

    def testClearClosesConnection(self):
        self.assertEqual(connections.count(), 1)
        self._clear()
        self.assertEqual(connections.count(), 0)

    def testClearClosesAllConnections(self):
        self._app()
        self.assertEqual(connections.count(), 2)
        self._clear()
        self.assertEqual(connections.count(), 0)

    def testClearLogsOut(self):
        uf = self.app.acl_users
        uf.userFolderAddUser('user_1', '', [], [])
        newSecurityManager(None, uf.getUserById('user_1').__of__(uf))
        self.assertEqual(getSecurityManager().getUser().getUserName(), 'user_1')
        self._clear()
        self.assertEqual(getSecurityManager().getUser().getUserName(), 'Anonymous User')

    def testCloseAbortsTransaction(self):
        self.assertEqual(len(self.getObjectsInTransaction()), 0)
        self.app.foo = 1
        self.assertEqual(len(self.getObjectsInTransaction()), 1)
        self._close()
        self.assertEqual(len(self.getObjectsInTransaction()), 0)

    def testCloseClosesConnection(self):
        self.assertEqual(connections.count(), 1)
        self._close()
        self.assertEqual(connections.count(), 0)

    def testCloseClosesAllConnections(self):
        self._app()
        self.assertEqual(connections.count(), 2)
        self._close()
        self.assertEqual(connections.count(), 0)

    def testLogoutLogsOut(self):
        uf = self.app.acl_users
        uf.userFolderAddUser('user_1', '', [], [])
        newSecurityManager(None, uf.getUserById('user_1').__of__(uf))
        self.assertEqual(getSecurityManager().getUser().getUserName(), 'user_1')
        self.logout()
        self.assertEqual(getSecurityManager().getUser().getUserName(), 'Anonymous User')

    def getObjectsInTransaction(self):
        # Lets us spy into the transaction
        t = transaction.get()
        if hasattr(t, '_objects'):      # Zope < 2.8
            return t._objects
        elif hasattr(t, '_resources'):  # Zope >= 2.8
            return t._resources
        else:
            raise Exception, 'Unknown version'


class TestSetUpRaises(HookTest):

    class Error: pass

    def setUp(self):
        try:
            HookTest.setUp(self)
        except self.Error:
            self.assertHooks(['beforeSetUp', '_setup', 'afterClear'])
            # Connection has been closed
            self.assertEqual(connections.count(), 0)

    def _setup(self):
        HookTest._setup(self)
        raise self.Error

    def testTrigger(self):
        pass


class TestTearDownRaises(HookTest):

    class Error: pass

    def tearDown(self):
        self._called = []
        try:
            HookTest.tearDown(self)
        except self.Error:
            self.assertHooks(['beforeTearDown', 'beforeClose', 'afterClear'])
            # Connection has been closed
            self.assertEqual(connections.count(), 0)

    def beforeClose(self):
        HookTest.beforeClose(self)
        raise self.Error

    def testTrigger(self):
        pass


class TestConnectionRegistry(base.TestCase):

    class Conn:
        closed = 0
        def close(self):
            self.closed = 1

    def afterSetUp(self):
        self.reg = connections.ConnectionRegistry()
        self.conns = [self.Conn(), self.Conn(), self.Conn()]

    def testRegister(self):
        # Should be able to register connections
        for conn in self.conns:
            self.reg.register(conn)
        assert len(self.reg) == 3
        assert self.reg.count() == 3

    def testCloseConnection(self):
        # Should be able to close a single registered connection
        for conn in self.conns:
            self.reg.register(conn)
        assert len(self.reg) == 3
        self.reg.close(self.conns[0])
        assert len(self.reg) == 2
        assert self.conns[0].closed == 1
        assert self.conns[1].closed == 0
        assert self.conns[2].closed == 0

    def testCloseSeveralConnections(self):
        # Should be able to close all registered connections one-by-one
        for conn in self.conns:
            self.reg.register(conn)
        assert len(self.reg) == 3
        self.reg.close(self.conns[0])
        assert len(self.reg) == 2
        assert self.conns[0].closed == 1
        assert self.conns[1].closed == 0
        assert self.conns[2].closed == 0
        self.reg.close(self.conns[2])
        assert len(self.reg) == 1
        assert self.conns[0].closed == 1
        assert self.conns[1].closed == 0
        assert self.conns[2].closed == 1
        self.reg.close(self.conns[1])
        assert len(self.reg) == 0
        assert self.conns[0].closed == 1
        assert self.conns[1].closed == 1
        assert self.conns[2].closed == 1

    def testCloseForeignConnection(self):
        # Should be able to close a connection that has not been registered
        for conn in self.conns:
            self.reg.register(conn)
        assert len(self.reg) == 3
        conn = self.Conn()
        self.reg.close(conn)
        assert len(self.reg) == 3
        assert self.conns[0].closed == 0
        assert self.conns[1].closed == 0
        assert self.conns[2].closed == 0
        assert conn.closed == 1

    def testCloseAllConnections(self):
        # Should be able to close all registered connections at once
        for conn in self.conns:
            self.reg.register(conn)
        assert len(self.reg) == 3
        self.reg.closeAll()
        assert len(self.reg) == 0
        assert self.conns[0].closed == 1
        assert self.conns[1].closed == 1
        assert self.conns[2].closed == 1

    def testContains(self):
        # Should be able to check if a connection is registered
        for conn in self.conns:
            self.reg.register(conn)
        assert len(self.reg) == 3
        assert self.reg.contains(self.conns[0])
        assert self.reg.contains(self.conns[1])
        assert self.reg.contains(self.conns[2])


class TestListConverter(base.TestCase):

    def testList0(self):
        self.assertEqual(utils.makelist([]), [])

    def testList1(self):
        self.assertEqual(utils.makelist(['foo']), ['foo'])

    def testList2(self):
        self.assertEqual(utils.makelist(['foo', 'bar']), ['foo', 'bar'])

    def testTuple0(self):
        self.assertEqual(utils.makelist(()), [])

    def testTuple1(self):
        self.assertEqual(utils.makelist(('foo',)), ['foo'])

    def testTuple2(self):
        self.assertEqual(utils.makelist(('foo', 'bar')), ['foo', 'bar'])

    def testString0(self):
        self.assertEqual(utils.makelist(''), [])

    def testString1(self):
        self.assertEqual(utils.makelist('foo'), ['foo'])

    def testString2(self):
        self.assertEqual(utils.makelist('foo, bar'), ['foo, bar'])

    def testInteger(self):
        self.assertRaises(ValueError, utils.makelist, 0)

    def testObject(self):
        class dummy: pass
        self.assertRaises(ValueError, utils.makelist, dummy())


class TestRequestVariables(base.TestCase):
    '''Makes sure the REQUEST contains required variables'''

    def testRequestVariables(self):
        request = self.app.REQUEST
        self.failIfEqual(request.get('SERVER_NAME', ''), '')
        self.failIfEqual(request.get('SERVER_PORT', ''), '')
        self.failIfEqual(request.get('REQUEST_METHOD', ''), '')
        self.failIfEqual(request.get('URL', ''), '')
        self.failIfEqual(request.get('SERVER_URL', ''), '')
        self.failIfEqual(request.get('URL0', ''), '')
        self.failIfEqual(request.get('URL1', ''), '')
        self.failIfEqual(request.get('BASE0', ''), '')
        self.failIfEqual(request.get('BASE1', ''), '')
        self.failIfEqual(request.get('BASE2', ''), '')


import gc
_sentinel1 = []

class TestRequestGarbage1(base.TestCase):
    '''Make sure we do not leak REQUEST._held (and REQUEST.other)'''

    class Held:
        def __del__(self):
            _sentinel1.append('__del__')

    def afterSetUp(self):
        self.anApp = base.app()
        self.anApp.REQUEST._hold(self.Held())

    def testBaseCloseClosesRequest(self):
        base.close(self.anApp)
        gc.collect()
        self.assertEqual(_sentinel1, ['__del__'])


_sentinel2 = []

class TestRequestGarbage2(base.TestCase):
    '''Make sure we do not leak REQUEST._held (and REQUEST.other)'''

    class Held:
        def __del__(self):
            _sentinel2.append('__del__')

    def afterSetUp(self):
        self.app.REQUEST._hold(self.Held())

    def testClearClosesRequest(self):
        self._clear()
        gc.collect()
        self.assertEqual(_sentinel2, ['__del__'])


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestTestCase))
    suite.addTest(makeSuite(TestSetUpRaises))
    suite.addTest(makeSuite(TestTearDownRaises))
    suite.addTest(makeSuite(TestConnectionRegistry))
    suite.addTest(makeSuite(TestListConverter))
    suite.addTest(makeSuite(TestRequestVariables))
    suite.addTest(makeSuite(TestRequestGarbage1))
    suite.addTest(makeSuite(TestRequestGarbage2))
    return suite

if __name__ == '__main__':
    framework()

