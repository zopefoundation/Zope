##############################################################################
#
# Copyright (c) 2001 Zope Corporation and Contributors. All Rights Reserved.
# 
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
# 
##############################################################################
import os, sys, unittest

import ZODB
from Products.PythonScripts.PythonScript import PythonScript
from AccessControl.SecurityManagement import newSecurityManager
from AccessControl.SecurityManagement import noSecurityManager


if __name__=='__main__':
    here = os.getcwd()
else:
    here = os.path.dirname(__file__)
    if not here:
        here = os.getcwd()

# Test Classes

def readf(name):
    return open( os.path.join( here
                             , 'tscripts'
                             , '%s.ps' % name
                             ), 'r').read()

class TestPythonScriptNoAq(unittest.TestCase):

    def setUp(self):
        newSecurityManager(None, None)

    def tearDown(self):
        noSecurityManager()

    def _newPS(self, txt, bind=None):
        ps = PythonScript('ps')
        ps.ZBindings_edit(bind or {})
        ps.write(txt)
        ps._makeFunction()
        return ps

    def fail(self):
        'Fail if called'
        assert 0, 'Fail called'

    def testEmpty(self):
        empty = self._newPS('')()
        assert empty is None, empty

    def testIndented(self):
        # This failed to compile in Zope 2.4.0b2.
        res = self._newPS('if 1:\n return 2')()
        assert res == 2, res

    def testReturn(self):
        return1 = self._newPS('return 1')()
        assert return1 == 1, return1

    def testReturnNone(self):
        none = self._newPS('return')()
        assert none == None

    def testParam1(self):
        txt = self._newPS('##parameters=x\nreturn x')('txt')
        assert txt == 'txt', txt

    def testParam2(self):
       one, two = self._newPS('##parameters=x,y\nreturn x,y')('one','two')
       assert one == 'one'
       assert two == 'two'

    def testParam26(self):
        import string
        params = string.letters[:26]
        sparams = string.join(params, ',')
        tup = apply(self._newPS('##parameters=%s\nreturn %s'
                                % (sparams,sparams)), params)
        assert tup == tuple(params), (tup, params)
        
    def testArithmetic(self):
        one = self._newPS('return 1 * 5 + 4 / 2 - 6')()
        assert one == 1, one

    def testImport(self):
        a,b,c = self._newPS('import string; return string.split("a b c")')()
        assert a == 'a'
        assert b == 'b'
        assert c == 'c'

    def testWhileLoop(self):
        one = self._newPS(readf('while_loop'))()
        assert one == 1

    def testForLoop(self):
        ten = self._newPS(readf('for_loop'))()
        assert ten == 10
        
    def testMutateLiterals(self):
        l, d = self._newPS(readf('mutate_literals'))()
        assert l == [2], l
        assert d == {'b': 2}

    def testTupleUnpackAssignment(self):
        d, x = self._newPS(readf('tuple_unpack_assignment'))()
        assert d == {'a': 0, 'b': 1, 'c': 2}, d
        assert x == 3, x

    def testDoubleNegation(self):
        one = self._newPS('return not not "this"')()
        assert one == 1

    def testTryExcept(self):
        a,b = self._newPS(readf('try_except'))()
        assert a==1
        assert b==1
        
    def testBigBoolean(self):
        true = self._newPS(readf('big_boolean'))()
        assert true, true

    def testFibonacci(self):
        r = self._newPS(readf('fibonacci'))()
        assert r == [1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377,
                     610, 987, 1597, 2584, 4181, 6765, 10946, 17711, 28657,
                     46368, 75025, 121393, 196418, 317811, 514229, 832040,
                     1346269, 2178309, 3524578, 5702887, 9227465, 14930352,
                     24157817, 39088169, 63245986], r

    def testSimplePrint(self):
        txt = self._newPS(readf('simple_print'))()
        assert txt == 'a 1 []\n', txt

    def testComplexPrint(self):
        txt = self._newPS(readf('complex_print'))()
        assert txt == 'double\ndouble\nx: 1\ny: 0 1 2\n\n', txt

    def testNSBind(self):
        f = self._newPS(readf('ns_bind'), bind={'name_ns': '_'})
        bound = f.__render_with_namespace__({'yes': 1, 'no': self.fail})
        assert bound == 1, bound

    def testBooleanMap(self):
        true = self._newPS(readf('boolean_map'))()
        assert true

    def testGetSize(self):
        f = self._newPS(readf('complex_print'))
        self.assertEqual(f.get_size(),len(f.read()))

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest( unittest.makeSuite( TestPythonScriptNoAq ) )
    return suite

def main():
    unittest.TextTestRunner().run(test_suite())

if __name__ == '__main__':
    main()

