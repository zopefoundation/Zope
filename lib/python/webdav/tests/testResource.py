import unittest

MS_DAV_AGENT = "Microsoft Data Access Internet Publishing Provider DAV"

def make_request_response(environ=None):
    from StringIO import StringIO
    from ZPublisher.HTTPRequest import HTTPRequest
    from ZPublisher.HTTPResponse import HTTPResponse
    
    if environ is None:
        environ = {}

    stdout = StringIO()
    stdin = StringIO()
    resp = HTTPResponse(stdout=stdout)
    environ.setdefault('SERVER_NAME', 'foo')
    environ.setdefault('SERVER_PORT', '80')
    environ.setdefault('REQUEST_METHOD', 'GET')
    req = HTTPRequest(stdin, environ, resp)
    return req, resp

class TestResource(unittest.TestCase):

    def test_z3interfaces(self):
        from webdav.interfaces import IDAVResource
        from webdav.interfaces import IWriteLock
        from webdav.Resource import Resource
        from zope.interface.verify import verifyClass

        verifyClass(IDAVResource, Resource)
        verifyClass(IWriteLock, Resource)

    def test_ms_author_via(self):
        import webdav
        from webdav.Resource import Resource

        default_settings = webdav.enable_ms_author_via
        try:
            req, resp = make_request_response()
            resource = Resource()
            resource.OPTIONS(req, resp)
            self.assert_(not resp.headers.has_key('ms-author-via'))

            webdav.enable_ms_author_via = True
            req, resp = make_request_response()
            resource = Resource()
            resource.OPTIONS(req, resp)
            self.assert_(not resp.headers.has_key('ms-author-via'))

            req, resp = make_request_response(
                environ={'USER_AGENT': MS_DAV_AGENT})
            resource = Resource()
            resource.OPTIONS(req, resp)
            self.assert_(resp.headers.has_key('ms-author-via'))
            self.assert_(resp.headers['ms-author-via'] == 'DAV')

        finally:
            webdav.enable_ms_author_via = default_settings

    def test_ms_public_header(self):
        import webdav
        from webdav.Resource import Resource
        default_settings = webdav.enable_ms_public_header
        try:
            req, resp = make_request_response()
            resource = Resource()
            resource.OPTIONS(req, resp)
            self.assert_(not resp.headers.has_key('public'))

            webdav.enable_ms_public_header = True
            req, resp = make_request_response()
            resource = Resource()
            resource.OPTIONS(req, resp)
            self.assert_(not resp.headers.has_key('public'))
            self.assert_(resp.headers.has_key('allow'))

            req, resp = make_request_response(
                environ={'USER_AGENT': MS_DAV_AGENT})
            resource = Resource()
            resource.OPTIONS(req, resp)
            self.assert_(resp.headers.has_key('public'))
            self.assert_(resp.headers.has_key('allow'))
            self.assert_(resp.headers['public'] == resp.headers['allow'])

        finally:
            webdav.enable_ms_public_header = default_settings

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(TestResource),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
