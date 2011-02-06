import unittest

class ViewMixinForTemplatesTests(unittest.TestCase):

    def _getTargetClass(self):
        from Products.Five.browser.metaconfigure import ViewMixinForTemplates
        return ViewMixinForTemplates

    def _makeOne(self, context=None, request=None):
        if context is None:
            context = DummyContext()
        if request is None:
            request = DummyRequest()
        return self._getTargetClass()(context, request)

    def test_class_conforms_to_IBrowserPublisher(self):
        from zope.interface.verify import verifyClass
        from zope.publisher.interfaces.browser import IBrowserPublisher
        verifyClass(IBrowserPublisher, self._getTargetClass())

    def test_browserDefault(self):
        request = DummyRequest()
        view = self._makeOne(request=request)
        self.assertEqual(view.browserDefault(request), (view, ()))

    def test_publishTraverse_not_index_raises_NotFound(self):
        from zope.publisher.interfaces import NotFound
        request = DummyRequest()
        view = self._makeOne(request=request)
        self.assertRaises(NotFound, view.publishTraverse, request, 'nonesuch')

    def test_publishTraverse_w_index_returns_index(self):
        request = DummyRequest()
        view = self._makeOne(request=request)
        index = view.index = DummyTemplate()
        self.failUnless(view.publishTraverse(request, 'index.html') is index)

    def test___getitem___uses_index_macros(self):
        view = self._makeOne()
        view.index = index = DummyTemplate()
        index.macros = {}
        index.macros['aaa'] = aaa = object()
        self.failUnless(view['aaa'] is aaa)
    
    def test__getitem__gives_shortcut_to_index_macros(self):
        view = self._makeOne()
        view.index = index = DummyTemplate()
        index.macros = {}
        self.failUnless(view['macros'] is index.macros)

    def test___call___no_args_no_kw(self):
        view = self._makeOne()
        view.index = index = DummyTemplate()
        result = view()
        self.failUnless(result is index)
        self.assertEqual(index._called_with, ((), {}))

    def test___call___w_args_no_kw(self):
        view = self._makeOne()
        view.index = index = DummyTemplate()
        result = view('abc')
        self.failUnless(result is index)
        self.assertEqual(index._called_with, (('abc',), {}))

    def test___call___no_args_w_kw(self):
        view = self._makeOne()
        view.index = index = DummyTemplate()
        result = view(foo='bar')
        self.failUnless(result is index)
        self.assertEqual(index._called_with, ((), {'foo': 'bar'}))

    def test___call___w_args_w_kw(self):
        view = self._makeOne()
        view.index = index = DummyTemplate()
        result = view('abc', foo='bar')
        self.failUnless(result is index)
        self.assertEqual(index._called_with, (('abc',), {'foo': 'bar'}))


class DummyContext:
    pass

class DummyRequest:
    pass

class DummyTemplate:
    def __call__(self, *args, **kw):
        self._called_with = (args, kw)
        return self

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(ViewMixinForTemplatesTests),
    ))
