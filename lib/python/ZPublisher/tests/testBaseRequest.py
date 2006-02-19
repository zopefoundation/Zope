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

    import sys
    if sys.version_info >= (2, 4):

        def test_traverse_set_type(self):
            from ZPublisher import NotFound
            self.f1.simpleSet = set([])
            self.f1.simpleFrozenSet = frozenset([])
            r = self.makeBaseRequest()
            self.assertRaises(NotFound, r.traverse, 'folder/simpleSet')
            self.assertRaises(NotFound, r.traverse, 'folder/simpleFrozenSet')


def test_suite():
    return TestSuite( ( makeSuite(TestBaseRequest), ) )

if __name__ == '__main__':
    main(defaultTest='test_suite')
