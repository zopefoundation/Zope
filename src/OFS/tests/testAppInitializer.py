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

from logging import getLogger

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
        self.assertTrue(hasattr(app.Control_Panel, 'Products'))
        self.assertEqual(app.Control_Panel.Products.meta_type,
                         'Product Management')

    def test_install_tempfolder_and_sdc(self):
        self.configure(good_cfg)
        i = self.getOne()
        i.install_tempfolder_and_sdc()
        app = i.getApp()
        self.assertEqual(app.temp_folder.meta_type, 'Temporary Folder')
        self.assertEqual(app.temp_folder.session_data.meta_type,
                         'Transient Object Container')
        self.assertTrue(app._getInitializerFlag('temp_folder'))

    def test_install_tempfolder_and_sdc_status(self):
        self.configure(good_cfg)
        i = self.getOne()
        status = i.install_tempfolder_and_sdc()
        self.assertTrue(status)

        i = self.getOne()
        self.configure(bad_cfg)
        try:
            logger = getLogger('Zope.ZODBMountPoint')
            logger.disabled = 1
            status = i.install_tempfolder_and_sdc()
        finally:
            logger.disabled = 0
        self.assertFalse(status)

    def test_install_tempfolder_and_sdc_unlimited_sessions(self):
        unlimited_cfg = good_cfg + """
        maximum-number-of-session-objects 0
        """
        self.configure(unlimited_cfg)
        i = self.getOne()
        status = i.install_tempfolder_and_sdc()
        self.assertTrue(status)

        sdc = i.getApp().temp_folder.session_data
        self.assertEqual(sdc.getSubobjectLimit(), 0)

    def test_install_browser_id_manager(self):
        self.configure(good_cfg)
        i = self.getOne()
        app = i.getApp()
        i.install_browser_id_manager()
        self.assertEqual(app.browser_id_manager.meta_type,'Browser Id Manager')
        self.assertTrue(app._getInitializerFlag('browser_id_manager'))

    def test_install_virtual_hosting(self):
        self.configure(good_cfg)
        i = self.getOne()
        app = i.getApp()
        i.install_virtual_hosting()
        self.assertEqual(app.virtual_hosting.meta_type,'Virtual Host Monster')
        self.assertTrue(app._getInitializerFlag('virtual_hosting'))

    def test_install_session_data_manager(self):
        self.configure(good_cfg)
        i = self.getOne()
        i.install_session_data_manager()
        app = i.getApp()
        self.assertEqual(app.session_data_manager.meta_type,
                         'Session Data Manager')
        self.assertTrue(app._getInitializerFlag('session_data_manager'))

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

    def test_install_errorlog(self):
        self.configure(good_cfg)
        i = self.getOne()
        i.install_errorlog()
        app = i.getApp()
        self.assertEqual(app.error_log.meta_type, 'Site Error Log')
        self.assertTrue(app._getInitializerFlag('error_log'))

    def test_install_products(self):
        self.configure(good_cfg)
        i = self.getOne()
        i.install_products()
        self.assertTrue(Application.misc_.__dict__.has_key('OFSP'))

    def test_install_standards(self):
        self.configure(good_cfg)
        i = self.getOne()
        i.install_products() # required
        i.install_standards()
        app = i.getApp()
        self.assertEqual(app.index_html.meta_type, 'Page Template')
        self.assertEqual(app.standard_error_message.meta_type, 'DTML Method')
        self.assertTrue(hasattr(app, '_standard_objects_have_been_added'))


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest( unittest.makeSuite( TestInitialization ) )
    return suite
