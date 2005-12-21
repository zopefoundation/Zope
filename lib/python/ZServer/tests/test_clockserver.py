import unittest
from StringIO import StringIO

from ZServer import ClockServer

class LogHelperTests(unittest.TestCase):
    def _getTargetClass(self):
        return ClockServer.LogHelper

    def _makeOne(self, *arg, **kw):
        return self._getTargetClass()(*arg **kw)

    def test_helper(self):
        from StringIO import StringIO
        logger = StringIO()
        logger.log = logger.write
        helper = self._makeOne(logger)
        self.assertEqual(helper.logger, logger)
        logger.log('ip', 'msg', foo=1, bar=2)
        logger.seek(0)
        self.assertEqual(logger.read(), 'ip msg')

class ClockServerTests(unittest.TestCase):
    def _getTargetClass(self):
        return ClockServer.ClockServer

    def _makeOne(self, *arg, **kw):
        return self._getTargetClass()(*arg **kw)

    def test_ctor(self):
        logger = StringIO()
        logger.log = logger.write
        server = self._makeOne(method='a', period=60, user='charlie',
                               password='brown', host='localhost',
                               logger=logger)
        auth = 'charlie:brown'.encode('base64')
        self.assertEqual(server.headers,
                         ['User-Agent: Zope Clock Server Client',
                          'Accept: text/html,text/plain',
                          'Host: localhost',
                          'Authorization: Basic %s' % auth])
        logger.seek(0)
        self.assertEqual(
            logger.read(),
            'Clock server for "a" started (user: charlie, period: 60)')
                          
    def test_get_requests_and_response(self):
        logger = StringIO()
        logger.log = logger.write
        server = self._makeOne(method='a', period=60, user='charlie',
                               password='brown', host='localhost',
                               logger=logger)
        req, zreq, resp = server.get_requests_and_response()

        from ZServer.medusa.http_server import http_request
        from ZServer.HTTPResponse import HTTPResponse
        from ZPublisher.HTTPRequest import HTTPRequest
        self.failUnless(issubclass(req, http_request))
        self.failUnless(issubclass(resp, HTTPResponse))
        self.failUnlesss(issubclass(zreq, HTTPRequest))

    def test_get_env(self):
        logger = StringIO()
        logger.log = logger.write
        server = self._makeOne(method='a', period=60, user='charlie',
                               password='brown', host='localhost',
                               logger=logger)
        class dummy_request:
            def split_uri(self):
                return '/a%20', '/b', '?foo=bar', ''

            header = ['BAR']
        env = server.get_env(dummy_request())
        _ENV = dict(REQUEST_METHOD = 'GET',
                    SERVER_PORT = 'Clock',
                    SERVER_NAME = 'Zope Clock Server',
                    SERVER_SOFTWARE = 'Zope',
                    SERVER_PROTOCOL = 'HTTP/1.0',
                    SCRIPT_NAME = '',
                    GATEWAY_INTERFACE='CGI/1.1',
                    REMOTE_ADDR = '0')
        for k, v in _ENV.items():
            self.assertEqual(env[k], v)
        self.assertEqual(env['PATH_INFO'], '')
        self.assertEqual(env['PATH_TRANSLATED'], '')
        self.assertEqual(env['QUERY_STRING'], 'foo=bar')
        self.assert_(env['channel.creation_time'])

    def test_handle_write(self):
        logger = StringIO()
        logger.log = logger.write
        server = self._makeOne(method='a', period=60, user='charlie',
                               password='brown', host='localhost',
                               logger=logger)
        server.handle_write()
        logger.seek(0)
        self.assertEqual(logger.read(), 'unexpected write event')

    def test_handle_error(self):
        logger = StringIO()
        logger.log = logger.write
        server = self._makeOne(method='a', period=60, user='charlie',
                               password='brown', host='localhost',
                               logger=logger)
        server.handle_error()
        logger.seek(0)
        self.assertEqual(logger.read, 'foo')

def test_suite():
    suite = unittest.makeSuite(ClockServerTests)
    suite.addTest(unittest.makeSuite(LogHelperTests))
    return suite

if __name__ == "__main__":
    unittest.main(defaultTest="test_suite")
