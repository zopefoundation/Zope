import unittest

class FauxResponse:

    def __init__(self):
        self._headers = {}
        self._body = None

    def setBody(self, body):
        self._body = body

    def setHeader(self, name, value):
        self._headers[name] = value

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


def test_suite():
    return unittest.TestSuite((unittest.makeSuite(XMLRPCResponseTests),))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
