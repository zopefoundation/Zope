"""SiteRoot regression tests.

These tests verify that the request URL headers, in particular ACTUAL_URL, are
set correctly when a SiteRoot is used.

See http://www.zope.org/Collectors/Zope/2077
"""
import unittest


class TraverserTests(unittest.TestCase):

    def _getTargetClass(self):
        from Products.SiteAccess.SiteRoot import Traverser
        return Traverser

    def _makeOne(self):
        traverser = self._getTargetClass()()
        traverser.id = 'testing'
        return traverser

    def test_addToContainer(self):
        traverser = self._makeOne()
        container = DummyContainer()
        traverser.addToContainer(container)
        self.assertTrue(container.testing is traverser)
        hook = container.__before_traverse__[(100, 'Traverser')]
        self.assertEqual(hook.name, 'testing')

    def test_manage_addToContainer_no_nextUrl(self):
        traverser = self._makeOne()
        container = DummyContainer()
        result = traverser.manage_addToContainer(container)
        self.assertTrue(result is None)
        self.assertTrue(container.testing is traverser)
        hook = container.__before_traverse__[(100, 'Traverser')]
        self.assertEqual(hook.name, 'testing')

    def test_manage_addToContainer_w_nextUrl_w_name_collision(self):
        NEXTURL='http://example.com/manage_main'
        traverser = self._makeOne()
        container = DummyContainer()
        container.testing = object()
        result = traverser.manage_addToContainer(container, nextURL=NEXTURL)
        self.assertTrue('<TITLE>Item Exists</TITLE>' in result)
        self.assertFalse(container.testing is traverser)

    def test_manage_addToContainer_w_nextUrl_wo_name_collision(self):
        NEXTURL='http://example.com/manage_main'
        traverser = self._makeOne()
        container = DummyContainer()
        result = traverser.manage_addToContainer(container, nextURL=NEXTURL)
        self.assertTrue('<TITLE>Item Added</TITLE>' in result)
        self.assertTrue(container.testing is traverser)
        hook = container.__before_traverse__[(100, 'Traverser')]
        self.assertEqual(hook.name, 'testing')

    def test_manage_beforeDelete_item_is_not_self(self):
        from ZPublisher.BeforeTraverse import registerBeforeTraverse
        traverser = self._makeOne()
        container = DummyContainer()
        other = container.other = DummyObject(name='other')
        registerBeforeTraverse(container, other, 'Traverser', 100)
        item = object()
        traverser.manage_beforeDelete(item, container)
        hook = container.__before_traverse__[(100, 'Traverser')]
        self.assertEqual(hook.name, 'other')

    def test_manage_beforeDelete_item_is_self(self):
        from ZPublisher.BeforeTraverse import registerBeforeTraverse
        traverser = self._makeOne()
        container = DummyContainer()
        other = container.other = DummyObject(name='other')
        registerBeforeTraverse(container, other, 'Traverser', 100)
        traverser.manage_beforeDelete(traverser, container)
        self.assertFalse(container.__before_traverse__)

    def test_manage_afterAdd_item_not_self(self):
        traverser = self._makeOne()
        container = DummyContainer()
        item = object()
        traverser.manage_afterAdd(item, container)
        self.assertFalse('__before_traverse__' in container.__dict__)

    def test_manage_afterAdd_item_is_self(self):
        traverser = self._makeOne()
        container = DummyContainer()
        traverser.manage_afterAdd(traverser, container)
        hook = container.__before_traverse__[(100, 'Traverser')]
        self.assertEqual(hook.name, 'testing')

    def test__setId_same(self):
        traverser = self._makeOne()
        traverser._setId('testing') # doesn't raise

    def test__setId_different(self):
        traverser = self._makeOne()
        self.assertRaises(ValueError, traverser._setId, 'other')


