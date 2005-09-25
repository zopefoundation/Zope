import os, sys, unittest

from Products.PageTemplates import Expressions
from Products.PageTemplates.DeferExpr import LazyWrapper
from Products.PageTemplates.DeferExpr import DeferWrapper

class Dummy:
    __allow_access_to_unprotected_subobjects__ = 1
    def __call__(self):
        return 'dummy'

class ExpressionTests(unittest.TestCase):

    def setUp(self):
        self.e = e = Expressions.getEngine()
        self.ec = e.getContext(
            one = 1,
            d = {'one': 1, 'b': 'b', '': 'blank', '_': 'under'},
            blank = '',
            dummy = Dummy()
            )

    def tearDown(self):
        del self.e, self.ec

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
        assert ec.evaluate('d/') == 'blank'
        assert ec.evaluate('d/_') == 'under'
        assert ec.evaluate('d/ | nothing') == 'blank'
        assert ec.evaluate('d/?blank') == 'blank'

    def testHybrid(self):
        '''Test hybrid path expressions'''
        ec = self.ec
        assert ec.evaluate('x | python:1+1') == 2
        assert ec.evaluate('x | python:int') == int
        assert ec.evaluate('x | string:x') == 'x'
        assert ec.evaluate('x | string:$one') == '1'
        assert ec.evaluate('x | not:exists:x')
        
    def testWrappers(self):
        """Test if defer and lazy are returning their wrappers
        """
        ec = self.ec
        defer = ec.evaluate('defer: b')
        lazy = ec.evaluate('lazy: b')
        self.failUnless(isinstance(defer, DeferWrapper))
        self.failUnless(isinstance(lazy, LazyWrapper))

def test_suite():
    return unittest.makeSuite(ExpressionTests)

if __name__=='__main__':
    main()
