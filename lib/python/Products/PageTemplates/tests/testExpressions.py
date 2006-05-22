import unittest

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

        # XXX The following test fails because Zope 3 doesn't allow
        # empty path elements.  My idea is to eventually disallow
        # blank path elements, but to allow them for a limited
        # deprecation period.  We do that by implementing our own
        # SubPathExpr that just looks for empty path elements and
        # replaces them with a call to a TALESNamespace adapter that
        # explicitly does the empty element lookup.  Then we hand off
        # to the standard Zope 3 SubPathExpr implementation.
        # Something along these lines (pseudo-ish code!):
        #
        # class Zope2SubPathExpr(SubPathExpr):
        #     def __init__(self, text, ...):
        #         text = text.replace('//', 'blank:element')
        #         return super(Zope2SubPathExpr, self).__init__(text ...)
        #
        assert ec.evaluate('d/') == 'blank'

        assert ec.evaluate('d/_') == 'under'
        assert ec.evaluate('d/ | nothing') == 'blank'
        assert ec.evaluate('d/?blank') == 'blank'

    def testHybrid(self):
        '''Test hybrid path expressions'''
        ec = self.ec
        assert ec.evaluate('x | python:1+1') == 2

        # XXX The following test fails because int here is called
        # which yields 0, not the int type. Why is it called? Because
        # PathExpr calls everything that's not on the trees by the
        # time it has counted to three.
        assert ec.evaluate('x | python:int') == int

        # The whole expression is a PathExpr with two subexpressions:
        # a SubPathExpr and a PythonExpr.  The first fails as
        # intended, so the second is evaluated.  The result is called.
        # The old PathExpr didn't do that.  Specifically, it wouldn't
        # call builtin types (str, unicode, dict, list, tuple, bool).
        # There are two things we can do about this now:

        # a) Nothing. Accept the incompatibility from Zope 2.9 to
        #    2.10.  Of course, this might break existing code, but
        #    there are ways to make code compatible with 2.9 and 2.10:
        #    Add a nocall: before the python: expression (if that's
        #    possible?!?).  You just have to know about these things
        #    beforehand.
        
        # b) Provide our own PathExpr implementation that does not
        #    blindly call primitive types.  We would have to keep this
        #    code in Zope 2 forever which means there'd be an
        #    incompatibility between Zope 2 and Zope 3 ZPTs forever.

        # I'm leaning towards option a). Given that this only turns
        # out to be a problem with builtin types, the breakage is
        # quite limited.

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
