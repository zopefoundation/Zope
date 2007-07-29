from unittest import TestCase, TestSuite, makeSuite, main

from Acquisition import Implicit
from ZPublisher.BaseRequest import BaseRequest
from ZPublisher.HTTPResponse import HTTPResponse


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


class DummyObjectWithoutDocstring(Implicit):
    ""

    def view(self):
        """Attribute with docstring."""
        return 'view content'

    def noview(self):
        # Attribute without docstring.
        return 'unpublishable'


class DummyObjectWithDefault(DummyObjectBasic):
    """Dummy class with docstring."""

    def index_html(self):
        """Attribute with docstring."""
        return 'index_html content'


class DummyObjectWithDefaultNone(DummyObjectWithDefault):
    """Dummy class with docstring."""

    index_html = None


class DummyObjectWithBPTH(DummyObjectBasic):
    """Dummy class with docstring."""

    def __before_publishing_traverse__(self, object, REQUEST):
        if REQUEST['_test_counter'] < 100:
            REQUEST['_test_counter'] += 1
        else:
            raise RuntimeError('Infinite loop detected.')
        REQUEST['TraversalRequestNameStack'] += self._path
        REQUEST._hacked_path=1


class DummyObjectWithBBT(DummyObjectBasic):
    """ Dummy class with docstring.
    """

    def __bobo_traverse__(self, REQUEST, name):
        raise AttributeError, name

class DummyObjectWithBD(DummyObjectBasic):
    """Dummy class with docstring."""

    def __browser_default__(self, REQUEST):
        if REQUEST['_test_counter'] < 100:
            REQUEST['_test_counter'] += 1
        else:
            raise RuntimeError('Infinite loop detected.')
        return self, self._default_path

class DummyObjectWithBDBBT(DummyObjectWithBD):
    """Dummy class with docstring."""

    def __bobo_traverse__(self, REQUEST, name):
        if name == self._default_path[0]:
            return getattr(self, name)
        raise AttributeError, name


