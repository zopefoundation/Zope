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

from App.config import getConfiguration
from App.config import setConfiguration
from OFS.Application import AppInitializer
from OFS.Application import Application
from Zope2.Startup.options import ZopeWSGIOptions


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
        self.TEMPNAME = tempfile.mkdtemp()
        os.mkdir(os.path.join(self.TEMPNAME, "Products"))

    def tearDown(self):
        import App.config
        App.config.setConfiguration(original_config)
        shutil.rmtree(self.TEMPNAME)
        import Products
        Products.__path__ = [d for d in Products.__path__
                             if os.path.exists(d)]

    def configure(self, text):
        # We have to create a directory of our own since the existence
        # of the directory is checked.  This handles this in a
        # platform-independent way.
        config_path = os.path.join(self.TEMPNAME, 'zope.conf')
        with open(config_path, 'w') as fd:
            fd.write(text.replace("<<INSTANCE_HOME>>", self.TEMPNAME))

        options = ZopeWSGIOptions(config_path)()
        config = options.configroot
        self.assertEqual(config.instancehome, self.TEMPNAME)
        setConfiguration(config)

    def getOne(self):
        app = getApp()
        return AppInitializer(app)

    def test_install_virtual_hosting(self):
        self.configure(good_cfg)
        i = self.getOne()
        i.install_virtual_hosting()
        app = i.getApp()
        self.assertTrue('virtual_hosting' in app)
        self.assertEqual(
            app.virtual_hosting.meta_type, 'Virtual Host Monster')

    def test_install_required_roles(self):
        self.configure(good_cfg)
        i = self.getOne()
        i.install_required_roles()
        app = i.getApp()
        self.assertTrue('Owner' in app.__ac_roles__)
        self.assertTrue('Authenticated' in app.__ac_roles__)

    def test_install_inituser(self):
        fname = os.path.join(self.TEMPNAME, 'inituser')
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
        self.assertTrue(hasattr(Application.misc_, '__roles__'))

    def test_install_root_view(self):
        self.configure(good_cfg)
        i = self.getOne()
        i.install_root_view()
        app = i.getApp()
        self.assertTrue('index_html' in app)
        self.assertEqual(app.index_html.meta_type, 'Page Template')

    def test_install_products_which_need_the_application(self):
        self.configure(good_cfg)
        from Zope2.App import zcml
        configure_zcml = '''
        <configure
         xmlns="http://namespaces.zope.org/zope"
         xmlns:five="http://namespaces.zope.org/five"
         i18n_domain="foo">
        <include package="Products.Five" file="meta.zcml" />
        <five:registerPackage
           package="OFS.tests.applicationproduct"
           initialize="OFS.tests.applicationproduct.initialize"
           />
        </configure>'''
        zcml.load_string(configure_zcml)

        i = self.getOne()
        i.install_products()
        app = i.getApp()
        self.assertEqual(app.some_folder.meta_type, 'Folder')
