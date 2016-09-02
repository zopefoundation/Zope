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
        self.setconfig(clienthome='foo')
        self.assertEqual(self.getconfig('clienthome'), 'foo')
        self.assertEqual(os.environ.get('CLIENT_HOME'), 'foo')

    def testInstanceHomeLegacySources(self):
        import os
        self.setconfig(instancehome='foo')
        self.assertEqual(self.getconfig('instancehome'), 'foo')
        self.assertEqual(os.environ.get('INSTANCE_HOME'), 'foo')
