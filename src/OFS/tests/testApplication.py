import unittest


class ApplicationTests(unittest.TestCase):

    def _getTargetClass(self):
        from OFS.Application import Application
        return Application

    def _makeOne(self):
        return self._getTargetClass()()

    def test_class_provides_IApplication(self):
        from OFS.interfaces import IApplication
        from zope.interface.verify import verifyClass

        verifyClass(IApplication, self._getTargetClass())

    def test_instance_conforms_to_IApplication(self):
        from OFS.interfaces import IApplication
        from zope.interface.verify import verifyObject

        verifyObject(IApplication, self._makeOne())

    def test_instance_attributes(self):
        app = self._makeOne()
        self.failUnless(app.isTopLevelPrincipiaApplicationObject)
        self.assertEqual(app.title, 'Zope')

    def test_id_no_request(self):
        app = self._makeOne()
        self.assertEqual(app.id(), 'Zope')

    def test_id_w_request_no_SCRIPT_NAME(self):
        app = self._makeOne()
        app.REQUEST = {}
        self.assertEqual(app.id(), 'Zope')

    def test_id_w_request_w_SCRIPT_NAME(self):
        app = self._makeOne()
        app.REQUEST = {'SCRIPT_NAME': '/Dummy'}
        self.assertEqual(app.id(), 'Dummy')

    def test_title_and_id_plus_title_or_id(self):
        app = self._makeOne()
        app.title = 'Other'
        self.assertEqual(app.title_and_id(), 'Other')
        self.assertEqual(app.title_or_id(), 'Other')

    def test___bobo_traverse__attribute_hit(self):
        app = self._makeOne()
        app.NAME = 'attribute'
        app._getOb = lambda x, y: x
        request = {}
        self.assertEqual(app.__bobo_traverse__(request, 'NAME'), 'attribute')

    def test___bobo_traverse__attribute_miss_key_hit(self):
        app = self._makeOne()
        app._getOb = lambda x, y: x
        app._objects = [{'id': 'OTHER', 'meta_type': None}]
        request = {}
        self.assertEqual(app.__bobo_traverse__(request, 'OTHER'), 'OTHER')

    def test___bobo_traverse__attribute_key_miss_R_M_default_real_request(self):
        from UserDict import UserDict
        request = UserDict()

        class _Response:
            def notFoundError(self, msg):
                1/0

        request.RESPONSE = _Response()
        app = self._makeOne()
        app._getOb = _noWay

        self.assertRaises(ZeroDivisionError,
                          app.__bobo_traverse__, request, 'NONESUCH')

    def test___bobo_traverse__attribute_key_miss_R_M_default_fake_request(self):
        app = self._makeOne()

        app._getOb = _noWay
        request = {}
        self.assertRaises(KeyError, app.__bobo_traverse__, request, 'NONESUCH')

    def test___bobo_traverse__attribute_key_miss_R_M_is_GET(self):
        app = self._makeOne()

        app._getOb = _noWay
        request = {'REQUEST_METHOD': 'GET'}
        self.assertRaises(KeyError, app.__bobo_traverse__, request, 'NONESUCH')

    def test___bobo_traverse__attribute_key_miss_R_M_not_GET_POST(self):
        from Acquisition import aq_inner, aq_parent
        from webdav.NullResource import NullResource

        app = self._makeOne()
        app._getOb = _noWay
        request = {'REQUEST_METHOD': 'GOOFY'}

        result = app.__bobo_traverse__(request, 'OTHER')

        self.failUnless(isinstance(result, NullResource))
        self.failUnless(aq_parent(aq_inner(result)) is app)

def _noWay(self, key, default=None):
    raise KeyError(key)

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(ApplicationTests),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
