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

from Testing.ZopeTestCase.layer import ZopeLite


class SetConfigTests(unittest.TestCase):

    layer = ZopeLite

    def setUp(self):
        # Save away everything as we need to restore it later on
        self.clienthome = self.getconfig('clienthome')
        self.instancehome = self.getconfig('instancehome') 
        self.debug_mode = self.getconfig('debug_mode')

    def tearDown(self):
        self.setconfig(clienthome=self.clienthome,
                       instancehome=self.instancehome,
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
