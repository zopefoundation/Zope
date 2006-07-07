import unittest

import zope.component.testing
from zope.traversing.adapters import DefaultTraversable

from Products.PageTemplates import Expressions
from Products.PageTemplates.DeferExpr import LazyWrapper
from Products.PageTemplates.DeferExpr import DeferWrapper

class Dummy:
    __allow_access_to_unprotected_subobjects__ = 1
    def __call__(self):
        return 'dummy'

class ExpressionTests(zope.component.testing.PlacelessSetup, unittest.TestCase):

    def setUp(self):
        super(ExpressionTests, self).setUp()
        zope.component.provideAdapter(DefaultTraversable, (None,))

        self.e = e = Expressions.getEngine()
        self.ec = e.getContext(
            one = 1,
            d = {'one': 1, 'b': 'b', '': 'blank', '_': 'under'},
            blank = '',
            dummy = Dummy()
            )

    def testCompile(self):
        '''Test expression compilation'''
        e = self.e
        for p in ('x', 'x/y', 'x/y/z'):
            e.compile(p)
        e.compile('path:a|b|c/d/e')
        e.compile('string:Fred')
        e.compile('string:A$B')
        e.compile('string:a ${x/y} b ${y/z} c')
        e.compile('python: 2 + 2')
        e.compile('python: 2 \n+\n 2\n')

    def testSimpleEval(self):
        '''Test simple expression evaluation'''
        ec = self.ec
        assert ec.evaluate('one') == 1
        assert ec.evaluate('d/one') == 1
        assert ec.evaluate('d/b') == 'b'

    def testRenderedEval(self):
        ec = self.ec
        assert ec.evaluate('dummy') == 'dummy'

    def testEval1(self):
        '''Test advanced expression evaluation 1'''
        ec = self.ec
        assert ec.evaluate('x | nothing') is None
        # empty path elements aren't supported anymore, for the lack
        # of a use case
        #assert ec.evaluate('d/') == 'blank'
        assert ec.evaluate('d/_') == 'under'
        #assert ec.evaluate('d/ | nothing') == 'blank'
        assert ec.evaluate('d/?blank') == 'blank'

    def testHybrid(self):
        '''Test hybrid path expressions'''
        ec = self.ec
        assert ec.evaluate('x | python:1+1') == 2
        assert ec.evaluate('x | python:int') == int
        assert ec.evaluate('x | string:x') == 'x'
        assert ec.evaluate('x | string:$one') == '1'
        assert ec.evaluate('x | not:exists:x')

    def testIteratorZRPythonExpr(self):
        '''Test access to iterator functions from Python expressions'''
        ec = self.ec
        ec.beginScope()
        ec.setRepeat('loop', "python:[1,2,3]")
        assert ec.evaluate("python:repeat['loop'].odd()")
        ec.endScope()

    def testWrappers(self):
        """Test if defer and lazy are returning their wrappers
        """
        ec = self.ec
        defer = ec.evaluate('defer: b')
        lazy = ec.evaluate('lazy: b')
        self.failUnless(isinstance(defer, DeferWrapper))
        self.failUnless(isinstance(lazy, LazyWrapper))

    def test_empty_ZopePathExpr(self):
        """Test empty path expressions.
        """
        ec = self.ec
        self.assertEquals(ec.evaluate('path:'), None)
        self.assertEquals(ec.evaluate('path:  '), None)
        self.assertEquals(ec.evaluate(''), None)
        self.assertEquals(ec.evaluate('  \n'), None)

def test_suite():
    return unittest.makeSuite(ExpressionTests)

if __name__=='__main__':
    main()
