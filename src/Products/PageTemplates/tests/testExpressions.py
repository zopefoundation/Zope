# -*- coding: utf-8 -*-

import unittest
import warnings

from six import text_type

from AccessControl import safe_builtins
from zExceptions import NotFound
from zope.component.testing import PlacelessSetup


class EngineTestsBase(PlacelessSetup):

    def setUp(self):
        from zope.component import provideAdapter
        from zope.traversing.adapters import DefaultTraversable
        PlacelessSetup.setUp(self)
        provideAdapter(DefaultTraversable, (None,))

    def tearDown(self):
        PlacelessSetup.tearDown(self)

    def _makeEngine(self):
        # subclasses must override
        raise NotImplementedError

    def _makeContext(self, bindings=None):

        class Dummy(object):
            __allow_access_to_unprotected_subobjects__ = 1

            def __call__(self):
                return 'dummy'

        class DummyDocumentTemplate(object):
            __allow_access_to_unprotected_subobjects__ = 1
            isDocTemp = True

            def __call__(self, client=None, REQUEST={}, RESPONSE=None, **kw):
                return 'dummy'

            def absolute_url(self, relative=0):
                url = 'dummy'
                if not relative:
                    url = "http://server/" + url
                return url

        _DEFAULT_BINDINGS = dict(
            one=1,
            d={'one': 1, 'b': 'b', '': 'blank', '_': 'under'},
            blank='',
            dummy=Dummy(),
            dummy2=DummyDocumentTemplate(),
            eightbit=b'\xe4\xfc\xf6',
            # ZopeContext needs 'context' and 'template' keys for unicode
            # conflict resolution
            context=Dummy(),
            template=DummyDocumentTemplate(),
        )

        if bindings is None:
            bindings = _DEFAULT_BINDINGS
        return self._makeEngine().getContext(bindings)

    def test_compile(self):
        # Test expression compilation
        e = self._makeEngine()
        for p in ('x', 'x/y', 'x/y/z'):
            e.compile(p)
        e.compile('path:a|b|c/d/e')
        e.compile('string:Fred')
        e.compile('string:A$B')
        e.compile('string:a ${x/y} b ${y/z} c')
        e.compile('python: 2 + 2')
        e.compile('python: 2 \n+\n 2\n')

    def test_evaluate_simple_path_binding(self):
        ec = self._makeContext()
        self.assertEqual(ec.evaluate('one'), 1)

    def test_evaluate_simple_path_dict_key_int_value(self):
        ec = self._makeContext()
        self.assertEqual(ec.evaluate('d/one'), 1)

    def test_evaluate_simple_path_dict_key_string_value(self):
        ec = self._makeContext()
        self.assertEqual(ec.evaluate('d/b'), 'b')

    def test_evaluate_with_render_simple_callable(self):
        ec = self._makeContext()
        self.assertEqual(ec.evaluate('dummy'), 'dummy')

    def test_evaluate_with_unimplemented_call(self):
        class Dummy(object):
            def __call__(self):
                raise NotImplementedError()

        dummy = Dummy()
        ec = self._makeContext(bindings={'dummy': dummy})
        self.assertIs(ec.evaluate('dummy'), dummy)

    def test_evaluate_with_render_DTML_template(self):
        # http://www.zope.org/Collectors/Zope/2232
        # DTML templates could not be called from a Page Template
        # due to an ImportError
        ec = self._makeContext()
        self.assertEqual(ec.evaluate('dummy2'), 'dummy')

    def test_evaluate_alternative_first_missing(self):
        ec = self._makeContext()
        self.assertTrue(ec.evaluate('x | nothing') is None)

    def test_evaluate_dict_key_as_underscore(self):
        # Traversing to the name `_` will raise a DeprecationWarning
        # because it will go away in Zope 6.
        ec = self._makeContext()
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            self.assertEqual(ec.evaluate('d/_'), 'under')

    def test_evaluate_dict_with_key_from_expansion(self):
        ec = self._makeContext()
        self.assertEqual(ec.evaluate('d/?blank'), 'blank')

    def test_hybrid_with_python_expression_int_value(self):
        ec = self._makeContext()
        self.assertEqual(ec.evaluate('x | python:1+1'), 2)

    def test_hybrid_with_python_expression_type_value_not_called(self):
        ec = self._makeContext()
        self.assertEqual(ec.evaluate('x | python:int'), int)

    def test_hybrid_with_string_expression(self):
        ec = self._makeContext()
        self.assertEqual(ec.evaluate('x | string:x'), 'x')

    def test_hybrid_with_string_expression_and_expansion(self):
        ec = self._makeContext()
        self.assertEqual(ec.evaluate('x | string:$one'), '1')

    def test_hybrid_with_compound_expression_int_value(self):
        ec = self._makeContext()
        self.assertTrue(ec.evaluate('x | not:exists:x'))

    def test_access_iterator_from_python_expression(self):
        ec = self._makeContext()
        ec.beginScope()
        ec.setRepeat('loop', "python:[1,2,3]")
        self.assertTrue(ec.evaluate("python:repeat['loop'].odd()"))
        ec.endScope()

    def test_defer_expression_returns_wrapper(self):
        from zope.tales.expressions import DeferWrapper
        ec = self._makeContext()
        defer = ec.evaluate('defer: b')
        self.assertIsInstance(defer, DeferWrapper)

    def test_lazy_expression_returns_wrapper(self):
        from zope.tales.expressions import LazyWrapper
        ec = self._makeContext()
        lazy = ec.evaluate('lazy: b')
        self.assertIsInstance(lazy, LazyWrapper)

    def test_empty_path_expression_explicit(self):
        ec = self._makeContext()
        self.assertEqual(ec.evaluate('path:'), None)

    def test_empty_path_expression_explicit_with_trailing_whitespace(self):
        ec = self._makeContext()
        self.assertEqual(ec.evaluate('path:  '), None)

    def test_empty_path_expression_implicit(self):
        ec = self._makeContext()
        self.assertEqual(ec.evaluate(''), None)

    def test_empty_path_expression_implicit_with_trailing_whitespace(self):
        ec = self._makeContext()
        self.assertEqual(ec.evaluate('  \n'), None)

    def test_unicode(self):
        # All our string expressions are unicode now
        eng = self._makeEngine()
        ec = self._makeContext()
        # XXX: can't do ec.evaluate(u'string:x') directly because ZopeContext
        # only bothers compiling true strings, not unicode strings
        result = ec.evaluate(eng.compile(u'string:x'))
        self.assertEqual(result, u'x')
        self.assertIsInstance(result, text_type)

    def test_mixed(self):
        # 8-bit strings in unicode string expressions cause UnicodeDecodeErrors
        eng = self._makeEngine()
        ec = self._makeContext()
        expr = eng.compile(u'string:$eightbit')
        self.assertRaises(UnicodeDecodeError,
                          ec.evaluate, expr)
        # But registering an appropriate IUnicodeEncodingConflictResolver
        # should fix it
        from zope.component import provideUtility
        from Products.PageTemplates.unicodeconflictresolver \
            import StrictUnicodeEncodingConflictResolver
        from Products.PageTemplates.interfaces \
            import IUnicodeEncodingConflictResolver
        provideUtility(StrictUnicodeEncodingConflictResolver,
                       IUnicodeEncodingConflictResolver)
        self.assertEqual(ec.evaluate(expr), u'äüö')

    def test_builtin_in_path_expr(self):
        ec = self._makeContext()
        self.assertIs(ec.evaluate('True'), True)
        self.assertIs(ec.evaluate('False'), False)
        self.assertIs(ec.evaluate('nocall: test'), safe_builtins["test"])


