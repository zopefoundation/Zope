##############################################################################
#
# Copyright (c) 2010 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################

import logging
import unittest

from Testing.ZopeTestCase import ZopeTestCase
from zope.testing.loggingsupport import InstalledHandler


logged = """Zope2.App.test_startup INFO
  <class 'zope.processlifetime.DatabaseOpened'>
Zope2.App.test_startup INFO
  <class 'ZODB.DB.DB'>
Zope2.App.test_startup INFO
  Root not ready.
Zope2.App.test_startup INFO
  <class 'zope.processlifetime.DatabaseOpenedWithRoot'>
Zope2.App.test_startup INFO
  <class 'ZODB.DB.DB'>
Zope2.App.test_startup INFO
  <class 'OFS.Application.Application'>"""


def logevent(event):
    logger = logging.getLogger('Zope2.App.test_startup')
    logger.info(event.__class__)
    db = event.database
    logger.info(db.__class__)
    conn = db.open()
    try:
        try:
            root = conn.root()
            app = root['Application']
            logger.info(app.__class__)
        except KeyError:
            logger.info('Root not ready.')
    finally:
        conn.close()


class StartupTests(ZopeTestCase):

    def test_database_events(self):
        from Zope2.App.startup import startup
        from zope.component import provideHandler
        from zope.processlifetime import IDatabaseOpened
        from zope.processlifetime import IDatabaseOpenedWithRoot

        handler = InstalledHandler('Zope2.App.test_startup')
        provideHandler(logevent, [IDatabaseOpenedWithRoot])
        provideHandler(logevent, [IDatabaseOpened])
        startup()
        self.assertEqual(str(handler), logged)

    def test_interface(self):
        # We don't want Interface methods to be publishable.
        # So they should not have a docstring.
        # This is done in Zope2.App.patches.publishing.
        from zope.interface import Interface
        self.assertFalse(Interface.names.__doc__)
        self.assertFalse(Interface.getTaggedValue.__doc__)
        self.assertFalse(Interface.setTaggedValue.__doc__)


class FreezeSecurityDeclarationsTests(unittest.TestCase):

    def setUp(self):
        try:
            from AccessControl import frozen
        except ImportError:
            self.skipTest('AccessControl cannot freeze security declarations')
        self.frozen = frozen
        self._orig_frozen = frozen._frozen
        frozen._frozen = False

    def tearDown(self):
        self.frozen._frozen = self._orig_frozen

    def test_freeze_on_process_starting(self):
        from AccessControl import allow_module
        from zExceptions import Forbidden
        from Zope2.App.startup import freeze_security_declarations
        from zope.component import getGlobalSiteManager
        from zope.event import notify
        from zope.processlifetime import IProcessStarting
        from zope.processlifetime import ProcessStarting

        gsm = getGlobalSiteManager()
        gsm.registerHandler(freeze_security_declarations, [IProcessStarting])
        self.addCleanup(gsm.unregisterHandler, freeze_security_declarations,
                        [IProcessStarting])
        self.assertFalse(self.frozen.is_frozen())
        notify(ProcessStarting())
        self.assertTrue(self.frozen.is_frozen())
        with self.assertRaises(Forbidden):
            allow_module('Zope2.App.tests.nonesuch')


def test_suite():
    loader = unittest.defaultTestLoader
    return unittest.TestSuite((
        loader.loadTestsFromTestCase(StartupTests),
        loader.loadTestsFromTestCase(FreezeSecurityDeclarationsTests),
    ))
