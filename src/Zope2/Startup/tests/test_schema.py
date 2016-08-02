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
"""Test that the Zope schema can be loaded."""

import os
import cStringIO
import tempfile
import unittest

import ZConfig

import Products
from Zope2.Startup import datatypes
from Zope2.Startup.options import ZopeOptions

_SCHEMA = {}
TEMPNAME = tempfile.mktemp()
TEMPPRODUCTS = os.path.join(TEMPNAME, "Products")
TEMPVAR = os.path.join(TEMPNAME, "var")


def getSchema(schemafile):
    global _SCHEMA
    if schemafile not in _SCHEMA:
        opts = ZopeOptions()
        opts.schemafile = schemafile
        opts.load_schema()
        _SCHEMA[schemafile] = opts.schema
    return _SCHEMA[schemafile]


class WSGIStartupTestCase(unittest.TestCase):

    @property
    def schema(self):
        return getSchema('wsgischema.xml')

    def load_config_text(self, text):
        # We have to create a directory of our own since the existence
        # of the directory is checked.  This handles this in a
        # platform-independent way.
        schema = self.schema
        sio = cStringIO.StringIO(
            text.replace("<<INSTANCE_HOME>>", TEMPNAME))
        os.mkdir(TEMPNAME)
        os.mkdir(TEMPVAR)
        try:
            conf, handler = ZConfig.loadConfigFile(schema, sio)
        finally:
            os.rmdir(TEMPVAR)
            os.rmdir(TEMPNAME)
        self.assertEqual(conf.instancehome, TEMPNAME)
        return conf, handler

    def test_load_config_template(self):
        import Zope2.utilities
        base = os.path.dirname(Zope2.utilities.__file__)
        fn = os.path.join(base, "skel", "etc", "base.conf.in")
        f = open(fn)
        text = f.read()
        f.close()
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
        items = conf.environment.items()
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
                mount-point                    /
                cache-size                     5000
                pool-size                      7
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


class ZServerStartupTestCase(unittest.TestCase):

    def tearDown(self):
        Products.__path__ = [d for d in Products.__path__
                             if os.path.exists(d)]

    @property
    def schema(self):
        return getSchema('zopeschema.xml')

    def load_config_text(self, text):
        # We have to create a directory of our own since the existence
        # of the directory is checked.  This handles this in a
        # platform-independent way.
        schema = self.schema
        sio = cStringIO.StringIO(
            text.replace("<<INSTANCE_HOME>>", TEMPNAME))
        os.mkdir(TEMPNAME)
        os.mkdir(TEMPPRODUCTS)
        os.mkdir(TEMPVAR)
        try:
            conf, handler = ZConfig.loadConfigFile(schema, sio)
        finally:
            os.rmdir(TEMPPRODUCTS)
            os.rmdir(TEMPVAR)
            os.rmdir(TEMPNAME)
        self.assertEqual(conf.instancehome, TEMPNAME)
        return conf, handler

    def test_cgi_environment(self):
        conf, handler = self.load_config_text("""\
            # instancehome is here since it's required
            instancehome <<INSTANCE_HOME>>
            <cgi-environment>
              HEADER value
              ANOTHER value2
            </cgi-environment>
            """)
        items = conf.cgi_environment.items()
        items.sort()
        self.assertEqual(items, [("ANOTHER", "value2"), ("HEADER", "value")])

    def test_ms_public_header(self):
        from Zope2.Startup import config
        from Zope2.Startup.handlers import handleConfig

        default_setting = config.ZSERVER_ENABLE_MS_PUBLIC_HEADER
        try:
            conf, handler = self.load_config_text("""\
                instancehome <<INSTANCE_HOME>>
                enable-ms-public-header true
                """)
            handleConfig(None, handler)
            self.assertTrue(config.ZSERVER_ENABLE_MS_PUBLIC_HEADER)

            conf, handler = self.load_config_text("""\
                instancehome <<INSTANCE_HOME>>
                enable-ms-public-header false
                """)
            handleConfig(None, handler)
            self.assertFalse(config.ZSERVER_ENABLE_MS_PUBLIC_HEADER)
        finally:
            config.ZSERVER_ENABLE_MS_PUBLIC_HEADER = default_setting

    def test_path(self):
        p1 = tempfile.mktemp()
        p2 = tempfile.mktemp()
        try:
            os.mkdir(p1)
            os.mkdir(p2)
            conf, handler = self.load_config_text("""\
                # instancehome is here since it's required
                instancehome <<INSTANCE_HOME>>
                path %s
                path %s
                """ % (p1, p2))
            items = conf.path
            self.assertEqual(items, [p1, p2])
        finally:
            if os.path.exists(p1):
                os.rmdir(p1)
            if os.path.exists(p2):
                os.rmdir(p2)

    def test_access_and_trace_logs(self):
        fn = tempfile.mktemp()
        conf, handler = self.load_config_text("""
            instancehome <<INSTANCE_HOME>>
            <logger access>
              <logfile>
                path %s
              </logfile>
            </logger>
            """ % fn)
        self.assert_(isinstance(conf.access, datatypes.LoggerFactory))
        self.assertEqual(conf.access.name, "access")
        self.assertEqual(conf.access.handler_factories[0].section.path, fn)
        self.assert_(conf.trace is None)
