##############################################################################
#
# Copyright (c) 2010 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
""" Unit tests for App.Extensions module
"""
import unittest


class FuncCodeTests(unittest.TestCase):

    def _getTargetClass(self):
        from App.Extensions import FuncCode
        return FuncCode

    def _makeOne(self, f, im=0):
        return self._getTargetClass()(f, im)

    def test_ctor_not_method_no_args(self):
        def f():
            pass
        fc = self._makeOne(f)
        self.assertEqual(fc.co_varnames, ())
        self.assertEqual(fc.co_argcount, 0)

    def test_ctor_not_method_w_args(self):
        def f(a, b):
            pass
        fc = self._makeOne(f)
        self.assertEqual(fc.co_varnames, ('a', 'b'))
        self.assertEqual(fc.co_argcount, 2)

    def test_ctor_w_method_no_args(self):
        def f(self):
            pass
        fc = self._makeOne(f, im=1)
        self.assertEqual(fc.co_varnames, ())
        self.assertEqual(fc.co_argcount, 0)

    def test_ctor_w_method_w_args(self):
        def f(self, a, b):
            pass
        fc = self._makeOne(f, im=1)
        self.assertEqual(fc.co_varnames, ('a', 'b'))
        self.assertEqual(fc.co_argcount, 2)

    def test___cmp___None(self):
        def f(self):
            pass
        fc = self._makeOne(f, im=1)
        self.assertTrue(cmp(fc, None) > 0)

    def test___cmp___non_FuncCode(self):
        def f(self):
            pass
        fc = self._makeOne(f, im=1)
        self.assertTrue(cmp(fc, object()) > 0)

    def test___cmp___w_FuncCode_same_args(self):
        def f(self, a, b):
            pass
        def g(self, a, b):
            pass
        fc = self._makeOne(f, im=1)
        fc2 = self._makeOne(g, im=1)
        self.assertTrue(cmp(fc, fc2) == 0)

    def test___cmp___w_FuncCode_different_args(self):
        def f(self):
            pass
        def g(self, a, b):
            pass
        fc = self._makeOne(f, im=1)
        fc2 = self._makeOne(g, im=1)
        self.assertTrue(cmp(fc, fc2) < 0)


class _TempdirBase:

    _old_Products___path__ = None
    _tmpdirs = ()
    _old_sys_path = None
    _added_path = None

    def tearDown(self):
        import shutil
        if self._old_Products___path__ is not None:
            import Products
            Products.__path__ = self._old_Products___path__
        for tmpdir in self._tmpdirs:
            shutil.rmtree(tmpdir)
        if self._old_sys_path is not None:
            import sys
            sys.path[:] = self._old_sys_path
            for k, v in sys.modules.items():
                if getattr(v, '__file__', '').startswith(self._added_path):
                    del sys.modules[k]

    def _makeTempdir(self):
        import tempfile
        tmp = tempfile.mkdtemp()
        self._tmpdirs += (tmp,)
        return tmp

    def _makePathDir(self):
        import sys
        dir = self._makeTempdir()
        self._old_sys_path = sys.path[:]
        sys.path.insert(0, dir)
        self._added_path = dir
        return dir

    def _makeTempExtension(self, name='foo', extname='Extensions', dir=None):
        import os
        if dir is None:
            dir = self._makeTempdir()
        if name is None:
            extdir = os.path.join(dir, extname)
        else:
            extdir = os.path.join(dir, name, extname)
        os.makedirs(extdir)
        return extdir

    def _makeTempProduct(self, name='foo', extname='Extensions'):
        import Products
        self._old_Products___path__ = Products.__path__[:]
        root = self._makeTempdir()
        pdir = self._makeTempExtension(name=name, extname=extname, dir=root)
        Products.__path__ = (root,)
        return pdir

    def _makeFile(self, dir, name, text='#extension'):
        import os
        fqn = os.path.join(dir, name)
        f = open(fqn, 'w')
        f.write(text)
        f.flush()
        f.close()
        return fqn


