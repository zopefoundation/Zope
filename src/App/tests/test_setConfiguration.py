##############################################################################
#
# Copyright (c) 2004 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Tests for App.config.setConfiguration()
"""
import unittest

import Testing
#import Zope2
#Zope2.startup()

from Testing.ZopeTestCase.layer import ZopeLite


class SetConfigTests(unittest.TestCase):

    layer = ZopeLite

    def setUp(self):
        # Save away everything as we need to restore it later on
        self.clienthome = self.getconfig('clienthome')
        self.instancehome = self.getconfig('instancehome') 
        self.softwarehome = self.getconfig('softwarehome')
        self.zopehome = self.getconfig('zopehome')
        self.debug_mode = self.getconfig('debug_mode')

    def tearDown(self):
        self.setconfig(clienthome=self.clienthome,
                       instancehome=self.instancehome,
                       softwarehome=self.softwarehome,
                       zopehome=self.zopehome,
                       debug_mode=self.debug_mode)

    def getconfig(self, key):
        import App.config
        config = App.config.getConfiguration()
        return getattr(config, key, None)

    def setconfig(self, **kw):
        import App.config
        config = App.config.getConfiguration()
        for key, value in kw.items():
            setattr(config, key, value)
        App.config.setConfiguration(config)

    def testClientHomeLegacySources(self):
        import os
        import App.FindHomes
        import Globals  # for data
        import __builtin__
        self.setconfig(clienthome='foo')
        self.assertEqual(os.environ.get('CLIENT_HOME'), 'foo')
        self.assertEqual(App.FindHomes.CLIENT_HOME, 'foo')
        self.assertEqual(__builtin__.CLIENT_HOME, 'foo')
        self.assertEqual(Globals.data_dir, 'foo')

    def testInstanceHomeLegacySources(self):
        import os
        import App.FindHomes
        import Globals  # for data
        import __builtin__
        self.setconfig(instancehome='foo')
        self.assertEqual(os.environ.get('INSTANCE_HOME'), 'foo')
        self.assertEqual(App.FindHomes.INSTANCE_HOME, 'foo')
        self.assertEqual(__builtin__.INSTANCE_HOME, 'foo')
        self.assertEqual(Globals.INSTANCE_HOME, 'foo')

    def testSoftwareHomeLegacySources(self):
        import os
        import App.FindHomes
        import Globals  # for data
        import __builtin__
        self.setconfig(softwarehome='foo')
        self.assertEqual(os.environ.get('SOFTWARE_HOME'), 'foo')
        self.assertEqual(App.FindHomes.SOFTWARE_HOME, 'foo')
        self.assertEqual(__builtin__.SOFTWARE_HOME, 'foo')
        self.assertEqual(Globals.SOFTWARE_HOME, 'foo')

    def testZopeHomeLegacySources(self):
        import os
        import App.FindHomes
        import Globals  # for data
        import __builtin__
        self.setconfig(zopehome='foo')
        self.assertEqual(os.environ.get('ZOPE_HOME'), 'foo')
        self.assertEqual(App.FindHomes.ZOPE_HOME, 'foo')
        self.assertEqual(__builtin__.ZOPE_HOME, 'foo')
        self.assertEqual(Globals.ZOPE_HOME, 'foo')

    def testDebugModeLegacySources(self):
        import Globals  # for data
        self.setconfig(debug_mode=True)
        self.assertEqual(Globals.DevelopmentMode, True)
        self.setconfig(debug_mode=False)
        self.assertEqual(Globals.DevelopmentMode, False)


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(SetConfigTests))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
