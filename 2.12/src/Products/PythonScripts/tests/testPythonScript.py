##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
import os, unittest, warnings

from Products.PythonScripts.PythonScript import PythonScript
from AccessControl.SecurityManagement import newSecurityManager
from AccessControl.SecurityManagement import noSecurityManager
from RestrictedPython.tests.verify import verify


if __name__=='__main__':
    here = os.getcwd()
else:
    here = os.path.dirname(__file__)
    if not here:
        here = os.getcwd()

class WarningInterceptor:

    _old_stderr = None
    _our_stderr_stream = None

    def _trap_warning_output( self ):

        if self._old_stderr is not None:
            return

        import sys
        from StringIO import StringIO

        self._old_stderr = sys.stderr
        self._our_stderr_stream = sys.stderr = StringIO()

    def _free_warning_output( self ):

        if self._old_stderr is None:
            return

        import sys
        sys.stderr = self._old_stderr

# Test Classes

def readf(name):
    path = os.path.join(here, 'tscripts', '%s.ps' % name)
    return open(path, 'r').read()

class VerifiedPythonScript(PythonScript):

    def _newfun(self, code):
        verify(code)
        return PythonScript._newfun(self, code)


class PythonScriptTestBase(unittest.TestCase):
    def setUp(self):
        newSecurityManager(None, None)

    def tearDown(self):
        noSecurityManager()

    def _newPS(self, txt, bind=None):
        ps = VerifiedPythonScript('ps')
        ps.ZBindings_edit(bind or {})
        ps.write(txt)
        ps._makeFunction()
        if ps.errors:
            raise SyntaxError, ps.errors[0]
        return ps

    def _filePS(self, fname, bind=None):
        ps = VerifiedPythonScript(fname)
        ps.ZBindings_edit(bind or {})
        ps.write(readf(fname))
        ps._makeFunction()
        if ps.errors:
            raise SyntaxError, ps.errors[0]
        return ps

class TestPythonScriptNoAq(PythonScriptTestBase):

    def testEmpty(self):
        empty = self._newPS('')()
        self.failUnless(empty is None)

    def testIndented(self):
        # This failed to compile in Zope 2.4.0b2.
        res = self._newPS('if 1:\n return 2')()
        self.assertEqual(res, 2)

    def testReturn(self):
        res = self._newPS('return 1')()
        self.assertEqual(res, 1)

    def testReturnNone(self):
        res = self._newPS('return')()
        self.failUnless(res is None)

    def testParam1(self):
        res = self._newPS('##parameters=x\nreturn x')('txt')
        self.assertEqual(res, 'txt')

    def testParam2(self):
        eq = self.assertEqual
        one, two = self._newPS('##parameters=x,y\nreturn x,y')('one','two')
        eq(one, 'one')
        eq(two, 'two')

    def testParam26(self):
        import string
        params = string.letters[:26]
        sparams = ','.join(params)
        ps = self._newPS('##parameters=%s\nreturn %s' % (sparams, sparams))
        res = ps(*params)
        self.assertEqual(res, tuple(params))

    def testArithmetic(self):
        res = self._newPS('return 1 * 5 + 4 / 2 - 6')()
        self.assertEqual(res, 1)

    def testCollector2295(self):
        res = self._newPS('if False:\n  pass\n#hi')

    def testCollector2295(self):
        res = self._newPS('if False:\n  pass\n#hi')

    def testReduce(self):
        res = self._newPS('return reduce(lambda x, y: x + y, [1,3,5,7])')()
        self.assertEqual(res, 16)
        res = self._newPS('return reduce(lambda x, y: x + y, [1,3,5,7], 1)')()
        self.assertEqual(res, 17)

    def testImport(self):
        eq = self.assertEqual
        a, b, c = self._newPS('import string; return string.split("a b c")')()
        eq(a, 'a')
        eq(b, 'b')
        eq(c, 'c')

    def testWhileLoop(self):
        res = self._filePS('while_loop')()
        self.assertEqual(res, 1)

    def testForLoop(self):
        res = self._filePS('for_loop')()
        self.assertEqual(res, 10)

    def testMutateLiterals(self):
        eq = self.assertEqual
        l, d = self._filePS('mutate_literals')()
        eq(l, [2])
        eq(d, {'b': 2})

    def testTupleUnpackAssignment(self):
        eq = self.assertEqual
        d, x = self._filePS('tuple_unpack_assignment')()
        eq(d, {'a': 0, 'b': 1, 'c': 2})
        eq(x, 3)

    def testDoubleNegation(self):
        res = self._newPS('return not not "this"')()
        self.assertEqual(res, 1)

    def testTryExcept(self):
        eq = self.assertEqual
        a, b = self._filePS('try_except')()
        eq(a, 1)
        eq(b, 1)

    def testBigBoolean(self):
        res = self._filePS('big_boolean')()
        self.failUnless(res)

    def testFibonacci(self):
        res = self._filePS('fibonacci')()
        self.assertEqual(
            res, [1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377,
                  610, 987, 1597, 2584, 4181, 6765, 10946, 17711, 28657,
                  46368, 75025, 121393, 196418, 317811, 514229, 832040,
                  1346269, 2178309, 3524578, 5702887, 9227465, 14930352,
                  24157817, 39088169, 63245986])

    def testSimplePrint(self):
        res = self._filePS('simple_print')()
        self.assertEqual(res, 'a 1 []\n')

    def testComplexPrint(self):
        res = self._filePS('complex_print')()
        self.assertEqual(res, 'double\ndouble\nx: 1\ny: 0 1 2\n\n')

    def testNSBind(self):
        f = self._filePS('ns_bind', bind={'name_ns': '_'})
        bound = f.__render_with_namespace__({'yes': 1, 'no': self.fail})
        self.assertEqual(bound, 1)

    def testNSBindInvalidHeader(self):
        self.assertRaises(SyntaxError, self._filePS, 'ns_bind_invalid')

    def testBooleanMap(self):
        res = self._filePS('boolean_map')()
        self.failUnless(res)

    def testGetSize(self):
        f = self._filePS('complex_print')
        self.assertEqual(f.get_size(), len(f.read()))

    def testSet(self):
        res = self._newPS('from sets import Set; return len(Set([1,2,3]))')()
        self.assertEqual(res, 3)

    def testDateTime(self):
        res = self._newPS("return DateTime('2007/12/10').strftime('%d.%m.%Y')")()
        self.assertEqual(res, '10.12.2007')

    def testRaiseSystemExitLaunchpad257269(self):
        ps = self._newPS("raise SystemExit")
        self.assertRaises(ValueError, ps)

    def testEncodingTestDotTestAllLaunchpad257276(self):
        ps = self._newPS("return 'foo'.encode('test.testall')")
        self.assertRaises(LookupError, ps)