class SiteRootTests(unittest.TestCase):

    _old_SSR = None

    def setUp(self):
        from Testing.ZopeTestCase import ZopeLite
        ZopeLite.startup()

    def tearDown(self):
        if self._old_SSR is not None:
            self._set_SUPPRESS_SITEROOT(self._old_SSR)

    def _set_SUPPRESS_SITEROOT(self, value):
        from Products.SiteAccess import SiteRoot as SR
        (self._old_SSR,
         SR.SUPPRESS_SITEROOT) = (SR.SUPPRESS_SITEROOT, value)

    def _getTargetClass(self):
        from Products.SiteAccess.SiteRoot import SiteRoot
        return SiteRoot

    def _makeOne(self, title='TITLE', base='', path=''):
        return self._getTargetClass()(title, base, path)

    def test___init___strips_base_and_path(self):
        siteroot = self._makeOne(base=' ', path=' ')
        self.assertEqual(siteroot.title, 'TITLE')
        self.assertEqual(siteroot.base, '')
        self.assertEqual(siteroot.path, '')

    def test___init___w_base_and_path(self):
        siteroot = self._makeOne(base='http://example.com', path='/path')
        self.assertEqual(siteroot.title, 'TITLE')
        self.assertEqual(siteroot.base, 'http://example.com')
        self.assertEqual(siteroot.path, '/path')

    def test_manage_edit_no_REQUEST(self):
        siteroot = self._makeOne(title='Before',
                                 base='http://before.example.com',
                                 path='/before')
        result = siteroot.manage_edit('After', 'http://after.example.com ',
                                      '/after ')
        self.assertTrue(result is None)
        self.assertEqual(siteroot.title, 'After')
        self.assertEqual(siteroot.base, 'http://after.example.com')
        self.assertEqual(siteroot.path, '/after')

    def test_manage_edit_w_REQUEST(self):
        siteroot = self._makeOne(title='Before',
                                 base='http://before.example.com',
                                 path='/before')
        result = siteroot.manage_edit('After', 'http://after.example.com ',
                                      '/after ',
                                      REQUEST = {'URL1':
                                        'http://localhost:8080/manage_main'})
        self.assertTrue('<TITLE>SiteRoot changed.</TITLE>' in result)
        self.assertEqual(siteroot.title, 'After')
        self.assertEqual(siteroot.base, 'http://after.example.com')
        self.assertEqual(siteroot.path, '/after')

    def test___call___w_SUPPRESS_SITEROOT_set(self):
        self._set_SUPPRESS_SITEROOT(1)
        siteroot = self._makeOne(base='http://example.com', path='/path')
        request = {}
        siteroot(None, request)
        self.assertEqual(request, {})

    def test___call___w_SUPPRESS_SITEROOT_in_URL(self):
        # This behavior changed in landing lp:142878.
        URL='http://localhost:8080/example/folder/'
        siteroot = self._makeOne(base='http://example.com', path='/example')
        request = DummyRequest(TraversalRequestNameStack=
                                    ['_SUPPRESS_SITEROOT'],
                               URL=URL,
                               ACTUAL_URL=URL,
                               SERVER_URL='http://localhost:8080',
                              )
        request.steps = []
        request.environ = {}
        siteroot(None, request)
        self.assertEqual(request['URL'], URL)
        self.assertEqual(request['SERVER_URL'], 'http://example.com')
        self.assertEqual(request['ACTUAL_URL'], 
                         'http://example.com/example/folder/')
        self.assertEqual(request._virtual_root, '/example')
        self.assertTrue(request._urls_reset)

    def test___call___wo_SUPPRESS_SITEROOT_w_base_wo_path(self):
        URL='http://localhost:8080/example/folder/'
        siteroot = self._makeOne(base='http://example.com', path='')
        request = DummyRequest(TraversalRequestNameStack=[],
                               URL=URL,
                               ACTUAL_URL=URL,
                               SERVER_URL='http://localhost:8080',
                              )
        request.steps = []
        request.environ = {}
        siteroot(None, request)
        self.assertEqual(request['URL'], URL)
        self.assertEqual(request['SERVER_URL'], 'http://example.com')
        self.assertEqual(request['ACTUAL_URL'],
                         'http://example.com/example/folder/')
        self.assertEqual(request._virtual_root, None)
        self.assertTrue(request._urls_reset)

    def test___call___wo_SUPPRESS_SITEROOT_wo_base_w_path(self):
        URL='http://localhost:8080/example/folder/'
        siteroot = self._makeOne(base='', path='/example')
        request = DummyRequest(TraversalRequestNameStack=[],
                               URL=URL,
                               ACTUAL_URL=URL,
                               SERVER_URL='http://localhost:8080',
                              )
        request.steps = []
        request.environ = {}
        siteroot(None, request)
        self.assertEqual(request['URL'], URL)
        self.assertEqual(request['SERVER_URL'], 'http://localhost:8080')
        self.assertEqual(request['ACTUAL_URL'], URL)
        self.assertEqual(request._virtual_root, '/example')
        self.assertFalse(request._urls_reset)

    def test___call___wo_SUPPRESS_SITEROOT_w_base_w_path(self):
        URL='http://localhost:8080/example/folder/'
        siteroot = self._makeOne(base='http://example.com', path='/example')
        request = DummyRequest(TraversalRequestNameStack=[],
                               URL=URL,
                               ACTUAL_URL=URL,
                               SERVER_URL='http://localhost:8080',
                              )
        request.steps = []
        request.environ = {}
        siteroot(None, request)
        self.assertEqual(request['URL'], URL)
        self.assertEqual(request['SERVER_URL'], 'http://example.com')
        self.assertEqual(request['ACTUAL_URL'], 
                         'http://example.com/example/folder/')
        self.assertEqual(request._virtual_root, '/example')
        self.assertTrue(request._urls_reset)

    def test_get_size(self):
        siteroot = self._makeOne()
        self.assertEqual(siteroot.get_size(), 0)


class DummyObject(object):

    def __init__(self, **kw):
        self.__dict__.update(kw)


class DummyContainer(object):

    def __init__(self, **kw):
        self.__dict__.update(kw)

    def _setObject(self, name, object):
        setattr(self, name, object)

    def this(self):
        return self


class DummyRequest(dict):

    _virtual_root = None
    _urls_reset = False

    def setVirtualRoot(self, root):
        self._virtual_root = root

    def _resetURLS(self):
        self._urls_reset = True


class SiteRootRegressions(unittest.TestCase):

    def setUp(self):
        import transaction
        from Testing.makerequest import makerequest
        from Testing.ZopeTestCase.ZopeLite import app
        transaction.begin()
        self.app = makerequest(app())
        self.app.manage_addFolder('folder')
        p_disp = self.app.folder.manage_addProduct['SiteAccess']
        p_disp.manage_addSiteRoot(title='SiteRoot',
                                    base='http://test_base',
                                    path='/test_path')
        self.app.REQUEST.set('PARENTS', [self.app])
        self.app.REQUEST.traverse('/folder')

    def tearDown(self):
        import transaction
        transaction.abort()
        self.app._p_jar.close()
        
    def testRequest(self):
        self.assertEqual(self.app.REQUEST['SERVER_URL'], 'http://test_base') 
        self.assertEqual(self.app.REQUEST['URL'],
                         'http://test_base/test_path/index_html')
        self.assertEqual(self.app.REQUEST['ACTUAL_URL'],
                         'http://test_base/test_path')
    def testAbsoluteUrl(self):            
        self.assertEqual(self.app.folder.absolute_url(),
                         'http://test_base/test_path')

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(TraverserTests),
        unittest.makeSuite(SiteRootTests),
        unittest.makeSuite(SiteRootRegressions),
    ))
