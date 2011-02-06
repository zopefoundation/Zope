import unittest

from zope.interface import implements
from zope.publisher.interfaces import IPublishTraverse
from zope.publisher.interfaces import NotFound as ztkNotFound


class DummyTraverser(object):

    implements(IPublishTraverse)

    def publishTraverse(self, request, name):
        if name == 'dummy':
            return 'dummy object'
        raise ztkNotFound(self, name)


class BaseRequest_factory:

    def _makeOne(self, root):
        from Acquisition import Implicit

        class DummyResponse(Implicit):

            base = ''
            status = None
            debug_mode = False

            def setStatus(self, code):
                self.status = code

            def setBase(self, base):
                if base is None:
                    base = ''
                elif not base.endswith('/'):
                    base = base+'/'
                self.base = str(base)

            def notFoundError(self, name):
                from zExceptions import NotFound
                raise NotFound(name)

            # Real responses raise NotFound, to avoid information disclosure
            #def forbiddenError(self, name):
            #    from zExceptions import Forbidden
            #    raise Forbidden(name)
            forbiddenError = notFoundError

        response = DummyResponse()
        environment = { 'URL': '',
                        'PARENTS': [root],
                        'steps': [],
                        '_hacked_path': 0,
                        '_test_counter': 0,
                        'response': response }
        return self._getTargetClass()(environment)

    def _makeBasicObjectClass(self):
        from Acquisition import Implicit

        class DummyObjectBasic(Implicit):
            """Dummy class with docstring."""

            def _setObject(self, id, object):
                setattr(self, id, object)
                return getattr(self, id)

            def view(self):
                """Attribute with docstring."""
                return 'view content'

            def noview(self):
                # Attribute without docstring.
                return 'unpublishable'

        return DummyObjectBasic

    def _makeBasicObject(self):
        return self._makeBasicObjectClass()()

    def _makeObjectWithDefault(self):

        class DummyObjectWithDefault(self._makeBasicObjectClass()):
            """Dummy class with docstring."""

            def index_html(self):
                """Attribute with docstring."""
                return 'index_html content'

        return DummyObjectWithDefault()

    def _makeObjectWithDefaultNone(self):

        class DummyObjectWithDefaultNone(self._makeBasicObjectClass()):
            """Dummy class with docstring."""

            index_html = None

        return DummyObjectWithDefaultNone()

    def _makeObjectWithBPTH(self):

        class DummyObjectWithBPTH(self._makeBasicObjectClass()):
            """Dummy class with __before_publishing_traverse__."""

            def __before_publishing_traverse__(self, object, REQUEST):
                if REQUEST['_test_counter'] < 100:
                    REQUEST['_test_counter'] += 1
                else:
                    raise RuntimeError('Infinite loop detected.')
                REQUEST['TraversalRequestNameStack'] += self._path
                REQUEST._hacked_path=1

        return DummyObjectWithBPTH()

    def _makeObjectWithBD(self):
        class DummyObjectWithBD(self._makeBasicObjectClass()):
            """Dummy class with __browser_default__."""
            def __browser_default__(self, REQUEST):
                if REQUEST['_test_counter'] < 100:
                    REQUEST['_test_counter'] += 1
                else:
                    raise RuntimeError('Infinite loop detected.')
                return self, self._default_path
        return DummyObjectWithBD()

    def _makeObjectWithBBT(self):
        from ZPublisher.interfaces import UseTraversalDefault

        class _DummyResult(object):
            ''' '''
            def __init__(self, tag):
                self.tag = tag

        class DummyObjectWithBBT(self._makeBasicObjectClass()):
            """ Dummy class with __bobo_traverse__
            """
            default = _DummyResult('Default')

            def __bobo_traverse__(self, REQUEST, name):
                if name == 'normal':
                    return _DummyResult('Normal')
                elif name == 'default':
                    raise UseTraversalDefault
                raise AttributeError(name)
        return DummyObjectWithBBT()

    def _makeObjectWithBDBBT(self):
        class DummyObjectWithBDBBT(self._makeBasicObjectClass()):
            """Dummy class with __browser_default__."""
            def __browser_default__(self, REQUEST):
                if REQUEST['_test_counter'] < 100:
                    REQUEST['_test_counter'] += 1
                else:
                    raise RuntimeError('Infinite loop detected.')
                return self, self._default_path
            def __bobo_traverse__(self, REQUEST, name):
                if name == self._default_path[0]:
                    return getattr(self, name)
                raise AttributeError, name
        return DummyObjectWithBDBBT()

    def _makeObjectWithEmptyDocstring(self):
        from Acquisition import Implicit

        class DummyObjectWithEmptyDocstring(Implicit):
            ""
            def view(self):
                """Attribute with docstring."""
                return 'view content'

            def noview(self):
                # Attribute without docstring.
                return 'unpublishable'
        return DummyObjectWithEmptyDocstring()


