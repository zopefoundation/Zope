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
        self.failUnless(cmp(fc, None) > 0)

    def test___cmp___non_FuncCode(self):
        def f(self):
            pass
        fc = self._makeOne(f, im=1)
        self.failUnless(cmp(fc, object()) > 0)

    def test___cmp___w_FuncCode_same_args(self):
        def f(self, a, b):
            pass
        def g(self, a, b):
            pass
        fc = self._makeOne(f, im=1)
        fc2 = self._makeOne(g, im=1)
        self.failUnless(cmp(fc, fc2) == 0)

    def test___cmp___w_FuncCode_different_args(self):
        def f(self):
            pass
        def g(self, a, b):
            pass
        fc = self._makeOne(f, im=1)
        fc2 = self._makeOne(g, im=1)
        self.failUnless(cmp(fc, fc2) < 0)
 
class Test_getPath(unittest.TestCase):

    _old_Products___path__ = None
    _tmpdirs = ()

    def tearDown(self):
        import shutil
        if self._old_Products___path__ is not None:
            import Products
            Products.__path__ = self._old_Products___path__
        for tmpdir in self._tmpdirs:
            shutil.rmtree(tmpdir)

    def _callFUT(self, prefix, name, checkProduct=1, suffixes=('',), cfg=None):
        from App.Extensions import getPath
        return getPath(prefix, name, checkProduct, suffixes, cfg)

    def _makeTempdir(self):
        import tempfile
        tmp = tempfile.mkdtemp()
        self._tmpdirs += (tmp,)
        return tmp

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

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(FuncCodeTests),
        unittest.makeSuite(Test_getPath),
    ))
