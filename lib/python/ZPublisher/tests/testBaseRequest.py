import unittest

from Acquisition import Implicit

import zope.interface
import zope.component
import zope.testing.cleanup
import zope.traversing.namespace
from zope.publisher.browser import IBrowserRequest
from zope.publisher.browser import IDefaultBrowserLayer
from zope.traversing.interfaces import ITraversable


class TestBaseRequest(unittest.TestCase):

    def _getTargetClass(self):
        from ZPublisher.BaseRequest import BaseRequest
        return BaseRequest

    def _makeOne(self, root):
        response = DummyResponse()
        environment = { 'URL': '',
                        'PARENTS': [root],
                        'steps': [],
                        '_hacked_path': 0,
                        '_test_counter': 0,
                        'response': response }
        return self._getTargetClass()(environment)

    def _makeRootAndFolder(self):
        root = DummyObjectBasic()
        folder = root._setObject('folder', DummyObjectBasic())
        return root, folder

    def test_traverse_basic(self):
        root, folder = self._makeRootAndFolder()
        folder._setObject('objBasic', DummyObjectBasic())
        r = self._makeOne(root)
        r.traverse('folder/objBasic')
        self.assertEqual(r.URL, '/folder/objBasic')
        self.assertEqual(r.response.base, '')

    def test_traverse_withDefault(self):
        root, folder = self._makeRootAndFolder()
        folder._setObject('objWithDefault', DummyObjectWithDefault())
        r = self._makeOne(root)
        r.traverse('folder/objWithDefault')
        self.assertEqual(r.URL, '/folder/objWithDefault/index_html')
        self.assertEqual(r.response.base, '/folder/objWithDefault/')

    def test_traverse_withDefaultNone(self):
        root, folder = self._makeRootAndFolder()
        folder._setObject('objWithDefaultNone', DummyObjectWithDefaultNone())
        r = self._makeOne(root)
        r.traverse('folder/objWithDefaultNone')
        self.assertEqual(r.URL, '/folder/objWithDefaultNone')
        self.assertEqual(r.response.base, '')

    def test_traverse_withBPTH(self):
        root, folder = self._makeRootAndFolder()
        folder._setObject('objWithBPTH', DummyObjectWithBPTH())
        folder.objWithBPTH._path = ['view']
        r = self._makeOne(root)
        r.traverse('folder/objWithBPTH')
        self.assertEqual(r.URL, '/folder/objWithBPTH/view')
        self.assertEqual(r.response.base, '/folder/objWithBPTH/')

    def test_traverse_withBDView(self):
        root, folder = self._makeRootAndFolder()
        folder._setObject('objWithBD', DummyObjectWithBD())
        folder.objWithBD._default_path = ['view']
        r = self._makeOne(root)
        r.traverse('folder/objWithBD')
        self.assertEqual(r.URL, '/folder/objWithBD/view')
        self.assertEqual(r.response.base, '/folder/objWithBD/')

    def test_traverse_withAcquisition(self):
        root, folder = self._makeRootAndFolder()
        folder._setObject('objWithBPTH', DummyObjectWithBPTH())
        folder.objWithBPTH._path = ['view']
        folder._setObject('objWithBD', DummyObjectWithBD())
        folder.objWithBD._default_path = ['view']
        r = self._makeOne(root)
        r.traverse('folder/objWithBD/objWithBPTH')
        self.assertEqual(r.URL, '/folder/objWithBD/objWithBPTH/view')
        self.assertEqual(r.response.base, '/folder/objWithBD/objWithBPTH/')

    def test_traverse_withBDAndBPTH(self):
        # Collector 1079 (infinite loop 1)
        root, folder = self._makeRootAndFolder()
        folder._setObject('objBasic', DummyObjectBasic())
        folder._setObject('objWithBPTH', DummyObjectWithBPTH())
        folder.objWithBPTH._path = ['objBasic']
        folder._setObject('objWithBD', DummyObjectWithBD())
        folder.objWithBD._default_path = ['objWithBPTH']
        r = self._makeOne(root)
        r.traverse('folder/objWithBD')
        self.assertEqual(r.URL, '/folder/objWithBD/objWithBPTH/objBasic')
        self.assertEqual(r.response.base, '/folder/objWithBD/objWithBPTH/')

    def test_traverse_withBDEmpty(self):
        # Collector 1079 (infinite loop 2)
        from ZPublisher import NotFound
        root, folder = self._makeRootAndFolder()
        folder._setObject('objWithBD', DummyObjectWithBD())
        folder.objWithBD._default_path = ['']
        r = self._makeOne(root)
        self.failUnlessRaises(NotFound, r.traverse, 'folder/objWithBD')

    def test_traverse_withBBT_handles_AttributeError(self):
        # Test that if __bobo_traverse__ raises AttributeError
        # that we get a NotFound
        from ZPublisher import NotFound
        root, folder = self._makeRootAndFolder()
        folder._setObject('objWithBBT', DummyObjectWithBBT())
        r = self._makeOne(root)
        self.failUnlessRaises(NotFound, r.traverse,
                              'folder/objWithBBT/bbt_foo')

    def test_traverse_withBDBBT(self):
        # Test for an object which has a __browser_default__
        # and __bobo_traverse__
        # __bobo_traverse__ should return the object
        # pointed by __browser_default__
        root, folder = self._makeRootAndFolder()
        folder._setObject('objWithBDBBT', DummyObjectWithBDBBT())
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
        folder._setObject('objWithBDBBT', DummyObjectWithBDBBT())
        folder.objWithBDBBT._default_path = ['xxx']
        r = self._makeOne(root)
        self.failUnlessRaises(NotFound, r.traverse, 'folder/objWithBDBBT')

    def test_traverse_slash(self):
        root, folder = self._makeRootAndFolder()
        folder._setObject('objWithDefault', DummyObjectWithDefault())
        r = self._makeOne(root)
        r['PARENTS'] = [folder.objWithDefault]
        r.traverse('/')
        self.assertEqual(r.URL, '/index_html')
        self.assertEqual(r.response.base, '')

    def test_traverse_attribute_with_docstring(self):
        root, folder = self._makeRootAndFolder()
        folder._setObject('objBasic', DummyObjectBasic())
        r = self._makeOne(root)
        r.traverse('folder/objBasic/view')
        self.assertEqual(r.URL, '/folder/objBasic/view')
        self.assertEqual(r.response.base, '')

    def test_traverse_attribute_without_docstring(self):
        from ZPublisher import NotFound
        root, folder = self._makeRootAndFolder()
        folder._setObject('objBasic', DummyObjectBasic())
        r = self._makeOne(root)
        self.assertRaises(NotFound, r.traverse, 'folder/objBasic/noview')

    def test_traverse_class_without_docstring(self):
        from ZPublisher import NotFound
        root, folder = self._makeRootAndFolder()
        folder._setObject('objWithoutDocstring', DummyObjectWithoutDocstring())
        r = self._makeOne(root)
        self.assertRaises(NotFound, r.traverse, 'folder/objWithoutDocstring')

    def test_traverse_attribute_of_class_without_docstring(self):
        from ZPublisher import NotFound
        root, folder = self._makeRootAndFolder()
        folder._setObject('objWithoutDocstring', DummyObjectWithoutDocstring())
        r = self._makeOne(root)
        self.assertRaises(NotFound, r.traverse,
                              'folder/objWithoutDocstring/view')

    def test_traverse_attribute_and_class_without_docstring(self):
        from ZPublisher import NotFound
        root, folder = self._makeRootAndFolder()
        r = self._makeOne(root)
        folder._setObject('objWithoutDocstring', DummyObjectWithoutDocstring())
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
        class _Object(object):
            pass
        root = _Object()
        r = self._makeOne(None)
        self.assertRaises(NotFound, r.traverse, 'not_found')