class Test_getPath(_TempdirBase, unittest.TestCase):

    def _callFUT(self, prefix, name, checkProduct=1, suffixes=('',), cfg=None):
        from App.Extensions import getPath
        return getPath(prefix, name, checkProduct, suffixes, cfg)

    def _makeConfig(self, **kw):
        class DummyConfig:
            def __init__(self, **kw):
                self.__dict__.update(kw)
        return DummyConfig(**kw)

    def test_name_as_path_raises(self):
        self.assertRaises(ValueError, self._callFUT, 'Extensions', 'foo/bar')

    def test_found_in_product(self):
        instdir = self._makeTempdir()
        swdir = self._makeTempdir()
        cfg = self._makeConfig(instancehome=instdir,
                               softwarehome=swdir,
                              )
        extdir = self._makeTempProduct()
        ext = self._makeFile(extdir, 'extension.py')
        path = self._callFUT('Extensions', 'foo.extension',
                             suffixes=('py',), cfg=cfg)
        self.assertEqual(path, ext)

    def test_not_found_in_product(self):
        instdir = self._makeTempdir()
        swdir = self._makeTempdir()
        cfg = self._makeConfig(instancehome=instdir,
                               softwarehome=swdir,
                              )
        extdir = self._makeTempProduct()
        ext = self._makeFile(extdir, 'extension.py')
        path = self._callFUT('Extensions', 'foo.other',
                             suffixes=('py',), cfg=cfg)
        self.assertEqual(path, None)

    def test_wo_checkProduct_skips_product(self):
        import Products
        self._old_Products___path__ = Products.__path__
        del Products.__path__ # so any iteration will raise
        instdir = self._makeTempdir()
        instext = self._makeTempExtension(name=None, dir=instdir)
        instfqn = self._makeFile(instext, 'extension.py')
        swdir = self._makeTempdir()
        swext = self._makeTempExtension(name=None, dir=swdir)
        swfqn = self._makeFile(swext, 'extension.py')
        cfg = self._makeConfig(instancehome=instdir,
                               softwarehome=swdir,
                              )
        path = self._callFUT('Extensions', 'extension', checkProduct=0,
                             suffixes=('py',), cfg=cfg)
        self.assertEqual(path, instfqn)

    def test_w_cfg_extensions(self):
        cfgdir = self._makeTempdir()
        cfgfqn = self._makeFile(cfgdir, 'extension.py')
        instdir = self._makeTempdir()
        instext = self._makeTempExtension(name=None, dir=instdir)
        instfqn = self._makeFile(instext, 'extension.py')
        swdir = self._makeTempdir()
        swext = self._makeTempExtension(name=None, dir=swdir)
        swfqn = self._makeFile(swext, 'extension.py')
        cfg = self._makeConfig(extensions=cfgdir,
                               instancehome=instdir,
                               softwarehome=swdir,
                              )
        path = self._callFUT('Extensions', 'extension', checkProduct=0,
                             suffixes=('py',), cfg=cfg)
        self.assertEqual(path, cfgfqn)

    def test_not_found_in_instancehome(self):
        import os
        instdir = self._makeTempdir()
        zopedir = self._makeTempdir()
        swdir = os.path.join(zopedir, 'src')
        os.mkdir(swdir)
        zopeext = self._makeTempExtension(name=None, dir=zopedir)
        zopefqn = self._makeFile(zopeext, 'extension.py')
        cfg = self._makeConfig(instancehome=instdir,
                               softwarehome=swdir,
                              )
        path = self._callFUT('Extensions', 'extension',
                             suffixes=('py',), cfg=cfg)
        self.assertEqual(path, zopefqn)

    def test_no_swhome(self):
        instdir = self._makeTempdir()
        cfg = self._makeConfig(instancehome=instdir,
                              )
        extdir = self._makeTempProduct()
        path = self._callFUT('Extensions', 'extension',
                             suffixes=('py',), cfg=cfg)
        self.assertEqual(path, None)

    def test_search_via_import_one_dot(self):
        import os
        instdir = self._makeTempdir()
        cfg = self._makeConfig(instancehome=instdir,
                              )
        pathdir = self._makePathDir()
        pkgdir = os.path.join(pathdir, 'somepkg')
        os.mkdir(pkgdir)
        self._makeFile(pkgdir, '__init__.py', '#package')
        pkgext = self._makeTempExtension(name=None, dir=pkgdir)
        pkgfqn = self._makeFile(pkgext, 'extension.py')
        path = self._callFUT('Extensions', 'somepkg.extension',
                                suffixes=('py',), cfg=cfg)
        self.assertEqual(path, pkgfqn)

    def test_search_via_import_multiple_dots(self):
        import os
        instdir = self._makeTempdir()
        cfg = self._makeConfig(instancehome=instdir,
                              )
        pathdir = self._makePathDir()
        pkgdir = os.path.join(pathdir, 'somepkg')
        os.mkdir(pkgdir)
        self._makeFile(pkgdir, '__init__.py', '#package')
        subpkgdir = os.path.join(pkgdir, 'subpkg')
        os.mkdir(subpkgdir)
        self._makeFile(subpkgdir, '__init__.py', '#subpackage')
        subpkgext = self._makeTempExtension(name=None, dir=subpkgdir)
        subpkgfqn = self._makeFile(subpkgext, 'extension.py')
        path = self._callFUT('Extensions', 'somepkg.subpkg.extension',
                                suffixes=('py',), cfg=cfg)
        self.assertEqual(path, subpkgfqn)

"""
Index: lib/python/App/Extensions.py
===================================================================
--- lib/python/App/Extensions.py	(revision 28473)
+++ lib/python/App/Extensions.py	(working copy)
@@ -87,8 +87,14 @@
                 r = _getPath(product_dir, os.path.join(p, prefix), n, suffixes)
                 if r is not None: return r
 
+        
     import App.config
     cfg = App.config.getConfiguration()
+
+    if (prefix=="Extensions") and (cfg.extensions is not None):
+        r=_getPath(cfg.extensions, '', name, suffixes)
+        if r is not None: return r
+        
     sw=os.path.dirname(os.path.dirname(cfg.softwarehome))
     for home in (cfg.instancehome, sw):
         r=_getPath(home, prefix, name, suffixes)
"""