class TestBaseRequest(TestCase):

    def setUp(self):
        self.root = DummyObjectBasic()
        self.f1 = self.root._setObject('folder', DummyObjectBasic() )
        self.f1._setObject('objBasic', DummyObjectBasic() )
        self.f1._setObject('objWithDefault', DummyObjectWithDefault() )
        self.f1._setObject('objWithDefaultNone', DummyObjectWithDefaultNone() )
        self.f1._setObject('objWithBPTH', DummyObjectWithBPTH() )
        self.f1._setObject('objWithBD', DummyObjectWithBD() )
        self.f1._setObject('objWithBBT', DummyObjectWithBBT() )
        self.f1._setObject('objWithBDBBT', DummyObjectWithBDBBT() )
        self.f1._setObject('objWithoutDocstring', DummyObjectWithoutDocstring() )
        self.f1.simpleString = 'foo'
        self.f1.simpleList = []
        self.f1.simpleBoolean = True
        self.f1.simpleComplex = complex(1)
        self.f1.simpleSet = set([])
        self.f1.simpleFrozenSet = frozenset([])

    def makeBaseRequest(self):
        response = HTTPResponse()
        environment = { 'URL': '',
                        'PARENTS': [self.root],
                        'steps': [],
                        '_hacked_path': 0,
                        '_test_counter': 0,
                        'response': response }
        return BaseRequest(environment)

    def test_traverse_basic(self):
        r = self.makeBaseRequest()
        r.traverse('folder/objBasic')
        self.assertEqual(r.URL, '/folder/objBasic')
        self.assertEqual(r.response.base, '')

    def test_traverse_withDefault(self):
        r = self.makeBaseRequest()
        r.traverse('folder/objWithDefault')
        self.assertEqual(r.URL, '/folder/objWithDefault/index_html')
        self.assertEqual(r.response.base, '/folder/objWithDefault/')

    def test_traverse_withDefaultNone(self):
        r = self.makeBaseRequest()
        r.traverse('folder/objWithDefaultNone')
        self.assertEqual(r.URL, '/folder/objWithDefaultNone')
        self.assertEqual(r.response.base, '')

    def test_traverse_withBPTH(self):
        r = self.makeBaseRequest()
        self.f1.objWithBPTH._path = ['view']
        r.traverse('folder/objWithBPTH')
        self.assertEqual(r.URL, '/folder/objWithBPTH/view')
        self.assertEqual(r.response.base, '/folder/objWithBPTH/')

    def test_traverse_withBDView(self):
        r = self.makeBaseRequest()
        self.f1.objWithBD._default_path = ['view']
        r.traverse('folder/objWithBD')
        self.assertEqual(r.URL, '/folder/objWithBD/view')
        self.assertEqual(r.response.base, '/folder/objWithBD/')

    def test_traverse_withAcquisition(self):
        r = self.makeBaseRequest()
        self.f1.objWithBPTH._path = ['view']
        self.f1.objWithBD._default_path = ['view']
        r.traverse('folder/objWithBD/objWithBPTH')
        self.assertEqual(r.URL, '/folder/objWithBD/objWithBPTH/view')
        self.assertEqual(r.response.base, '/folder/objWithBD/objWithBPTH/')

    def test_traverse_withBDAndBPTH(self):
        # Collector 1079 (infinite loop 1)
        r = self.makeBaseRequest()
        self.f1.objWithBPTH._path = ['objBasic']
        self.f1.objWithBD._default_path = ['objWithBPTH']
        r.traverse('folder/objWithBD')
        self.assertEqual(r.URL, '/folder/objWithBD/objWithBPTH/objBasic')
        self.assertEqual(r.response.base, '/folder/objWithBD/objWithBPTH/')

    def test_traverse_withBDEmpty(self):
        # Collector 1079 (infinite loop 2)
        from ZPublisher import NotFound
        r = self.makeBaseRequest()
        self.f1.objWithBD._default_path = ['']
        self.failUnlessRaises(NotFound, r.traverse, 'folder/objWithBD')

    def test_traverse_withBBT_handles_AttributeError(self):
        # Test that if __bobo_traverse__ raises AttributeError
        # that we get a NotFound
        from ZPublisher import NotFound
        r = self.makeBaseRequest()
        self.failUnlessRaises(NotFound, r.traverse, 'folder/objWithBBT/bbt_foo')

    def test_traverse_withBDBBT(self):
        # Test for an object which has a __browser_default__
        # and __bobo_traverse__
        # __bobo_traverse__ should return the object
        # pointed by __browser_default__
        r = self.makeBaseRequest()
        self.f1.objWithBDBBT._default_path = ['view']
        r.traverse('folder/objWithBDBBT')
        self.assertEqual(r.URL, '/folder/objWithBDBBT/view')
        self.assertEqual(r.response.base, '/folder/objWithBDBBT/')

    def test_traverse_withBDBBT_NotFound(self):
        # Test for an object which has a __browser_default__
        # and __bobo_traverse__
        # __bobo_traverse__ should raise an AttributeError, which will
        # raise a NotFound
        from ZPublisher import NotFound
        r = self.makeBaseRequest()
        self.f1.objWithBDBBT._default_path = ['xxx']
        r = self.makeBaseRequest()
        self.failUnlessRaises(NotFound, r.traverse, 'folder/objWithBDBBT')

    def test_traverse_slash(self):
        r = self.makeBaseRequest()
        r['PARENTS'] = [self.f1.objWithDefault]
        r.traverse('/')
        self.assertEqual(r.URL, '/index_html')
        self.assertEqual(r.response.base, '')

    def test_traverse_attribute_with_docstring(self):
        r = self.makeBaseRequest()
        r.traverse('folder/objBasic/view')
        self.assertEqual(r.URL, '/folder/objBasic/view')
        self.assertEqual(r.response.base, '')

    def test_traverse_attribute_without_docstring(self):
        from ZPublisher import NotFound
        r = self.makeBaseRequest()
        self.assertRaises(NotFound, r.traverse, 'folder/objBasic/noview')

    def test_traverse_class_without_docstring(self):
        from ZPublisher import NotFound
        r = self.makeBaseRequest()
        self.assertRaises(NotFound, r.traverse, 'folder/objWithoutDocstring')

    def test_traverse_attribute_of_class_without_docstring(self):
        from ZPublisher import NotFound
        r = self.makeBaseRequest()
        self.assertRaises(NotFound, r.traverse, 'folder/objWithoutDocstring/view')

    def test_traverse_attribute_and_class_without_docstring(self):
        from ZPublisher import NotFound
        r = self.makeBaseRequest()
        self.assertRaises(NotFound, r.traverse, 'folder/objWithoutDocstring/noview')

    def test_traverse_simple_type(self):
        from ZPublisher import NotFound
        r = self.makeBaseRequest()
        self.assertRaises(NotFound, r.traverse, 'folder/simpleString')
        self.assertRaises(NotFound, r.traverse, 'folder/simpleList')
        self.assertRaises(NotFound, r.traverse, 'folder/simpleBoolean')
        self.assertRaises(NotFound, r.traverse, 'folder/simpleComplex')

    def test_traverse_set_type(self):
        from ZPublisher import NotFound
        r = self.makeBaseRequest()
        self.assertRaises(NotFound, r.traverse, 'folder/simpleSet')
        self.assertRaises(NotFound, r.traverse, 'folder/simpleFrozenSet')

    def test_hold_after_close(self):
        # Request should no longer accept holds after it has been closed
        r = self.makeBaseRequest()
        r._hold(lambda x: None)
        self.assertEqual(len(r._held), 1)
        r.close()
        # No more holding from now on
        self.assertEqual(r._held, None)
        r._hold(lambda x: None)
        self.assertEqual(r._held, None)