class TestBaseRequest(unittest.TestCase, BaseRequest_factory):

    def _getTargetClass(self):
        from ZPublisher.BaseRequest import BaseRequest
        return BaseRequest

    def _makeRootAndFolder(self):
        root = self._makeBasicObject()
        folder = root._setObject('folder', self._makeBasicObject())
        return root, folder

    def test_traverse_basic(self):
        root, folder = self._makeRootAndFolder()
        folder._setObject('objBasic', self._makeBasicObject())
        r = self._makeOne(root)
        r.traverse('folder/objBasic')
        self.assertEqual(r.URL, '/folder/objBasic')
        self.assertEqual(r.response.base, '')

    def test_traverse_withDefault(self):
        root, folder = self._makeRootAndFolder()
        folder._setObject('objWithDefault', self._makeObjectWithDefault())
        r = self._makeOne(root)
        r.traverse('folder/objWithDefault')
        self.assertEqual(r.URL, '/folder/objWithDefault/index_html')
        self.assertEqual(r.response.base, '/folder/objWithDefault/')

    def test_traverse_withDefaultNone(self):
        root, folder = self._makeRootAndFolder()
        folder._setObject('objWithDefaultNone',
                          self._makeObjectWithDefaultNone())
        r = self._makeOne(root)
        r.traverse('folder/objWithDefaultNone')
        self.assertEqual(r.URL, '/folder/objWithDefaultNone')
        self.assertEqual(r.response.base, '')

    def test_traverse_withBPTH(self):
        root, folder = self._makeRootAndFolder()
        folder._setObject('objWithBPTH', self._makeObjectWithBPTH())
        folder.objWithBPTH._path = ['view']
        r = self._makeOne(root)
        r.traverse('folder/objWithBPTH')
        self.assertEqual(r.URL, '/folder/objWithBPTH/view')
        self.assertEqual(r.response.base, '/folder/objWithBPTH/')

    def test_traverse_withBDView(self):
        root, folder = self._makeRootAndFolder()
        folder._setObject('objWithBD', self._makeObjectWithBD())
        folder.objWithBD._default_path = ['view']
        r = self._makeOne(root)
        r.traverse('folder/objWithBD')
        self.assertEqual(r.URL, '/folder/objWithBD/view')
        self.assertEqual(r.response.base, '/folder/objWithBD/')

    def test_traverse_withAcquisition(self):
        root, folder = self._makeRootAndFolder()
        folder._setObject('objWithBPTH', self._makeObjectWithBPTH())
        folder.objWithBPTH._path = ['view']
        folder._setObject('objWithBD', self._makeObjectWithBD())
        folder.objWithBD._default_path = ['view']
        r = self._makeOne(root)
        r.traverse('folder/objWithBD/objWithBPTH')
        self.assertEqual(r.URL, '/folder/objWithBD/objWithBPTH/view')
        self.assertEqual(r.response.base, '/folder/objWithBD/objWithBPTH/')

    def test_traverse_withBDAndBPTH(self):
        # Collector 1079 (infinite loop 1)
        root, folder = self._makeRootAndFolder()
        folder._setObject('objBasic', self._makeBasicObject())
        folder._setObject('objWithBPTH', self._makeObjectWithBPTH())
        folder.objWithBPTH._path = ['objBasic']
        folder._setObject('objWithBD', self._makeObjectWithBD())
        folder.objWithBD._default_path = ['objWithBPTH']
        r = self._makeOne(root)
        r.traverse('folder/objWithBD')
        self.assertEqual(r.URL, '/folder/objWithBD/objWithBPTH/objBasic')
        self.assertEqual(r.response.base, '/folder/objWithBD/objWithBPTH/')

    def test_traverse_withBDEmpty(self):
        # Collector 1079 (infinite loop 2)
        from ZPublisher import NotFound
        root, folder = self._makeRootAndFolder()
        folder._setObject('objWithBD', self._makeObjectWithBD())
        folder.objWithBD._default_path = ['']
        r = self._makeOne(root)
        self.assertRaises(NotFound, r.traverse, 'folder/objWithBD')

    def test_traverse_withBBT_handles_AttributeError(self):
        # Test that if __bobo_traverse__ raises AttributeError
        # that we get a NotFound
        from ZPublisher import NotFound
        root, folder = self._makeRootAndFolder()
        def _faux___bobo_traverse__(REQUEST, name):
            raise AttributeError, name
        obj = self._makeBasicObject()
        obj.__bobo_traverse__ = _faux___bobo_traverse__
        folder._setObject('objWithBBT', obj)
        r = self._makeOne(root)
        self.assertRaises(NotFound, r.traverse,
                              'folder/objWithBBT/bbt_foo')

    def test_traverse_UseTraversalDefault(self):
        root, folder = self._makeRootAndFolder()
        folder._setObject('objWithBBT', self._makeObjectWithBBT())
        # test non default usage
        r = self._makeOne(root)
        self.assertEqual(r.traverse('folder/objWithBBT/normal').tag, 'Normal')
        # test default usage
        r = self._makeOne(root)
        self.assertEqual(r.traverse('folder/objWithBBT/default').tag, 'Default')

    def test_traverse_withBDBBT(self):
        # Test for an object which has a __browser_default__
        # and __bobo_traverse__
        # __bobo_traverse__ should return the object
        # pointed by __browser_default__
        root, folder = self._makeRootAndFolder()
        folder._setObject('objWithBDBBT', self._makeObjectWithBDBBT())
        folder.objWithBDBBT._default_path = ['view']
        r = self._makeOne(root)
        r.traverse('folder/objWithBDBBT')
        self.assertEqual(r.URL, '/folder/objWithBDBBT/view')
        self.assertEqual(r.response.base, '/folder/objWithBDBBT/')

    def test_traverse_withBDBBT_NotFound(self):
        # Test for an object which has a __browser_default__
        # and __bobo_traverse__
        # __bobo_traverse__ should raise an AttributeError, which will
        # raise a NotFound
        from ZPublisher import NotFound
        root, folder = self._makeRootAndFolder()
        folder._setObject('objWithBDBBT', self._makeObjectWithBDBBT())
        folder.objWithBDBBT._default_path = ['xxx']
        r = self._makeOne(root)
        self.assertRaises(NotFound, r.traverse, 'folder/objWithBDBBT')

    def test_traverse_slash(self):
        root, folder = self._makeRootAndFolder()
        folder._setObject('objWithDefault', self._makeObjectWithDefault())
        r = self._makeOne(root)
        r['PARENTS'] = [folder.objWithDefault]
        r.traverse('/')
        self.assertEqual(r.URL, '/index_html')
        self.assertEqual(r.response.base, '')

    def test_traverse_attribute_with_docstring(self):
        root, folder = self._makeRootAndFolder()
        folder._setObject('objBasic', self._makeBasicObject())
        r = self._makeOne(root)
        r.traverse('folder/objBasic/view')
        self.assertEqual(r.URL, '/folder/objBasic/view')
        self.assertEqual(r.response.base, '')

    def test_traverse_attribute_without_docstring(self):
        from ZPublisher import NotFound
        root, folder = self._makeRootAndFolder()
        folder._setObject('objBasic', self._makeBasicObject())
        r = self._makeOne(root)
        self.assertRaises(NotFound, r.traverse, 'folder/objBasic/noview')

    def test_traverse_acquired_attribute_without_docstring(self):
        from ZPublisher import NotFound
        root, folder = self._makeRootAndFolder()
        root._setObject('objBasic',
                        self._makeObjectWithEmptyDocstring())
        r = self._makeOne(root)
        self.assertRaises(NotFound, r.traverse, 'folder/objBasic')

    def test_traverse_class_without_docstring(self):
        from ZPublisher import NotFound
        root, folder = self._makeRootAndFolder()
        folder._setObject('objWithoutDocstring', 
                          self._makeObjectWithEmptyDocstring())
        r = self._makeOne(root)
        self.assertRaises(NotFound, r.traverse, 'folder/objWithoutDocstring')

    def test_traverse_attribute_of_class_without_docstring(self):
        from ZPublisher import NotFound
        root, folder = self._makeRootAndFolder()
        folder._setObject('objWithoutDocstring', 
                          self._makeObjectWithEmptyDocstring())
        r = self._makeOne(root)
        self.assertRaises(NotFound, r.traverse,
                              'folder/objWithoutDocstring/view')

    def test_traverse_attribute_and_class_without_docstring(self):
        from ZPublisher import NotFound
        root, folder = self._makeRootAndFolder()
        r = self._makeOne(root)
        folder._setObject('objWithoutDocstring', 
                          self._makeObjectWithEmptyDocstring())
        self.assertRaises(NotFound, r.traverse,
                              'folder/objWithoutDocstring/noview')

    def test_traverse_simple_string(self):
        from ZPublisher import NotFound
        root, folder = self._makeRootAndFolder()
        folder.simpleString = 'foo'
        r = self._makeOne(root)
        self.assertRaises(NotFound, r.traverse, 'folder/simpleString')

    def test_traverse_simple_list(self):
        from ZPublisher import NotFound
        root, folder = self._makeRootAndFolder()
        folder.simpleList = []
        r = self._makeOne(root)
        self.assertRaises(NotFound, r.traverse, 'folder/simpleList')

    def test_traverse_simple_boolean(self):
        from ZPublisher import NotFound
        root, folder = self._makeRootAndFolder()
        folder.simpleBoolean = True
        r = self._makeOne(root)
        self.assertRaises(NotFound, r.traverse, 'folder/simpleBoolean')

    def test_traverse_simple_complex(self):
        from ZPublisher import NotFound
        root, folder = self._makeRootAndFolder()
        folder.simpleComplex = complex(1)
        folder.simpleString = 'foo'
        r = self._makeOne(root)
        self.assertRaises(NotFound, r.traverse, 'folder/simpleComplex')

    def test_traverse_simple_set(self):
        from ZPublisher import NotFound
        root, folder = self._makeRootAndFolder()
        folder.simpleSet = set([])
        r = self._makeOne(root)
        self.assertRaises(NotFound, r.traverse, 'folder/simpleSet')

    def test_traverse_simple_frozen_set(self):
        from ZPublisher import NotFound
        root, folder = self._makeRootAndFolder()
        folder.simpleFrozenSet = frozenset([])
        r = self._makeOne(root)
        self.assertRaises(NotFound, r.traverse, 'folder/simpleFrozenSet')

    def test_hold_after_close(self):
        # Request should no longer accept holds after it has been closed
        root, folder = self._makeRootAndFolder()
        r = self._makeOne(root)
        r._hold(lambda x: None)
        self.assertEqual(len(r._held), 1)
        r.close()
        # No more holding from now on
        self.assertEqual(r._held, None)
        r._hold(lambda x: None)
        self.assertEqual(r._held, None)

    def test_traverse_unsubscriptable(self):
        # See https://bugs.launchpad.net/bugs/213311
        from ZPublisher import NotFound
        r = self._makeOne(None)
        self.assertRaises(NotFound, r.traverse, 'not_found')

    def test_traverse_publishTraverse(self):
        r = self._makeOne(DummyTraverser())
        self.assertEqual(r.traverse('dummy'), 'dummy object')

    def test_traverse_publishTraverse_error(self):
        from ZPublisher import NotFound
        r = self._makeOne(DummyTraverser())
        self.assertRaises(NotFound, r.traverse, 'not_found')


