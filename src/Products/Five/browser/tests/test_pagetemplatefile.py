import unittest

class ViewPageTemplateFileTests(unittest.TestCase):

    def setUp(self):
        from AccessControl.SecurityManagement import noSecurityManager
        noSecurityManager()

    def tearDown(self):
        from AccessControl.SecurityManagement import noSecurityManager
        noSecurityManager()

    def _getTargetClass(self):
        from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
        return ViewPageTemplateFile

    def _makeOne(self, filename, _prefix=None, content_type=None):
        return self._getTargetClass()(filename, _prefix, content_type)

    def _makeView(self, context=None, request=None):
        if context is None:
            context = DummyContext()
        if request is None:
            request = DummyRequest()
        return DummyView(context, request)

    def test_getId_simple_name(self):
        vptf = self._makeOne('seagull.pt')
        self.assertEqual(vptf.getId(), 'seagull.pt')
        self.assertEqual(vptf.id, 'seagull.pt')

    def test_getId_with_path(self):
        vptf = self._makeOne('templates/dirpage1.pt')
        self.assertEqual(vptf.id, 'dirpage1.pt')

    def test_pt_getEngine(self):
        from zope.tales.expressions import DeferExpr
        from zope.tales.expressions import NotExpr
        from zope.tales.expressions import PathExpr
        from zope.tales.expressions import Undefs
        from zope.tales.pythonexpr import PythonExpr
        from zope.contentprovider.tales import TALESProviderExpression
        from Products.PageTemplates.DeferExpr import LazyExpr
        from Products.PageTemplates.Expressions import TrustedZopePathExpr
        from Products.PageTemplates.Expressions import SecureModuleImporter
        from Products.PageTemplates.Expressions import UnicodeAwareStringExpr

        vptf = self._makeOne('seagull.pt')
        engine = vptf.pt_getEngine()
        self.assertEqual(engine.types['standard'], TrustedZopePathExpr)
        self.assertEqual(engine.types['path'], TrustedZopePathExpr)
        self.assertEqual(engine.types['exists'], TrustedZopePathExpr)
        self.assertEqual(engine.types['nocall'], TrustedZopePathExpr)
        self.assertEqual(engine.types['string'], UnicodeAwareStringExpr)
        self.assertEqual(engine.types['python'], PythonExpr)
        self.assertEqual(engine.types['not'], NotExpr)
        self.assertEqual(engine.types['defer'], DeferExpr)
        self.assertEqual(engine.types['lazy'], LazyExpr)
        self.assertEqual(engine.types['provider'], TALESProviderExpression)
        self.assertEqual(engine.base_names['modules'], SecureModuleImporter)

    def test_pt_getContext_no_kw_no_physicalRoot(self):
        from Products.Five.browser.pagetemplatefile import ViewMapper
        from Products.PageTemplates.Expressions import SecureModuleImporter
        from AccessControl.SecurityManagement import newSecurityManager
        newSecurityManager(None, DummyUser('a_user'))
        context = DummyContext()
        request = DummyRequest()
        view = self._makeView(context, request)
        vptf = self._makeOne('seagull.pt')
        namespace = vptf.pt_getContext(view, request)
        self.assertTrue(namespace['context'] is context)
        self.assertTrue(namespace['request'] is request)
        views = namespace['views']
        self.assertTrue(isinstance(views, ViewMapper))
        self.assertEqual(views.ob, context)
        self.assertEqual(views.request, request)
        self.assertTrue(namespace['here'] is context)
        self.assertTrue(namespace['container'] is context)
        self.assertTrue(namespace['root'] is None)
        modules = namespace['modules']
        self.assertTrue(modules is SecureModuleImporter)
        self.assertEqual(namespace['traverse_subpath'], [])
        self.assertEqual(namespace['user'].getId(), 'a_user')

    def test_pt_getContext_w_physicalRoot(self):
        from Products.Five.browser.pagetemplatefile import ViewMapper
        from Products.PageTemplates.Expressions import SecureModuleImporter
        from AccessControl.SecurityManagement import newSecurityManager
        newSecurityManager(None, DummyUser('a_user'))
        context = DummyContext()
        root = DummyContext()
        context.getPhysicalRoot = lambda: root
        request = DummyRequest()
        view = self._makeView(context, request)
        vptf = self._makeOne('seagull.pt')
        namespace = vptf.pt_getContext(view, request)
        self.assertTrue(namespace['root'] is root)

    def test_pt_getContext_w_ignored_kw(self):
        from Products.Five.browser.pagetemplatefile import ViewMapper
        from Products.PageTemplates.Expressions import SecureModuleImporter
        from AccessControl.SecurityManagement import newSecurityManager
        newSecurityManager(None, DummyUser('a_user'))
        context = DummyContext()
        request = DummyRequest()
        view = self._makeView(context, request)
        vptf = self._makeOne('seagull.pt')
        namespace = vptf.pt_getContext(view, request, foo='bar')
        self.assertFalse('foo' in namespace)
        self.assertFalse('foo' in namespace['options'])

    def test_pt_getContext_w_args_kw(self):
        from Products.Five.browser.pagetemplatefile import ViewMapper
        from Products.PageTemplates.Expressions import SecureModuleImporter
        from AccessControl.SecurityManagement import newSecurityManager
        newSecurityManager(None, DummyUser('a_user'))
        context = DummyContext()
        request = DummyRequest()
        view = self._makeView(context, request)
        vptf = self._makeOne('seagull.pt')
        namespace = vptf.pt_getContext(view, request, args=('bar', 'baz'))
        self.assertEqual(namespace['args'], ('bar', 'baz'))

    def test_pt_getContext_w_options_kw(self):
        from Products.Five.browser.pagetemplatefile import ViewMapper
        from Products.PageTemplates.Expressions import SecureModuleImporter
        from AccessControl.SecurityManagement import newSecurityManager
        newSecurityManager(None, DummyUser('a_user'))
        context = DummyContext()
        request = DummyRequest()
        view = self._makeView(context, request)
        vptf = self._makeOne('seagull.pt')
        namespace = vptf.pt_getContext(view, request, options={'bar': 'baz'})
        self.assertEqual(namespace['options'], {'bar': 'baz'})

    def test___call___no_previous_content_type(self):
        context = DummyContext()
        request = DummyRequest()
        response = request.response = DummyResponse()
        view = self._makeView(context, request)
        vptf = self._makeOne('templates/dirpage1.pt')
        body = vptf(view)
        self.assertEqual(body, DIRPAGE1)
        self.assertEqual(response._headers['Content-Type'], 'text/html')

    def test___call___w_previous_content_type(self):
        context = DummyContext()
        request = DummyRequest()
        response = request.response = DummyResponse(
                                        {'Content-Type': 'text/xhtml'})
        view = self._makeView(context, request)
        vptf = self._makeOne('templates/dirpage1.pt')
        body = vptf(view)
        self.assertEqual(response._headers['Content-Type'], 'text/xhtml')

    def test___get___(self):
        from Products.Five.browser.pagetemplatefile import BoundPageTemplate
        template = self._makeOne('templates/dirpage1.pt')
        class Foo:
            def __init__(self, context, request):
                self.context = context
                self.request = request
            bar = template
        context = DummyContext()
        request = DummyRequest()
        foo = Foo(context, request)
        bound = foo.bar
        self.assertTrue(isinstance(bound, BoundPageTemplate))
        self.assertTrue(bound.im_func is template)
        self.assertTrue(bound.im_self is foo)