class TestPythonScriptErrors(PythonScriptTestBase):
    
    def assertPSRaises(self, error, path=None, body=None):
        assert not (path and body) and (path or body)
        if body is None:
            body = readf(path)
        if error is SyntaxError:
            self.assertRaises(SyntaxError, self._newPS, body)
        else:
            ps = self._newPS(body)
            self.assertRaises(error, ps)

    def testSubversiveExcept(self):
        self.assertPSRaises(SyntaxError, path='subversive_except')

    def testBadImports(self):
        from zExceptions import Unauthorized
        self.assertPSRaises(Unauthorized, body="from string import *")
        self.assertPSRaises(Unauthorized, body="from datetime import datetime")
        self.assertPSRaises(Unauthorized, body="import mmap")

    def testAttributeAssignment(self):
        # It's illegal to assign to attributes of anything that
        # doesn't has enabling security declared.
        # Classes (and their instances) defined by restricted code
        # are an exception -- they are fully readable and writable.
        cases = [("import string", "string"),
                 ("def f(): pass", "f"),
                 ]
        assigns = ["%s.splat = 'spam'",
                   "setattr(%s, '_getattr_', lambda x, y: True)",
                   "del %s.splat",
                   ]
        
        for defn, name in cases:
            for asn in assigns:
                f = self._newPS(defn + "\n" + asn % name)
                self.assertRaises(TypeError, f)

class TestPythonScriptGlobals(PythonScriptTestBase, WarningInterceptor):

    def setUp(self):
        PythonScriptTestBase.setUp(self)

    def tearDown(self):
        self._free_warning_output()
        PythonScriptTestBase.tearDown(self)

    def _exec(self, script, bound_names=None, args=None, kws=None):
        if args is None:
            args = ()
        if kws is None:
            kws = {}
        bindings = {'name_container': 'container'}
        f = self._filePS(script, bindings)
        return f._exec(bound_names, args, kws)

    def testGlobalIsDeclaration(self):
        bindings = {'container': 7}
        results = self._exec('global_is_declaration', bindings)
        self.assertEqual(results, 8)

    def test__name__(self):
        f = self._filePS('class.__name__')
        self.assertEqual(f(), ("'script.foo'>", "'string'"))

    def test_filepath(self):
        # This test is meant to raise a deprecation warning.
        # It used to fail mysteriously instead.
        def warnMe(message):
            warnings.warn(message, stacklevel=2)

        try:
            f = self._filePS('filepath')
            self._trap_warning_output()
            results = f._exec({'container': warnMe}, (), {})
            self._free_warning_output()
            warning = self._our_stderr_stream.getvalue()
            self.failUnless('UserWarning: foo' in warning)
        except TypeError, e:
            self.fail(e)


class PythonScriptInterfaceConformanceTests(unittest.TestCase):

    def test_class_conforms_to_IWriteLock(self):
        from zope.interface.verify import verifyClass
        from webdav.interfaces import IWriteLock
        verifyClass(IWriteLock, PythonScript)

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestPythonScriptNoAq))
    suite.addTest(unittest.makeSuite(TestPythonScriptErrors))
    suite.addTest(unittest.makeSuite(TestPythonScriptGlobals))
    suite.addTest(unittest.makeSuite(PythonScriptInterfaceConformanceTests))
    return suite


def main():
    unittest.TextTestRunner().run(test_suite())


if __name__ == '__main__':
    main()
