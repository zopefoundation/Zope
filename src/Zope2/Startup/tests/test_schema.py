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
import Zope2.Startup
import Products

from Zope2.Startup import datatypes

from App.config import getConfiguration


TEMPNAME = tempfile.mktemp()
TEMPPRODUCTS = os.path.join(TEMPNAME, "Products")
TEMPVAR = os.path.join(TEMPNAME, "var")

def getSchema():
    startup = os.path.dirname(os.path.realpath(Zope2.Startup.__file__))
    schemafile = os.path.join(startup, 'zopeschema.xml')
    return ZConfig.loadSchema(schemafile)

class StartupTestCase(unittest.TestCase):

    schema = None

    def setUp(self):
        if self.schema is None:
            StartupTestCase.schema = getSchema()

    def tearDown(self):
        Products.__path__ = [d for d in Products.__path__
                             if os.path.exists(d)]

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

    def test_load_config_template(self):
        schema = self.schema
        cfg = getConfiguration()
        import Zope2.utilities
        base = os.path.dirname(Zope2.utilities.__file__)
        fn = os.path.join(base, "skel", "etc", "zope.conf.in")
        f = open(fn)
        text = f.read()
        f.close()
        self.load_config_text(text)

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
        self.assertEqual(items, [("FEARFACTORY", "rocks"), ("NSYNC","doesnt")])

    def test_ms_author_via(self):
        import webdav
        from Zope2.Startup.handlers import handleConfig

        default_setting = webdav.enable_ms_author_via
        try:
            conf, handler = self.load_config_text("""\
                instancehome <<INSTANCE_HOME>>
                enable-ms-author-via true
                """)
            handleConfig(None, handler)
            self.assert_(webdav.enable_ms_author_via == True)

            conf, handler = self.load_config_text("""\
                instancehome <<INSTANCE_HOME>>
                enable-ms-author-via false
                """)
            handleConfig(None, handler)
            self.assert_(webdav.enable_ms_author_via == False)
        finally:
            webdav.enable_ms_author_via = default_setting

    def test_ms_public_header(self):
        import webdav
        from Zope2.Startup.handlers import handleConfig

        default_setting = webdav.enable_ms_public_header
        try:
            conf, handler = self.load_config_text("""\
                instancehome <<INSTANCE_HOME>>
                enable-ms-public-header true
                """)
            handleConfig(None, handler)
            self.assert_(webdav.enable_ms_public_header == True)

            conf, handler = self.load_config_text("""\
                instancehome <<INSTANCE_HOME>>
                enable-ms-public-header false
                """)
            handleConfig(None, handler)
            self.assert_(webdav.enable_ms_public_header == False)
        finally:
            webdav.enable_ms_public_header = default_setting

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

    def test_dns_resolver(self):
        from ZServer.medusa import resolver
        conf, handler = self.load_config_text("""\
            instancehome <<INSTANCE_HOME>>
            dns-server localhost
            """)
        self.assert_(isinstance(conf.dns_resolver, resolver.caching_resolver))

    def test_zodb_db(self):
        conf, handler = self.load_config_text("""\
            instancehome <<INSTANCE_HOME>>
            <zodb_db main>
              <filestorage>
               path <<INSTANCE_HOME>>/var/Data.fs
               </filestorage>
                connection-class  Products.TemporaryFolder.LowConflictConnection.LowConflictConnection
                mount-point                    /
                cache-size                     5000
                pool-size                      7
            </zodb_db>
            """)
        self.assertEqual(conf.databases[0].config.connection_class.__name__,
                         'LowConflictConnection')

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

def test_suite():
    return unittest.makeSuite(StartupTestCase)