class ViewMapperTests(unittest.TestCase):

    def setUp(self):
        from zope.component.testing import setUp
        setUp()

    def tearDown(self):
        from zope.component.testing import tearDown
        tearDown()

    def _getTargetClass(self):
        from Products.Five.browser.pagetemplatefile import ViewMapper
        return ViewMapper

    def _makeOne(self, ob=None, request=None):
        if ob is None:
            ob = DummyContext()
        if request is None:
            request = DummyRequest()
        return self._getTargetClass()(ob, request)

    def test___getitem___miss(self):
        from zope.component import ComponentLookupError
        mapper = self._makeOne()
        self.assertRaises(ComponentLookupError, mapper.__getitem__, 'nonesuch')

    def test___getitem___hit(self):
        from zope.interface import Interface
        from zope.component import provideAdapter
        def _adapt(context, request):
            return self
        provideAdapter(_adapt, (None, None), Interface, name='test')
        mapper = self._makeOne()
        self.assertTrue(mapper['test'] is self)

_marker = object()

class BoundPageTemplateTests(unittest.TestCase):

    def _getTargetClass(self):
        from Products.Five.browser.pagetemplatefile import BoundPageTemplate
        return BoundPageTemplate

    def _makeOne(self, pt=_marker, ob=_marker):
        if pt is _marker:
            pt = DummyTemplate()
        if ob is _marker:
            ob = DummyContext()
        return self._getTargetClass()(pt, ob)

    def test___init__(self):
        pt = DummyTemplate({'foo': 'bar'})
        ob = DummyContext()
        bpt = self._makeOne(pt, ob)
        self.assertTrue(bpt.im_func is pt)
        self.assertTrue(bpt.im_self is ob)
        self.assertTrue(bpt.__parent__ is ob)
        self.assertEqual(bpt.macros['foo'], 'bar')
        self.assertEqual(bpt.filename, 'dummy.pt')

    def test___setattr___raises(self):
        bpt = self._makeOne()
        try:
            bpt.foo = 'bar'
        except AttributeError:
            pass
        else:
            self.fail('Attribute assigned')

    def test___call___w_real_im_self_no_args_no_kw(self):
        pt = DummyTemplate()
        ob = DummyContext()
        bpt = self._makeOne(pt, ob)
        rendered = bpt()
        self.assertEqual(rendered, '<h1>Dummy</h1>')
        self.assertEqual(pt._called_with, (ob, (), {}))

    def test___call___w_real_im_self_w_args_w_kw(self):
        pt = DummyTemplate()
        ob = DummyContext()
        bpt = self._makeOne(pt, ob)
        rendered = bpt('abc', foo='bar')
        self.assertEqual(rendered, '<h1>Dummy</h1>')
        self.assertEqual(pt._called_with, (ob, ('abc',), {'foo': 'bar'}))

    def test___call___wo_real_im_self_w_args_w_kw(self):
        pt = DummyTemplate()
        bpt = self._makeOne(pt, None)
        rendered = bpt('abc', 'def', foo='bar')
        self.assertEqual(rendered, '<h1>Dummy</h1>')
        self.assertEqual(pt._called_with, ('abc', ('def',), {'foo': 'bar'}))

DIRPAGE1 = """\
<html>
<p>This is page 1</p>
</html>
"""

class DummyContext:
    pass

class DummyRequest:
    debug = object()

class DummyResponse:
    def __init__(self, headers=None):
        if headers is None:
            headers = {}
        self._headers = headers

    def getHeader(self, name):
        return self._headers.get(name)

    def setHeader(self, name, value):
        self._headers[name] = value

class DummyTemplate:
    filename = 'dummy.pt'
    def __init__(self, macros=None):
        if macros is None:
            macros = {}
        self.macros = macros
    def __call__(self, im_self, *args, **kw):
        self._called_with = (im_self, args, kw)
        return '<h1>Dummy</h1>'

class DummyView:
    def __init__(self, context, request):
        self.context = context
        self.request = request

class DummyUser:
    def __init__(self, name):
        self._name = name
    def getId(self):
        return self._name

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(ViewPageTemplateFileTests),
        unittest.makeSuite(ViewMapperTests),
        unittest.makeSuite(BoundPageTemplateTests),
    ))