from ZPublisher import NotFound

import zope.interface
import zope.component
import zope.testing.cleanup
import zope.traversing.namespace
import zope.publisher.browser
from zope.publisher.browser import IBrowserRequest
from zope.publisher.browser import IDefaultBrowserLayer
from zope.traversing.interfaces import ITraversable

class IDummy(zope.interface.Interface):
    """IDummy"""

class DummyObjectZ3(DummyObjectBasic):
    zope.interface.implements(IDummy)
    def __init__(self, name):
        self.name = name

class DummyObjectZ3WithAttr(DummyObjectZ3):
    def meth(self):
        """doc"""
        return 'meth on %s' % self.name
    def methonly(self):
        """doc"""
        return 'methonly on %s' % self.name

class DummyView(Implicit):
    def __init__(self, content, request):
        self.content = content
        self.request = request
    def __call__(self):
        return 'view on %s' % (self.content.name)

class DummyPage(zope.publisher.browser.BrowserPage):

    # BrowserPage is an IBrowserPublisher with a browserDefault that
    # returns self, () so that __call__ is invoked by the publisher.

    def __call__(self):
        return 'Test page'

class DummyPage2(zope.publisher.browser.BrowserPage):

    def browserDefault(self, request):
        # intentionally return something that's not self
        return DummyPage(self.context, request), ()

    # __call__ remains unimplemented, baseclass raises NotImplementedError

class DummyPage3(zope.publisher.browser.BrowserPage):

    def browserDefault(self, request):
        # intentionally return a method here
        return self.foo, ()

    def foo(self):
        return 'Test page'

    # __call__ remains unimplemented, baseclass raises NotImplementedError

