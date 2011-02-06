import unittest
from DateTime import DateTime

class FauxResponse:

    def __init__(self):
        self._headers = {}
        self._body = None

    def setBody(self, body):
        self._body = body

    def setHeader(self, name, value):
        self._headers[name] = value

    def setStatus(self, status):
        self._status = status

class FauxInstance:
    def __init__(self, **kw):
        self.__dict__.update(kw)

class XMLRPCResponseTests(unittest.TestCase):

    def _getTargetClass(self):
        from ZPublisher.xmlrpc import Response
        return Response

    def _makeOne(self, *args, **kw):
        return self._getTargetClass()(*args, **kw)

    def test_setBody(self):

        import xmlrpclib

        body = FauxInstance(_secret='abc', public='def')
        faux = FauxResponse()
        response = self._makeOne(faux)

        response.setBody(body)

        body_str = faux._body
        self.assertEqual(type(body_str), type(''))

        as_set, method = xmlrpclib.loads(body_str)
        as_set = as_set[0]

        self.assertEqual(method, None)
        self.failIf('_secret' in as_set.keys())
        self.failUnless('public' in as_set.keys())
        self.assertEqual(as_set['public'], 'def')

    def test_nil(self):
        import xmlrpclib
        body = FauxInstance(public=None)
        faux = FauxResponse()
        response = self._makeOne(faux)
        response.setBody(body)
        data, method = xmlrpclib.loads(faux._body)
        self.assert_(data[0]['public'] is None)

    def test_instance(self):
        # Instances are turned into dicts with their private
        # attributes removed.
        import xmlrpclib
        body = FauxInstance(_secret='abc', public='def')
        faux = FauxResponse()
        response = self._makeOne(faux)
        response.setBody(body)
        data, method = xmlrpclib.loads(faux._body)
        data = data[0]
        self.assertEqual(data, {'public': 'def'})

    def test_instanceattribute(self):
        # While the removal of private ('_') attributes works fine for the
        # top-level instance, how about attributes that are themselves
        # instances?
        import xmlrpclib
        body = FauxInstance(public=FauxInstance(_secret='abc', public='def'))
        faux = FauxResponse()
        response = self._makeOne(faux)
        response.setBody(body)
        data, method = xmlrpclib.loads(faux._body)
        data = data[0]['public']
        self.assertEqual(data, {'public': 'def'})

    def test_instanceattribute_recursive(self):
        # Instance "flattening" should work recursively, ad infinitum
        import xmlrpclib
        body = FauxInstance(public=FauxInstance(public=FauxInstance(_secret='abc', public='def')))
        faux = FauxResponse()
        response = self._makeOne(faux)
        response.setBody(body)
        data, method = xmlrpclib.loads(faux._body)
        data = data[0]['public']['public']
        self.assertEqual(data, {'public': 'def'})

    def test_instance_in_list(self):
        # Instances are turned into dicts with their private
        # attributes removed, even when embedded in another
        # data structure.
        import xmlrpclib
        body = [FauxInstance(_secret='abc', public='def')]
        faux = FauxResponse()
        response = self._makeOne(faux)
        response.setBody(body)
        data, method = xmlrpclib.loads(faux._body)
        data = data[0][0]
        self.assertEqual(data, {'public': 'def'})

    def test_instance_in_dict(self):
        # Instances are turned into dicts with their private
        # attributes removed, even when embedded in another
        # data structure.
        import xmlrpclib
        body = {'faux': FauxInstance(_secret='abc', public='def')}
        faux = FauxResponse()
        response = self._makeOne(faux)
        response.setBody(body)
        data, method = xmlrpclib.loads(faux._body)
        data = data[0]['faux']
        self.assertEqual(data, {'public': 'def'})

    def test_zopedatetimeinstance(self):
        # DateTime instance at top-level
        import xmlrpclib
        body = DateTime('2006-05-24 07:00:00 GMT+0')
        faux = FauxResponse()
        response = self._makeOne(faux)
        response.setBody(body)
        data, method = xmlrpclib.loads(faux._body)
        data = data[0]
        self.failUnless(isinstance(data, xmlrpclib.DateTime))
        self.assertEqual(data.value, u'2006-05-24T07:00:00+00:00')

    def test_zopedatetimeattribute(self):
        # DateTime instance as attribute
        import xmlrpclib
        body = FauxInstance(public=DateTime('2006-05-24 07:00:00 GMT+0'))
        faux = FauxResponse()
        response = self._makeOne(faux)
        response.setBody(body)
        data, method = xmlrpclib.loads(faux._body)
        data = data[0]['public']
        self.failUnless(isinstance(data, xmlrpclib.DateTime))
        self.assertEqual(data.value, u'2006-05-24T07:00:00+00:00')

    def test_zopedatetimeattribute_recursive(self):
        # DateTime encoding should work recursively
        import xmlrpclib
        body = FauxInstance(public=FauxInstance(public=DateTime('2006-05-24 07:00:00 GMT+0')))
        faux = FauxResponse()
        response = self._makeOne(faux)
        response.setBody(body)
        data, method = xmlrpclib.loads(faux._body)
        data = data[0]['public']['public']
        self.failUnless(isinstance(data, xmlrpclib.DateTime))
        self.assertEqual(data.value, u'2006-05-24T07:00:00+00:00')

    def test_zopedatetimeinstance_in_list(self):
        # DateTime instance embedded in a list
        import xmlrpclib
        body = [DateTime('2006-05-24 07:00:00 GMT+0')]
        faux = FauxResponse()
        response = self._makeOne(faux)
        response.setBody(body)
        data, method = xmlrpclib.loads(faux._body)
        data = data[0][0]
        self.failUnless(isinstance(data, xmlrpclib.DateTime))
        self.assertEqual(data.value, u'2006-05-24T07:00:00+00:00')

    def test_zopedatetimeinstance_in_dict(self):
        # DateTime instance embedded in a dict
        import xmlrpclib
        body = {'date': DateTime('2006-05-24 07:00:00 GMT+0')}
        faux = FauxResponse()
        response = self._makeOne(faux)
        response.setBody(body)
        data, method = xmlrpclib.loads(faux._body)
        data = data[0]['date']
        self.failUnless(isinstance(data, xmlrpclib.DateTime))
        self.assertEqual(data.value, u'2006-05-24T07:00:00+00:00')

    def test_functionattribute(self):
        # Cannot marshal functions or methods, obviously
        import sys
        import xmlrpclib
        def foo(): pass
        body = FauxInstance(public=foo)
        faux = FauxResponse()
        response = self._makeOne(faux)
        response.setBody(body)
        if sys.version_info < (2, 6):
            self.assertRaises(xmlrpclib.Fault, xmlrpclib.loads, faux._body)
        else:
            func = xmlrpclib.loads(faux._body)
            self.assertEqual(func, (({'public': {}},), None))

    def test_emptystringattribute(self):
        # Test an edge case: attribute name '' is possible,
        # at least in theory.
        import xmlrpclib
        body = FauxInstance(_secret='abc')
        setattr(body, '', True)
        faux = FauxResponse()
        response = self._makeOne(faux)
        response.setBody(body)
        data, method = xmlrpclib.loads(faux._body)
        data = data[0]
        self.assertEqual(data, {'': True})


def test_suite():
    return unittest.TestSuite((unittest.makeSuite(XMLRPCResponseTests),))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
