##############################################################################
#
# Copyright (c) 2003 Zope Foundation and Contributors.
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

import io
import shutil
import tempfile
import unittest

import ZConfig
from Zope2.Startup import get_wsgi_starter
from Zope2.Startup.options import ZopeWSGIOptions


_SCHEMA = None


def getSchema():
    global _SCHEMA
    if _SCHEMA is None:
        opts = ZopeWSGIOptions()
        opts.load_schema()
        _SCHEMA = opts.schema
    return _SCHEMA


class WSGIStarterTestCase(unittest.TestCase):

    def setUp(self):
        self.TEMPNAME = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.TEMPNAME)

    def get_starter(self, conf):
        starter = get_wsgi_starter()
        starter.setConfiguration(conf)
        return starter

    def load_config_text(self, text):
        # We have to create a directory of our own since the existence
        # of the directory is checked.  This handles this in a
        # platform-independent way.
        text = text.replace("<<INSTANCE_HOME>>", self.TEMPNAME)
        sio = io.StringIO(text)
        conf, self.handler = ZConfig.loadConfigFile(getSchema(), sio)
        self.assertEqual(conf.instancehome, self.TEMPNAME)
        return conf

    def testSetupLocale(self):
        # XXX this almost certainly won't work on all systems
        import locale
        try:
            try:
                conf = self.load_config_text("""
                    instancehome <<INSTANCE_HOME>>
                    locale en_GB""")
            except ZConfig.DataConversionError as e:
                # Skip this test if we don't have support.
                if e.message.startswith(
                        'The specified locale "en_GB" is not supported'):
                    return
                raise
            starter = self.get_starter(conf)
            starter.setupLocale()
            self.assertEqual(tuple(locale.getlocale()), ('en_GB', 'ISO8859-1'))
        finally:
            # reset to system-defined locale
            locale.setlocale(locale.LC_ALL, '')

    def testSetupConflictRetries(self):
        from Zope2.Startup.handlers import root_wsgi_handler
        from ZPublisher.HTTPRequest import HTTPRequest

        # If no value is provided, the default is 3 retries
        conf = self.load_config_text("""
            instancehome <<INSTANCE_HOME>>""")
        root_wsgi_handler(conf)
        self.assertEqual(HTTPRequest.retry_max_count, 3)

        conf = self.load_config_text("""
            instancehome <<INSTANCE_HOME>>
            max-conflict-retries 25""")
        root_wsgi_handler(conf)
        self.assertEqual(HTTPRequest.retry_max_count, 25)

    def test_webdav_source_port(self):
        from ZPublisher import WSGIPublisher

        # If no value is provided, the default is 0
        conf = self.load_config_text("""
            instancehome <<INSTANCE_HOME>>""")
        starter = self.get_starter(conf)
        starter.setupPublisher()
        self.assertEqual(WSGIPublisher._WEBDAV_SOURCE_PORT, 0)

        conf = self.load_config_text("""
            instancehome <<INSTANCE_HOME>>
            webdav-source-port 9800""")
        starter = self.get_starter(conf)
        starter.setupPublisher()
        self.assertEqual(WSGIPublisher._WEBDAV_SOURCE_PORT, 9800)

        # Cleanup
        WSGIPublisher.set_webdav_source_port(0)
