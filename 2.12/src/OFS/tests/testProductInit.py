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

import os, unittest, tempfile, shutil, cStringIO

from OFS.Application import Application
import Zope2.Startup
import ZConfig
from App.config import getConfiguration, setConfiguration
import Products

TEMPNAME = tempfile.mktemp()
TEMPPRODUCTS = os.path.join(TEMPNAME, "Products")
TEMPPRODUCTS2 = os.path.join(TEMPNAME, "Products2")
FAKEPRODUCTS = ['foo', 'bar', 'bee', 'baz']

cfg = """
instancehome <<INSTANCE_HOME>>
products <<PRODUCTS>>
products <<PRODUCTS2>>

<zodb_db main>
   mount-point /
   <mappingstorage>
      name mappingstorage
   </mappingstorage>
</zodb_db>
"""

# CAUTION:  A raw string must be used in the open() call.  This is crucial
# so that if you happen to be on Windows, and are passed a path containing
# backslashes, the backslashes get treated *as* backslashes instead of as
# string escape codes.
dummy_product_init = """
misc_ = {'a':1}
def amethod(self):
    pass
def initialize(context):
    f=open(r'%s', 'w')
    f.write('didit')
    f.close()
    context.registerClass(
        meta_type='grabass',
        permission='aPermission',
        constructors=(amethod,),
        legacy=(amethod,))
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

class TestProductInit( unittest.TestCase ):
    """ Test the application initializer object """

    def setUp(self):
        global original_config
        if original_config is None:
            original_config = getConfiguration()
        self.schema = getSchema()
        os.makedirs(TEMPNAME)
        os.makedirs(TEMPPRODUCTS)
        os.makedirs(TEMPPRODUCTS2)

    def tearDown(self):
        import App.config
        del self.schema
        App.config.setConfiguration(original_config)
        shutil.rmtree(TEMPNAME)
        Products.__path__ = [d for d in Products.__path__
                             if os.path.exists(d)]

    def configure(self, text):
        # We have to create a directory of our own since the existence
        # of the directory is checked.  This handles this in a
        # platform-independent way.
        schema = self.schema
        text = text.replace("<<INSTANCE_HOME>>", TEMPNAME)
        text = text.replace("<<PRODUCTS>>", TEMPPRODUCTS)
        text = text.replace("<<PRODUCTS2>>", TEMPPRODUCTS2)
        sio = cStringIO.StringIO(text)
        conf, handler = ZConfig.loadConfigFile(schema, sio)
        from Zope2.Startup.handlers import handleConfig
        handleConfig(conf, handler)
        self.assertEqual(conf.instancehome, TEMPNAME)
        setConfiguration(conf)

    def makeProduct(self, proddir):
        os.makedirs(proddir)
        f = open(os.path.join(proddir, '__init__.py'), 'w')
        f.write('#foo')
        f.close()

    def makeFakeProducts(self):
        for name in FAKEPRODUCTS:
            proddir = os.path.join(TEMPPRODUCTS, name)
            self.makeProduct(proddir)

    def test_get_products(self):
        self.makeFakeProducts()
        self.configure(cfg)
        from OFS.Application import get_products
        names =  [x[1] for x in get_products()]
        for name in FAKEPRODUCTS:
            self.assert_(name in names)

    def test_empty_dir_on_products_path_is_not_product(self):
        self.makeFakeProducts()
        os.makedirs(os.path.join(TEMPPRODUCTS, 'gleeb'))
        self.configure(cfg)
        from OFS.Application import get_products
        names =  [x[1] for x in get_products()]
        for name in FAKEPRODUCTS:
            self.assert_(name in names)
        self.assert_('gleeb' not in names)

    def test_file_on_products_path_is_not_product(self):
        self.makeFakeProducts()
        f = open(os.path.join(TEMPPRODUCTS, 'README.txt'), 'w')
        f.write('#foo')
        f.close()
        self.configure(cfg)
        from OFS.Application import get_products
        names =  [x[1] for x in get_products()]
        for name in FAKEPRODUCTS:
            self.assert_(name in names)
        self.assert_('README.txt' not in names)

    def test_multiple_product_paths(self):
        self.makeFakeProducts()
        self.makeProduct(os.path.join(TEMPPRODUCTS2, 'another'))
        self.configure(cfg)
        from OFS.Application import get_products
        names =  [x[1] for x in get_products()]
        for name in FAKEPRODUCTS:
            self.assert_(name in names)
        self.assert_('another' in names)

    def test_import_products(self):
        self.makeFakeProducts()
        self.configure(cfg)
        from OFS.Application import import_products
        names = import_products()
        for name in FAKEPRODUCTS:
            assert name in names

    def test_import_product_throws(self):
        self.makeProduct(os.path.join(TEMPPRODUCTS, 'abar'))
        f = open(os.path.join(TEMPPRODUCTS, 'abar', '__init__.py'), 'w')
        f.write('Syntax Error!')
        f.close()
        self.configure(cfg)
        try:
            from logging import getLogger
            logger = getLogger('Zope')
            logger.disabled = 1
            self.assertRaises(SyntaxError, self.import_bad_product)
        finally:
            logger.disabled = 0
            

    def import_bad_product(self):
        from OFS.Application import import_product
        import_product(TEMPPRODUCTS, 'abar', raise_exc=1)

    def test_install_product(self):
        self.makeProduct(os.path.join(TEMPPRODUCTS, 'abaz'))
        f = open(os.path.join(TEMPPRODUCTS, 'abaz', '__init__.py'), 'w')
        doneflag = os.path.join(TEMPPRODUCTS, 'abaz', 'doneflag')
        f.write(dummy_product_init % doneflag)
        f.close()
        self.configure(cfg)
        from OFS.Application import install_product, get_folder_permissions,\
             Application
        import Products
        from OFS.Folder import Folder
        app = getApp()
        meta_types = []
        install_product(app, TEMPPRODUCTS, 'abaz', meta_types,
                        get_folder_permissions(), raise_exc=1)
        # misc_ dictionary is updated
        self.assert_(Application.misc_.__dict__.has_key('abaz'))
        # initialize is called
        self.assert_(os.path.exists(doneflag))
        # Methods installed into folder
        self.assert_(hasattr(Folder, 'amethod'))
        # permission roles put into folder
        self.assert_(hasattr(Folder, 'amethod__roles__'))
        # Products.meta_types updated
        self.assert_( {'name': 'grabass',
                       'action': 'manage_addProduct/abaz/amethod',
                       'product': 'abaz',
                       'permission': 'aPermission',
                       'visibility': 'Global',
                       'interfaces': (),
                       'instance': None,
                       'container_filter': None}
                      in Products.meta_types)

    def test_install_products(self):
        self.makeFakeProducts()
        self.configure(cfg)
        app = getApp()
        from OFS.Application import install_products
        install_products(app)
        obids = app.Control_Panel.Products.objectIds()
        for name in FAKEPRODUCTS:
            assert name in obids

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest( unittest.makeSuite( TestProductInit ) )
    return suite

def main():
    unittest.main(defaultTest='test_suite')

if __name__ == '__main__':
    main()
