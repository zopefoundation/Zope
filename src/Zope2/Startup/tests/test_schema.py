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

import codecs
import io
import os
import shutil
import tempfile
import unittest

import ZConfig
import Zope2.Startup.datatypes
import ZPublisher.HTTPRequest
from Zope2.Startup.handlers import handleWSGIConfig
from Zope2.Startup.options import ZopeWSGIOptions


_SCHEMA = None


def getSchema():
    global _SCHEMA
    if _SCHEMA is None:
        opts = ZopeWSGIOptions()
        opts.load_schema()
        _SCHEMA = opts.schema
    return _SCHEMA


class WSGIStartupTestCase(unittest.TestCase):

    def setUp(self):
        self.default_encoding = ZPublisher.HTTPRequest.default_encoding
        self.TEMPNAME = tempfile.mkdtemp()
        self.TEMPVAR = os.path.join(self.TEMPNAME, "var")
        os.mkdir(self.TEMPVAR)

    def tearDown(self):
        shutil.rmtree(self.TEMPNAME)
        Zope2.Startup.datatypes.default_zpublisher_encoding(
            self.default_encoding)

    def load_config_text(self, text):
        # We have to create a directory of our own since the existence
        # of the directory is checked.  This handles this in a
        # platform-independent way.
        text = text.replace("<<INSTANCE_HOME>>", self.TEMPNAME)
        sio = io.StringIO(text)
        conf, handler = ZConfig.loadConfigFile(getSchema(), sio)
        self.assertEqual(conf.instancehome, self.TEMPNAME)
        return conf, handler

    def test_load_config_template(self):
        import Zope2.utilities
        base = os.path.dirname(Zope2.utilities.__file__)
        fn = os.path.join(base, "skel", "etc", "zope.conf.in")
        with codecs.open(fn, encoding='utf-8') as f:
            text = f.read()
        self.load_config_text(text)

    def test_environment(self):
        conf, handler = self.load_config_text("""\
            # instancehome is here since it's required
            instancehome <<INSTANCE_HOME>>
            <environment>
              FEARFACTORY rocks
              NSYNC doesnt
            </environment>
            """)
        items = list(conf.environment.items())
        items.sort()
        self.assertEqual(
            items, [("FEARFACTORY", "rocks"), ("NSYNC", "doesnt")])

    def test_zodb_db(self):
        conf, handler = self.load_config_text("""\
            instancehome <<INSTANCE_HOME>>
            <zodb_db main>
              <filestorage>
               path <<INSTANCE_HOME>>/var/Data.fs
               </filestorage>
                mount-point /
                cache-size 5000
                pool-size 7
            </zodb_db>
            """)
        self.assertEqual(conf.databases[0].config.cache_size, 5000)

    def test_max_conflict_retries_default(self):
        conf, handler = self.load_config_text("""\
            instancehome <<INSTANCE_HOME>>
            """)
        self.assertEqual(conf.max_conflict_retries, 3)

    def test_max_conflict_retries_explicit(self):
        conf, handler = self.load_config_text("""\
            instancehome <<INSTANCE_HOME>>
            max-conflict-retries 15
            """)
        self.assertEqual(conf.max_conflict_retries, 15)

    def test_default_zpublisher_encoding(self):
        conf, dummy = self.load_config_text("""\
            instancehome <<INSTANCE_HOME>>
            """)
        self.assertEqual(conf.default_zpublisher_encoding, 'utf-8')

        conf, dummy = self.load_config_text("""\
            instancehome <<INSTANCE_HOME>>
            default-zpublisher-encoding iso-8859-15
            """)
        self.assertEqual(conf.default_zpublisher_encoding, 'iso-8859-15')
        self.assertEqual(
            ZPublisher.HTTPRequest.default_encoding, 'iso-8859-15')
        self.assertEqual(type(ZPublisher.HTTPRequest.default_encoding), str)

    def test_pid_filename(self):
        conf, dummy = self.load_config_text("""\
            instancehome <<INSTANCE_HOME>>
            """)
        default = os.path.join(conf.clienthome, 'Z4.pid')
        self.assertEqual(conf.pid_filename, default)

        conf, dummy = self.load_config_text("""\
            instancehome <<INSTANCE_HOME>>
            pid-filename <<INSTANCE_HOME>>{sep}Z5.pid
            """.format(sep=os.path.sep))
        expected = os.path.join(conf.instancehome, 'Z5.pid')
        self.assertEqual(conf.pid_filename, expected)

    def test_automatically_quote_dtml_request_data(self):
        conf, handler = self.load_config_text("""\
            instancehome <<INSTANCE_HOME>>
            """)
        handleWSGIConfig(None, handler)
        self.assertTrue(conf.automatically_quote_dtml_request_data)
        self.assertEqual(os.environ.get('ZOPE_DTML_REQUEST_AUTOQUOTE', ''), '')

        conf, handler = self.load_config_text("""\
            instancehome <<INSTANCE_HOME>>
            automatically-quote-dtml-request-data off
            """)
        handleWSGIConfig(None, handler)
        self.assertFalse(conf.automatically_quote_dtml_request_data)
        self.assertEqual(os.environ.get('ZOPE_DTML_REQUEST_AUTOQUOTE', ''),
                         '0')

    def test_webdav_source_port(self):
        conf, handler = self.load_config_text("""\
            instancehome <<INSTANCE_HOME>>
            """)
        handleWSGIConfig(None, handler)
        self.assertEqual(conf.webdav_source_port, 0)

        conf, handler = self.load_config_text("""\
            instancehome <<INSTANCE_HOME>>
            webdav-source-port 9800
            """)
        handleWSGIConfig(None, handler)
        self.assertEqual(conf.webdav_source_port, 9800)

    def test_ms_public_header(self):
        import webdav

        default_setting = webdav.enable_ms_public_header
        try:
            conf, handler = self.load_config_text("""\
                instancehome <<INSTANCE_HOME>>
                enable-ms-public-header true
                """)
            handleWSGIConfig(None, handler)
            self.assertTrue(webdav.enable_ms_public_header)

            conf, handler = self.load_config_text("""\
                instancehome <<INSTANCE_HOME>>
                enable-ms-public-header false
                """)
            handleWSGIConfig(None, handler)
            self.assertFalse(webdav.enable_ms_public_header)
        finally:
            webdav.enable_ms_public_header = default_setting
