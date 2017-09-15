##############################################################################
#
# Copyright (c) 2001, 2002 Zope Foundation and Contributors.
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

import os
import shutil
import tempfile
import unittest

from App.config import getConfiguration, setConfiguration
from OFS.Application import Application, AppInitializer
from Zope2.Startup.options import ZopeWSGIOptions

TEMPNAME = tempfile.mktemp()
TEMPPRODUCTS = os.path.join(TEMPNAME, "Products")

good_cfg = """
instancehome <<INSTANCE_HOME>>

<zodb_db main>
   mount-point /
   <mappingstorage>
      name mappingstorage
   </mappingstorage>
</zodb_db>
"""

original_config = None


def getApp():
    from App.ZApplication import ZApplicationWrapper
    DB = getConfiguration().dbtab.getDatabase('/')
    return ZApplicationWrapper(DB, 'Application', Application)()


class TestInitialization(unittest.TestCase):
    """ Test the application initializer object """

    def setUp(self):
        global original_config
        if original_config is None:
            original_config = getConfiguration()
        os.makedirs(TEMPNAME)
        os.makedirs(TEMPPRODUCTS)

    def tearDown(self):
        import App.config
        App.config.setConfiguration(original_config)
        shutil.rmtree(TEMPNAME)
        import Products
        Products.__path__ = [d for d in Products.__path__
                             if os.path.exists(d)]

    def configure(self, text):
        # We have to create a directory of our own since the existence
        # of the directory is checked.  This handles this in a
        # platform-independent way.
        config_path = os.path.join(TEMPNAME, 'zope.conf')
        with open(config_path, 'w') as fd:
            fd.write(text.replace(u"<<INSTANCE_HOME>>", TEMPNAME))

        options = ZopeWSGIOptions(config_path)()
        config = options.configroot
        self.assertEqual(config.instancehome, TEMPNAME)
        setConfiguration(config)

    def getOne(self):
        app = getApp()
        return AppInitializer(app)

    def test_install_required_roles(self):
        self.configure(good_cfg)
        i = self.getOne()
        i.install_required_roles()
        app = i.getApp()
        self.assertTrue('Owner' in app.__ac_roles__)
        self.assertTrue('Authenticated' in app.__ac_roles__)

    def test_install_inituser(self):
        fname = os.path.join(TEMPNAME, 'inituser')
        f = open(fname, 'w')
        f.write('theuser:password')
        f.close()
        try:
            self.configure(good_cfg)
            i = self.getOne()
            i.install_inituser()
            app = i.getApp()
            self.assertTrue(app.acl_users.getUser('theuser'))
        finally:
            if os.path.exists(fname):
                os.unlink(fname)

    def test_install_products(self):
        self.configure(good_cfg)
        i = self.getOne()
        i.install_products()
        self.assertTrue('__roles__' in Application.misc_.__dict__)
