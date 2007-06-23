##############################################################################
#
# Copyright (c) 2003 Zope Corporation and Contributors.
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

from Zope2.Startup import datatypes

from App.config import getConfiguration


TEMPNAME = tempfile.mktemp()
TEMPPRODUCTS = os.path.join(TEMPNAME, "Products")

def getSchema():
    startup = os.path.dirname(os.path.realpath(Zope2.Startup.__file__))
    schemafile = os.path.join(startup, 'zopeschema.xml')
    return ZConfig.loadSchema(schemafile)

class StartupTestCase(unittest.TestCase):

    schema = None

    def setUp(self):
        if self.schema is None:
            StartupTestCase.schema = getSchema()

    def load_config_text(self, text):
        # We have to create a directory of our own since the existence
        # of the directory is checked.  This handles this in a
        # platform-independent way.
        schema = self.schema
        sio = cStringIO.StringIO(
            text.replace("<<INSTANCE_HOME>>", TEMPNAME))
        os.mkdir(TEMPNAME)
        os.mkdir(TEMPPRODUCTS)
        try:
            conf, handler = ZConfig.loadConfigFile(schema, sio)
        finally:
            os.rmdir(TEMPPRODUCTS)
            os.rmdir(TEMPNAME)
        self.assertEqual(conf.instancehome, TEMPNAME)
        return conf, handler

    def test_load_config_template(self):
        schema = self.schema
        cfg = getConfiguration()
        fn = os.path.join(cfg.zopehome, "skel", "etc", "zope.conf.in")
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
                version-pool-size              3
                version-cache-size             100
            </zodb_db>
            """)
        self.assertEqual(conf.databases[0].config.connection_class.__name__,
                         'LowConflictConnection')

def test_suite():
    return unittest.makeSuite(StartupTestCase)

if __name__ == "__main__":
    unittest.main(defaultTest="test_suite")
