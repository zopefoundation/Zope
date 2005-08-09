import os, sys, unittest

from Products.PageTemplates import TALES
from Products.PageTemplates.tests import harness1
import string

class DummyUnicodeExpr:
    '''Dummy expression type handler returning unicode'''
    def __init__(self, name, expr, engine):
        self._name = name
        self._expr = expr
    def __call__(self, econtext):
        return unicode(self._expr, 'latin1')
    def __repr__(self):
        return '<SimpleExpr %s %s>' % (self._name, `self._expr`)

class TALESTests(unittest.TestCase):

    def testIterator0(self):
        '''Test sample Iterator class'''
        context = harness1()
        it = TALES.Iterator('name', (), context)
        assert not it.next(), "Empty iterator"
        context._complete_()

    def testIterator1(self):
        '''Test sample Iterator class'''
        context = harness1()
        it = TALES.Iterator('name', (1,), context)
        context._assert_('setLocal', 'name', 1)
        assert it.next() and not it.next(), "Single-element iterator"
        context._complete_()

    def testIterator2(self):
        '''Test sample Iterator class'''
        context = harness1()
        it = TALES.Iterator('text', 'text', context)
        for c in 'text':
            context._assert_('setLocal', 'text', c)
        for c in 'text':
            assert it.next(), "Multi-element iterator"
        assert not it.next(), "Multi-element iterator"
        context._complete_()

    def testRegisterType(self):
        '''Test expression type registration'''
        e = TALES.Engine()
        e.registerType('simple', TALES.SimpleExpr)
        assert e.getTypes()['simple'] == TALES.SimpleExpr

    def testRegisterTypeUnique(self):
        '''Test expression type registration uniqueness'''
        e = TALES.Engine()
        e.registerType('simple', TALES.SimpleExpr)
        try:
            e.registerType('simple', TALES.SimpleExpr)
        except TALES.RegistrationError:
            pass
        else:
            assert 0, "Duplicate registration accepted."

    def testRegisterTypeNameConstraints(self):
        '''Test constraints on expression type names'''
        e = TALES.Engine()
        for name in '1A', 'A!', 'AB ':
            try:
                e.registerType(name, TALES.SimpleExpr)
            except TALES.RegistrationError:
                pass
            else:
                assert 0, 'Invalid type name "%s" accepted.' % name

    def testCompile(self):
        '''Test expression compilation'''
        e = TALES.Engine()
        e.registerType('simple', TALES.SimpleExpr)
        ce = e.compile('simple:x')
        assert ce(None) == ('simple', 'x'), (
            'Improperly compiled expression %s.' % `ce`)

    def testGetContext(self):
        '''Test Context creation'''
        TALES.Engine().getContext()
        TALES.Engine().getContext(v=1)
        TALES.Engine().getContext(x=1, y=2)

    def getContext(self, **kws):
        e = TALES.Engine()
        e.registerType('simple', TALES.SimpleExpr)
        e.registerType('unicode', DummyUnicodeExpr)
        return e.getContext(**kws)

    def testContext0(self):
        '''Test use of Context'''
        se = self.getContext().evaluate('simple:x')
        assert se == ('simple', 'x'), (
            'Improperly evaluated expression %s.' % `se`)

    def testContextUnicode(self):
        '''Test evaluateText on unicode-returning expressions'''
        se = self.getContext().evaluateText('unicode:\xe9')
        self.assertEqual(se, u'\xe9')

    def testVariables(self):
        '''Test variables'''
        ctxt = self.getContext()
        c = ctxt.vars
        ctxt.beginScope()
        ctxt.setLocal('v1', 1)
        ctxt.setLocal('v2', 2)

        assert c['v1'] == 1, 'Variable "v1"'

        ctxt.beginScope()
        ctxt.setLocal('v1', 3)
        ctxt.setGlobal('g', 1)

        assert c['v1'] == 3, 'Inner scope'
        assert c['v2'] == 2, 'Outer scope'
        assert c['g'] == 1, 'Global'

        ctxt.endScope()

        assert c['v1'] == 1, "Uncovered local"
        assert c['g'] == 1, "Global from inner scope"

        ctxt.endScope()

def test_suite():
    return unittest.makeSuite(TALESTests)

if __name__=='__main__':
    unittest.main(defaultTest='test_suite')