class TestBaseRequestZope3Views(unittest.TestCase):

    def _getTargetClass(self):
        from ZPublisher.BaseRequest import BaseRequest
        return BaseRequest

    def _makeOne(self, root):
        response = DummyResponse()
        environment = { 'URL': '',
                        'PARENTS': [root],
                        'steps': [],
                        '_hacked_path': 0,
                        '_test_counter': 0,
                        'response': response }

        request = self._getTargetClass()(environment)

        # The request needs to implement the proper interface
        zope.interface.directlyProvides(request, IDefaultBrowserLayer)
        return request

    def _makeRootAndFolder(self):
        root = DummyObjectBasic()
        folder = root._setObject('folder', DummyObjectZ3('folder'))
        return root, folder

    def setUp(self):
        zope.testing.cleanup.cleanUp()

        gsm = zope.component.getGlobalSiteManager()

        # Define our 'meth' view
        gsm.registerAdapter(DummyView, (IDummy, IDefaultBrowserLayer), None,
                            'meth')

        # Bind the 'view' namespace (for @@ traversal)
        gsm.registerAdapter(zope.traversing.namespace.view,
                            (IDummy, IDefaultBrowserLayer), ITraversable,
                            'view')

    def tearDown(self):
        zope.testing.cleanup.cleanUp()

    def _setDefaultViewName(self, name):
        from zope.component.interfaces import IDefaultViewName
        gsm = zope.component.getGlobalSiteManager()
        gsm.registerAdapter(name, (IDummy, IBrowserRequest), IDefaultViewName,
                            '')

    def test_traverse_view(self):
        #simple view
        root, folder = self._makeRootAndFolder()
        folder._setObject('obj', DummyObjectZ3('obj'))
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
        folder._setObject('withattr', DummyObjectZ3WithAttr('withattr'))
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
        folder2 = root._setObject('folder2', DummyObjectZ3WithAttr('folder2'))
        folder2._setObject('obj2', DummyObjectZ3('obj2'))
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
        folder2 = root._setObject('folder2', DummyObjectZ3WithAttr('folder2'))
        folder2._setObject('withattr2', DummyObjectZ3WithAttr('withattr2'))
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
        folder2 = root._setObject('folder2', DummyObjectZ3WithAttr('folder2'))
        folder2._setObject('obj2', DummyObjectZ3('obj2'))
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
        folder._setObject('obj', DummyObjectZ3('obj'))
        r = self._makeOne(root)
        r.traverse('folder/obj/@@meth')
        self.assertEqual(r['URL'], '/folder/obj/@@meth')
        
    def test_quoting_plusplus(self):
        #View markers ('++ should not be quoted
        root, folder = self._makeRootAndFolder()
        folder._setObject('obj', DummyObjectZ3('obj'))
        r = self._makeOne(root)
        r.traverse('folder/obj/++view++meth')
        self.assertEqual(r['URL'], '/folder/obj/++view++meth')


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

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(TestBaseRequest),
        unittest.makeSuite(TestBaseRequestZope3Views),
        ))

if __name__ == '__main__':
    unitttest.main(defaultTest='test_suite')