class TestBaseRequestZope3Views(TestCase):

    def setUp(self):
        zope.testing.cleanup.cleanUp()
        self.root = DummyObjectBasic()
        folder = self.root._setObject('folder', DummyObjectZ3('folder'))
        folder._setObject('obj', DummyObjectZ3('obj'))
        folder._setObject('withattr', DummyObjectZ3WithAttr('withattr'))
        folder2 = self.root._setObject('folder2',
                                       DummyObjectZ3WithAttr('folder2'))
        folder2._setObject('obj2', DummyObjectZ3('obj2'))
        folder2._setObject('withattr2', DummyObjectZ3WithAttr('withattr2'))
        gsm = zope.component.getGlobalSiteManager()

        # The request needs to implement the proper interface
        zope.interface.classImplements(BaseRequest, IDefaultBrowserLayer)

        # Define the views
        gsm.registerAdapter(DummyView, (IDummy, IDefaultBrowserLayer),
                            zope.interface.Interface, 'meth')
        gsm.registerAdapter(DummyPage, (IDummy, IDefaultBrowserLayer),
                            zope.interface.Interface, 'page')
        gsm.registerAdapter(DummyPage2, (IDummy, IDefaultBrowserLayer),
                            zope.interface.Interface, 'page2')
        gsm.registerAdapter(DummyPage3, (IDummy, IDefaultBrowserLayer),
                            zope.interface.Interface, 'page3')

        # Bind the 'view' namespace (for @@ traversal)
        gsm.registerAdapter(zope.traversing.namespace.view,
                            (IDummy, IDefaultBrowserLayer), ITraversable,
                            'view')

    def tearDown(self):
        zope.testing.cleanup.cleanUp()

    def makeBaseRequest(self):
        response = HTTPResponse()
        environment = {
            'URL': '',
            'PARENTS': [self.root],
            'steps': [],
            '_hacked_path': 0,
            '_test_counter': 0,
            'response': response,
            }
        return BaseRequest(environment)

    def setDefaultViewName(self, name):
        from zope.component.interfaces import IDefaultViewName
        gsm = zope.component.getGlobalSiteManager()
        gsm.registerAdapter(name, (IDummy, IBrowserRequest), IDefaultViewName,
                            '')

    def test_traverse_view(self):
        """simple view"""
        r = self.makeBaseRequest()
        ob = r.traverse('folder/obj/meth')
        self.assertEqual(ob(), 'view on obj')
        ob = r.traverse('folder/obj/@@meth')
        self.assertEqual(ob(), 'view on obj')
        # using default view
        self.setDefaultViewName('meth')
        ob = r.traverse('folder/obj')
        self.assertEqual(ob(), 'view on obj')

    def test_traverse_view_attr_local(self):
        """method on object used first"""
        r = self.makeBaseRequest()
        ob = r.traverse('folder/withattr/meth')
        self.assertEqual(ob(), 'meth on withattr')
        ob = r.traverse('folder/withattr/@@meth')
        self.assertEqual(ob(), 'view on withattr')
        # using default view
        self.setDefaultViewName('meth')
        ob = r.traverse('folder/withattr')
        self.assertEqual(ob(), 'view on withattr')

    def test_traverse_view_attr_above(self):
        """view takes precedence over acquired attribute"""
        r = self.makeBaseRequest()
        ob = r.traverse('folder2/obj2/meth')
        self.assertEqual(ob(), 'view on obj2') # used to be buggy (acquired)
        ob = r.traverse('folder2/obj2/@@meth')
        self.assertEqual(ob(), 'view on obj2')
        # using default view
        self.setDefaultViewName('meth')
        ob = r.traverse('folder2/obj2')
        self.assertEqual(ob(), 'view on obj2')

    def test_traverse_view_attr_local2(self):
        """method with other method above"""
        r = self.makeBaseRequest()
        ob = r.traverse('folder2/withattr2/meth')
        self.assertEqual(ob(), 'meth on withattr2')
        ob = r.traverse('folder2/withattr2/@@meth')
        self.assertEqual(ob(), 'view on withattr2')
        # using default view
        self.setDefaultViewName('meth')
        ob = r.traverse('folder2/withattr2')
        self.assertEqual(ob(), 'view on withattr2')

    def test_traverse_view_attr_acquired(self):
        """normal acquired attribute without view"""
        r = self.makeBaseRequest()
        ob = r.traverse('folder2/obj2/methonly')
        self.assertEqual(ob(), 'methonly on folder2')
        self.assertRaises(NotFound, r.traverse, 'folder2/obj2/@@methonly')
        # using default view
        self.setDefaultViewName('methonly')
        self.assertRaises(NotFound, r.traverse, 'folder2/obj2')
        
    def test_quoting(self):
        """View markers should not be quoted"""
        r = self.makeBaseRequest()
        r.traverse('folder/obj/@@meth')
        self.assertEqual(r['URL'], '/folder/obj/@@meth')

        r = self.makeBaseRequest()
        r.traverse('folder/obj/++view++meth')
        self.assertEqual(r['URL'], '/folder/obj/++view++meth')

    def test_browserDefault(self):
        # Test that browserDefault returning self, () works
        r = self.makeBaseRequest()
        ob = r.traverse('folder/obj/page')
        self.assertEqual(ob(), 'Test page')

        r = self.makeBaseRequest()
        ob = r.traverse('folder/obj/page2')
        self.assertEqual(ob(), 'Test page')

def test_suite():
    return TestSuite( ( makeSuite(TestBaseRequest),
                        makeSuite(TestBaseRequestZope3Views),
                    ) )

if __name__ == '__main__':
    main(defaultTest='test_suite')