class TestBaseRequestZope3Views(unittest.TestCase, BaseRequest_factory):

    _dummy_interface = None

    def _getTargetClass(self):
        from ZPublisher.BaseRequest import BaseRequest
        return BaseRequest

    def _makeOne(self, root):
        from zope.interface import directlyProvides
        from zope.publisher.browser import IDefaultBrowserLayer
        request = super(TestBaseRequestZope3Views, self)._makeOne(root)
        # The request needs to implement the proper interface
        directlyProvides(request, IDefaultBrowserLayer)
        return request

    def _makeRootAndFolder(self):
        root = self._makeBasicObject()
        folder = root._setObject('folder', self._makeDummyObject('folder'))
        return root, folder

    def _dummyInterface(self):
        from zope.interface import Interface
        if self._dummy_interface is not None:
            return self._dummy_interface

        class IDummy(Interface):
            """IDummy"""

        self._dummy_interface = IDummy
        return IDummy

    def _makeDummyObject(self, name='dummy'):
        from zope.interface import implements

        class DummyObjectZ3(self._makeBasicObjectClass()):
            implements(self._dummyInterface())
            def __init__(self, name):
                self.name = name

        return DummyObjectZ3(name)

    def _makeDummyObjectWithAttr(self, name):
        from zope.interface import implements

        class DummyObjectZ3WithAttr(self._makeBasicObjectClass()):
            implements(self._dummyInterface())
            def __init__(self, name):
                self.name = name

            def meth(self):
                """doc"""
                return 'meth on %s' % self.name
            def methonly(self):
                """doc"""
                return 'methonly on %s' % self.name

        return DummyObjectZ3WithAttr(name)

    def setUp(self):
        from zope.testing.cleanup import cleanUp

        cleanUp()
        self._registerAdapters()

    def _registerAdapters(self):
        from Acquisition import Implicit
        from zope.component import getGlobalSiteManager
        from zope.interface import Interface
        from zope.publisher.browser import BrowserPage
        from zope.publisher.browser import IDefaultBrowserLayer
        from zope.traversing.interfaces import ITraversable
        from zope.traversing.namespace import view

        gsm = getGlobalSiteManager()

        IDummy = self._dummyInterface()

        class DummyView(Implicit):
            def __init__(self, content, request):
                self.content = content
                self.request = request
            def __call__(self):
                return 'view on %s' % (self.content.name)

        class DummyPage(BrowserPage):

            # BrowserPage is an IBrowserPublisher with a browserDefault that
            # returns self, () so that __call__ is invoked by the publisher.

            def __call__(self):
                return 'Test page'

        class DummyPage2(BrowserPage):

            def browserDefault(self, request):
                # intentionally return something that's not self
                return DummyPage(self.context, request), ()

            # __call__ remains unimplemented, baseclass raises NotImplementedError

        class DummyPage3(BrowserPage):

            def browserDefault(self, request):
                # intentionally return a method here
                return self.foo, ()

            def foo(self):
                return 'Test page'

            # __call__ remains unimplemented, baseclass raises NotImplementedError

        class DummyPage4(Implicit, DummyPage):
            # a normal page that can implicitly acquire attributes
            pass

        # Define the views
        gsm.registerAdapter(DummyView, (IDummy, IDefaultBrowserLayer),
                            Interface, 'meth')
        gsm.registerAdapter(DummyPage, (IDummy, IDefaultBrowserLayer),
                            Interface, 'page')
        gsm.registerAdapter(DummyPage2, (IDummy, IDefaultBrowserLayer),
                            Interface, 'page2')
        gsm.registerAdapter(DummyPage3, (IDummy, IDefaultBrowserLayer),
                            Interface, 'page3')
        gsm.registerAdapter(DummyPage4, (IDummy, IDefaultBrowserLayer),
                            Interface, 'page4')

        # Bind the 'view' namespace (for @@ traversal)
        gsm.registerAdapter(view,
                            (self._dummyInterface(), IDefaultBrowserLayer),
                            ITraversable, 'view')

    def tearDown(self):
        from zope.testing.cleanup import cleanUp
        cleanUp()

    def _setDefaultViewName(self, name):
        from zope.component import getGlobalSiteManager
        from zope.publisher.interfaces import IDefaultViewName
        from zope.publisher.browser import IBrowserRequest
        gsm = getGlobalSiteManager()
        gsm.registerAdapter(name, (self._dummyInterface(), IBrowserRequest),
                            IDefaultViewName, '')

    def test_traverse_view(self):
        #simple view
        root, folder = self._makeRootAndFolder()
        folder._setObject('obj', self._makeDummyObject('obj'))
        r = self._makeOne(root)
        ob = r.traverse('folder/obj/meth')
        self.assertEqual(ob(), 'view on obj')
        ob = r.traverse('folder/obj/@@meth')
        self.assertEqual(ob(), 'view on obj')
        # using default view
        self._setDefaultViewName('meth')
        ob = r.traverse('folder/obj')
        self.assertEqual(ob(), 'view on obj')

    def test_traverse_view_attr_local(self):
        #method on object used first
        root, folder = self._makeRootAndFolder()
        folder._setObject('withattr', self._makeDummyObjectWithAttr('withattr'))
        r = self._makeOne(root)
        ob = r.traverse('folder/withattr/meth')
        self.assertEqual(ob(), 'meth on withattr')
        ob = r.traverse('folder/withattr/@@meth')
        self.assertEqual(ob(), 'view on withattr')
        # using default view
        self._setDefaultViewName('meth')
        ob = r.traverse('folder/withattr')
        self.assertEqual(ob(), 'view on withattr')

    def test_traverse_view_attr_above(self):
        #view takes precedence over acquired attribute
        root, folder = self._makeRootAndFolder()
        folder2 = root._setObject('folder2', self._makeDummyObjectWithAttr('folder2'))
        folder2._setObject('obj2', self._makeDummyObject('obj2'))
        r = self._makeOne(root)
        ob = r.traverse('folder2/obj2/meth')
        self.assertEqual(ob(), 'view on obj2') # used to be buggy (acquired)
        ob = r.traverse('folder2/obj2/@@meth')
        self.assertEqual(ob(), 'view on obj2')
        # using default view
        self._setDefaultViewName('meth')
        ob = r.traverse('folder2/obj2')
        self.assertEqual(ob(), 'view on obj2')

    def test_traverse_view_attr_local2(self):
        #method with other method above
        root, folder = self._makeRootAndFolder()
        folder2 = root._setObject('folder2', self._makeDummyObjectWithAttr('folder2'))
        folder2._setObject('withattr2', self._makeDummyObjectWithAttr('withattr2'))
        r = self._makeOne(root)
        ob = r.traverse('folder2/withattr2/meth')
        self.assertEqual(ob(), 'meth on withattr2')
        ob = r.traverse('folder2/withattr2/@@meth')
        self.assertEqual(ob(), 'view on withattr2')
        # using default view
        self._setDefaultViewName('meth')
        ob = r.traverse('folder2/withattr2')
        self.assertEqual(ob(), 'view on withattr2')

    def test_traverse_view_attr_acquired(self):
        #normal acquired attribute without view
        from ZPublisher import NotFound
        root, folder = self._makeRootAndFolder()
        folder2 = root._setObject('folder2', self._makeDummyObjectWithAttr('folder2'))
        folder2._setObject('obj2', self._makeDummyObject('obj2'))
        r = self._makeOne(root)
        ob = r.traverse('folder2/obj2/methonly')
        self.assertEqual(ob(), 'methonly on folder2')
        self.assertRaises(NotFound, r.traverse, 'folder2/obj2/@@methonly')
        # using default view
        self._setDefaultViewName('methonly')
        self.assertRaises(NotFound, r.traverse, 'folder2/obj2')
        
    def test_quoting_goggles(self):
        #View goggles ('@@') should not be quoted
        root, folder = self._makeRootAndFolder()
        folder._setObject('obj', self._makeDummyObject('obj'))
        r = self._makeOne(root)
        r.traverse('folder/obj/@@meth')
        self.assertEqual(r['URL'], '/folder/obj/@@meth')
        
    def test_quoting_plusplus(self):
        #View markers ('++ should not be quoted
        root, folder = self._makeRootAndFolder()
        folder._setObject('obj', self._makeDummyObject('obj'))
        r = self._makeOne(root)
        r.traverse('folder/obj/++view++meth')
        self.assertEqual(r['URL'], '/folder/obj/++view++meth')

    def test_browserDefault(self):
        # browserDefault can return self, () to indicate that the
        # object itself wants to be published (using __call__):
        root, folder = self._makeRootAndFolder()
        folder._setObject('obj', self._makeDummyObject('obj'))
        r = self._makeOne(root)
        ob = r.traverse('folder/obj/page')
        self.assertEqual(ob(), 'Test page')

        # browserDefault can return another_object, () to indicate
        # that that object should be published (using __call__):
        r = self._makeOne(root)
        ob = r.traverse('folder/obj/page2')
        self.assertEqual(ob(), 'Test page')

        # browserDefault can also return self.some_method, () to
        # indicate that that method should be called.
        r = self._makeOne(root)
        ob = r.traverse('folder/obj/page3')
        self.assertEqual(ob(), 'Test page')
        
    def test_wrapping_implicit_acquirers(self):
        # when the default publish traverser finds via adaptation
        # an object providing IAcquirer, it should wrap it in the
        # object being traversed
        root, folder = self._makeRootAndFolder()
        ob2 = self._makeDummyObject('ob2')
        folder._setObject('ob2', ob2)
        r = self._makeOne(root)
        ob = r.traverse('folder/page4')
        self.assertEqual(ob(), 'Test page')
        # make sure we can acquire
        self.assertEqual(ob.ob2, ob2)


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(TestBaseRequest),
        unittest.makeSuite(TestBaseRequestZope3Views),
        ))