class UntrustedEngineTests(EngineTestsBase, unittest.TestCase):

    def _makeEngine(self):
        from Products.PageTemplates.Expressions import createZopeEngine
        return createZopeEngine()

    # XXX:  add tests that show security checks being enforced

    def test_open_in_path_expr(self):
        ec = self._makeContext()
        with self.assertRaises(KeyError):
            ec.evaluate("nocall:open")

    def test_list_in_path_expr(self):
        ec = self._makeContext()
        self.assertIs(ec.evaluate('nocall: list'), safe_builtins["list"])

    def test_underscore_traversal(self):
        # Prevent traversal to names starting with an underscore (_)
        ec = self._makeContext()

        with self.assertRaises(NotFound):
            ec.evaluate("context/__class__")

        with self.assertRaises(NotFound):
            ec.evaluate("nocall: random/_itertools/repeat")

        with self.assertRaises(NotFound):
            ec.evaluate("random/_itertools/repeat/foobar")


class TrustedEngineTests(EngineTestsBase, unittest.TestCase):

    def _makeEngine(self):
        from Products.PageTemplates.Expressions import createTrustedZopeEngine
        return createTrustedZopeEngine()

    # XXX:  add tests that show security checks *not* being enforced

    def test_open_in_path_expr(self):
        ec = self._makeContext()
        self.assertIs(ec.evaluate("nocall:open"), open)

    def test_list_in_path_expr(self):
        ec = self._makeContext()
        self.assertIs(ec.evaluate('nocall: list'), list)


