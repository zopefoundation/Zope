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


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(StartupTests))
    return suite
