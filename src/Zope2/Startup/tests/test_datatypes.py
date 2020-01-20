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
from Zope2.Startup.options import ZopeWSGIOptions


_SCHEMA = None


def getSchema():
    global _SCHEMA
    if _SCHEMA is None:
        opts = ZopeWSGIOptions()
        opts.load_schema()
        _SCHEMA = opts.schema
    return _SCHEMA


class ZopeDatabaseTestCase(unittest.TestCase):

    def setUp(self):
        self.TEMPNAME = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.TEMPNAME)

    def load_config_text(self, text):
        # We have to create a directory of our own since the existence
        # of the directory is checked.  This handles this in a
        # platform-independent way.
        text = text.replace("<<INSTANCE_HOME>>", self.TEMPNAME)
        sio = io.StringIO(text)

        conf, self.handler = ZConfig.loadConfigFile(getSchema(), sio)
        self.assertEqual(conf.instancehome, self.TEMPNAME)
        return conf

    def test_parse_mount_points_as_native_strings(self):
        conf = self.load_config_text("""
            instancehome <<INSTANCE_HOME>>
            <zodb_db main>
               mount-point /test
               <mappingstorage>
                  name mappingstorage
               </mappingstorage>
            </zodb_db>
            """)
        db = conf.databases[0]
        self.assertEqual('main', db.name)
        virtual_path = db.getVirtualMountPaths()[0]
        self.assertEqual('/test', virtual_path)
        self.assertIsInstance(virtual_path, str)
        self.assertEqual([('/test', None, '/test')], db.computeMountPaths())
