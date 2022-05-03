##############################################################################
#
# Copyright (c) 2005 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""TestCase for Zope testing
"""

import unittest

import transaction
from AccessControl.SecurityManagement import noSecurityManager
from Testing.makerequest import makerequest
from Testing.ZopeTestCase import ZopeLite as Zope2
from Testing.ZopeTestCase import connections
from Testing.ZopeTestCase import interfaces
from Testing.ZopeTestCase import layer
from zope.interface import implementer


def app():
    '''Opens a ZODB connection and returns the app object.'''
    app = Zope2.app()
    app = makerequest(app)
    connections.register(app)
    return app


def close(app):
    '''Closes the app's ZODB connection.'''
    connections.close(app)


@implementer(interfaces.IZopeTestCase)
class TestCase(unittest.TestCase):
    '''Base test case for Zope testing
    '''

    layer = layer.ZopeLite

    def afterSetUp(self):
        '''Called after setUp() has completed. This is
           far and away the most useful hook.
        '''
        pass

    def beforeTearDown(self):
        '''Called before tearDown() is executed.
           Note that tearDown() is not called if
           setUp() fails.
        '''
        pass

    def afterClear(self):
        '''Called after the fixture has been cleared.
           Note that this may occur during setUp() *and*
           tearDown().
        '''
        pass

    def beforeSetUp(self):
        '''Called before the ZODB connection is opened,
           at the start of setUp(). By default begins
           a new transaction.
        '''
        transaction.begin()

    def beforeClose(self):
        '''Called before the ZODB connection is closed,
           at the end of tearDown(). By default aborts
           the transaction.
        '''
        transaction.abort()

    def setUp(self):
        '''Sets up the fixture. Do not override,
           use the hooks instead.
        '''
        try:
            self.beforeSetUp()
            self.app = self._app()
            self._setup()
            self.afterSetUp()
        except Exception:
            self._clear()
            raise

    def tearDown(self):
        '''Tears down the fixture. Do not override,
           use the hooks instead.
        '''
        try:
            self.beforeTearDown()
            self._clear(1)
        except Exception:
            self._clear()
            raise

    def _app(self):
        '''Returns the app object for a test.'''
        return app()

    def _setup(self):
        '''Sets up the fixture. Framework authors may
           override.
        '''
        pass

    def _clear(self, call_close_hook=0):
        '''Clears the fixture.'''
        if call_close_hook:
            self.beforeClose()
        self._close()
        self.logout()
        self.afterClear()

    def _close(self):
        '''Closes the ZODB connection.'''
        transaction.abort()
        connections.closeAll()

    def logout(self):
        '''Logs out.'''
        noSecurityManager()
