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

import os, unittest, tempfile, cStringIO

from OFS.Application import Application, AppInitializer
import Zope2.Startup
import ZConfig
from App.config import getConfiguration, setConfiguration

TEMPNAME = tempfile.mktemp()
TEMPPRODUCTS = os.path.join(TEMPNAME, "Products")

bad_cfg = """
instancehome <<INSTANCE_HOME>>

<zodb_db main>
   mount-point /
   <mappingstorage>
      name mappingstorage
   </mappingstorage>
</zodb_db>
"""

good_cfg = bad_cfg + """
<zodb_db temporary>
    # Temporary storage database (for sessions)
    <temporarystorage>
      name temporary storage for sessioning
    </temporarystorage>
    mount-point /temp_folder
   container-class Products.TemporaryFolder.TemporaryContainer
</zodb_db>
"""

def getSchema():
    startup = os.path.dirname(os.path.realpath(Zope2.Startup.__file__))
    schemafile = os.path.join(startup, 'zopeschema.xml')
    return ZConfig.loadSchema(schemafile)

def getApp():
    from App.ZApplication import ZApplicationWrapper
    DB = getConfiguration().dbtab.getDatabase('/')
    return ZApplicationWrapper(DB, 'Application', Application, ())()

original_config = None

class TestInitialization( unittest.TestCase ):
    """ Test the application initializer object """

    def setUp(self):
        global original_config
        if original_config is None:
            original_config = getConfiguration()
        self.schema = getSchema()
        os.makedirs(TEMPNAME)
        os.makedirs(TEMPPRODUCTS)

    def tearDown(self):
        import App.config
        del self.schema
        App.config.setConfiguration(original_config)
        os.rmdir(TEMPPRODUCTS)
        os.rmdir(TEMPNAME)
        import Products
        Products.__path__ = [d for d in Products.__path__
                             if os.path.exists(d)]

    def configure(self, text):
        # We have to create a directory of our own since the existence
        # of the directory is checked.  This handles this in a
        # platform-independent way.
        schema = self.schema
        sio = cStringIO.StringIO(text.replace("<<INSTANCE_HOME>>", TEMPNAME))
        conf, handler = ZConfig.loadConfigFile(schema, sio)
        self.assertEqual(conf.instancehome, TEMPNAME)
        setConfiguration(conf)

    def getOne(self):
        app = getApp()
        return AppInitializer(app)

    def test_install_cp_and_products(self):
        self.configure(good_cfg)
        i = self.getOne()
        app = i.getApp()
        i.install_cp_and_products()
        self.assertTrue(hasattr(app, 'Control_Panel'))
        self.assertEqual(app.Control_Panel.meta_type, 'Control Panel')

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


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest( unittest.makeSuite( TestInitialization ) )
    return suite