class UnicodeEncodingConflictResolverTests(PlacelessSetup, unittest.TestCase):

    def testDefaultResolver(self):
        from zope.component import getUtility
        from zope.component import provideUtility
        from Products.PageTemplates.interfaces \
            import IUnicodeEncodingConflictResolver
        from Products.PageTemplates.unicodeconflictresolver \
            import DefaultUnicodeEncodingConflictResolver
        provideUtility(DefaultUnicodeEncodingConflictResolver,
                       IUnicodeEncodingConflictResolver)
        resolver = getUtility(IUnicodeEncodingConflictResolver)
        self.assertRaises(UnicodeDecodeError,
                          resolver.resolve, None, b'\xe4\xfc\xf6', None)

    def testStrictResolver(self):
        from zope.component import getUtility
        from zope.component import provideUtility
        from Products.PageTemplates.interfaces \
            import IUnicodeEncodingConflictResolver
        from Products.PageTemplates.unicodeconflictresolver \
            import StrictUnicodeEncodingConflictResolver
        provideUtility(StrictUnicodeEncodingConflictResolver,
                       IUnicodeEncodingConflictResolver)
        resolver = getUtility(IUnicodeEncodingConflictResolver)
        text = u'\xe4\xfc\xe4'
        self.assertEqual(resolver.resolve(None, text, None), text)

    def testIgnoringResolver(self):
        from zope.component import getUtility
        from zope.component import provideUtility
        from Products.PageTemplates.interfaces \
            import IUnicodeEncodingConflictResolver
        from Products.PageTemplates.unicodeconflictresolver \
            import IgnoringUnicodeEncodingConflictResolver
        provideUtility(IgnoringUnicodeEncodingConflictResolver,
                       IUnicodeEncodingConflictResolver)
        resolver = getUtility(IUnicodeEncodingConflictResolver)
        self.assertEqual(resolver.resolve(None, b'\xe4\xfc\xf6', None), '')

    def testReplacingResolver(self):
        from zope.component import getUtility
        from zope.component import provideUtility
        from Products.PageTemplates.interfaces \
            import IUnicodeEncodingConflictResolver
        from Products.PageTemplates.unicodeconflictresolver \
            import ReplacingUnicodeEncodingConflictResolver
        provideUtility(ReplacingUnicodeEncodingConflictResolver,
                       IUnicodeEncodingConflictResolver)
        resolver = getUtility(IUnicodeEncodingConflictResolver)
        self.assertEqual(resolver.resolve(None, b'\xe4\xfc\xf6', None),
                         u'\ufffd\ufffd\ufffd')


class ZopeContextTests(unittest.TestCase):

    def _getTargetClass(self):
        from Products.PageTemplates.Expressions import ZopeContext
        return ZopeContext

    def _makeOne(self, engine=None, contexts=None):
        if engine is None:
            engine = self._makeEngine()
        if contexts is None:
            contexts = {}
        return self._getTargetClass()(engine, contexts)

    def _makeEngine(self):
        class DummyEngine(object):
            pass
        return DummyEngine()

    def test_class_conforms_to_ITALExpressionEngine(self):
        from zope.interface.verify import verifyClass
        from zope.tal.interfaces import ITALExpressionEngine
        verifyClass(ITALExpressionEngine, self._getTargetClass())

    def test_instance_conforms_to_ITALExpressionEngine(self):
        from zope.interface.verify import verifyObject
        from zope.tal.interfaces import ITALExpressionEngine
        verifyObject(ITALExpressionEngine, self._makeOne())

    def test_createErrorInfo_returns_unrestricted_object(self):
        # See: https://bugs.launchpad.net/zope2/+bug/174705
        context = self._makeOne()
        info = context.createErrorInfo(AttributeError('nonesuch'), (12, 3))
        self.assertTrue(info.type is AttributeError)
        self.assertEqual(info.__allow_access_to_unprotected_subobjects__, 1)