class Test_getObject(_TempdirBase, unittest.TestCase):

    def _callFUT(self, module, name, reload=0, modules=None):
        from App.Extensions import getObject
        if modules is not None:
            return getObject(module, name, reload, modules)
        return getObject(module, name, reload)

    def test_cache_miss(self):
        from zExceptions import NotFound
        MODULES = {'somemodule': {}}
        self.assertRaises(NotFound,
                          self._callFUT, 'somemodule', 'name', modules=MODULES)

    def test_cache_hit(self):
        obj = object()
        MODULES = {'somemodule': {'name': obj}}
        found = self._callFUT('somemodule', 'name', modules=MODULES)
        self.assertTrue(found is obj)

    def test_no_such_module(self):
        from zExceptions import NotFound
        MODULES = {}
        self.assertRaises(NotFound, self._callFUT,
                          'nonesuch', 'name', modules=MODULES)
        self.assertFalse('nonesuch' in MODULES)

    def test_not_found_in_module(self):
        from zExceptions import NotFound
        MODULES = {}
        extdir = self._makeTempProduct()
        ext = self._makeFile(extdir, 'extension.py')
        self.assertRaises(NotFound, self._callFUT,
                          'foo.extension', 'name', modules=MODULES)
        self.assertTrue('foo.extension' in MODULES)
        self.assertFalse('named' in MODULES['foo.extension'])

    def test_found_in_module(self):
        MODULES = {}
        extdir = self._makeTempProduct()
        ext = self._makeFile(extdir, 'extension.py', EXTENSION_PY)
        found = self._callFUT('foo.extension', 'named', modules=MODULES)
        self.assertEqual(found, 'NAMED')
        self.assertTrue('foo.extension' in MODULES)
        self.assertEqual(MODULES['foo.extension']['named'], 'NAMED')

    def test_found_in_module_pyc(self):
        from compileall import compile_dir
        import os
        MODULES = {}
        extdir = self._makeTempProduct()
        ext = self._makeFile(extdir, 'extension.py', EXTENSION_PY)
        compile_dir(extdir, quiet=1)
        os.remove(ext)
        found = self._callFUT('foo.extension', 'named', modules=MODULES)
        self.assertEqual(found, 'NAMED')
        self.assertTrue('foo.extension' in MODULES)
        self.assertEqual(MODULES['foo.extension']['named'], 'NAMED')

    def test_found_in_module_after_cache_miss(self):
        cached = {}
        MODULES = {'foo.extension': cached}
        extdir = self._makeTempProduct()
        ext = self._makeFile(extdir, 'extension.py', EXTENSION_PY)
        found = self._callFUT('foo.extension', 'named', modules=MODULES)
        self.assertEqual(found, 'NAMED')
        self.assertEqual(cached['named'], 'NAMED')

    def test_found_in_module_after_cache_hit_but_reload(self):
        cached = {'named': 'BEFORE'}
        MODULES = {'foo.extension': cached}
        extdir = self._makeTempProduct()
        ext = self._makeFile(extdir, 'extension.py', EXTENSION_PY)
        found = self._callFUT('foo.extension', 'named', reload=1,
                              modules=MODULES)
        self.assertEqual(found, 'NAMED')
        self.assertEqual(cached['named'], 'NAMED')


class Test_getBrain(_TempdirBase, unittest.TestCase):

    def _callFUT(self, module, name, reload=0, modules=None):
        from App.Extensions import getBrain
        if modules is not None:
            return getBrain(module, name, reload, modules)
        return getBrain(module, name, reload)

    def test_no_module_no_class_yields_NoBrains(self):
        from App.Extensions import NoBrains
        self.assertTrue(self._callFUT('', '') is NoBrains)

    def test_missing_name(self):
        from App.Extensions import NoBrains
        from zExceptions import NotFound
        self.assertTrue(self._callFUT('', '') is NoBrains)
        MODULES = {'somemodule': {}}
        self.assertRaises(NotFound,
                          self._callFUT, 'somemodule', 'name', modules=MODULES)

    def test_not_a_class(self):
        from App.Extensions import NoBrains
        self.assertTrue(self._callFUT('', '') is NoBrains)
        MODULES = {'somemodule': {'name': object()}}
        self.assertRaises(ValueError,
                          self._callFUT, 'somemodule', 'name', modules=MODULES)

    def test_found_class(self):
        from App.Extensions import NoBrains
        self.assertTrue(self._callFUT('', '') is NoBrains)
        MODULES = {'somemodule': {'name': self.__class__}}
        self.assertEqual(self._callFUT('somemodule', 'name', modules=MODULES),
                         self.__class__)

EXTENSION_PY = """\
named = 'NAMED'
"""

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(FuncCodeTests),
        unittest.makeSuite(Test_getPath),
        unittest.makeSuite(Test_getObject),
        unittest.makeSuite(Test_getBrain),
    ))
