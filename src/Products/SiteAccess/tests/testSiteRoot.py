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
        self.failUnless(container.testing is traverser)
        hook = container.__before_traverse__[(100, 'Traverser')]
        self.assertEqual(hook.name, 'testing')

    def test_manage_addToContainer_no_nextUrl(self):
        traverser = self._makeOne()
        container = DummyContainer()
        result = traverser.manage_addToContainer(container)
        self.failUnless(result is None)
        self.failUnless(container.testing is traverser)
        hook = container.__before_traverse__[(100, 'Traverser')]
        self.assertEqual(hook.name, 'testing')

    def test_manage_addToContainer_w_nextUrl_w_name_collision(self):
        NEXTURL='http://example.com/manage_main'
        traverser = self._makeOne()
        container = DummyContainer()
        container.testing = object()
        result = traverser.manage_addToContainer(container, nextURL=NEXTURL)
        self.failUnless(isinstance(result, str))
        self.failUnless('<TITLE>Item Exists</TITLE>' in result)
        self.failIf(container.testing is traverser)

    def test_manage_addToContainer_w_nextUrl_wo_name_collision(self):
        NEXTURL='http://example.com/manage_main'
        traverser = self._makeOne()
        container = DummyContainer()
        result = traverser.manage_addToContainer(container, nextURL=NEXTURL)
        self.failUnless(isinstance(result, str))
        self.failUnless('<TITLE>Item Added</TITLE>' in result)
        self.failUnless(container.testing is traverser)
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
        self.failIf(container.__before_traverse__)

    def test_manage_afterAdd_item_not_self(self):
        traverser = self._makeOne()
        container = DummyContainer()
        item = object()
        traverser.manage_afterAdd(item, container)
        self.failIf('__before_traverse__' in container.__dict__)

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
        unittest.makeSuite(SiteRootRegressions),
    ))
