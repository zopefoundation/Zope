import unittest
import time
from StringIO import StringIO

from ZServer import ClockServer

class DummyLogger:
    def __init__(self):
        self.L = []
        
    def log(self, *arg, **kw):
        self.L.extend(arg)

    def read(self):
        return ' '.join(self.L)

class LogHelperTests(unittest.TestCase):
    def _getTargetClass(self):
        return ClockServer.LogHelper

    def _makeOne(self, *arg, **kw):
        return self._getTargetClass()(*arg, **kw)

    def test_helper(self):
        from StringIO import StringIO
        logger = DummyLogger()
        helper = self._makeOne(logger)
        self.assertEqual(helper.logger, logger)
        logger.log('ip', 'msg', foo=1, bar=2)
        self.assertEqual(logger.read(), 'ip msg')

class ClockServerTests(unittest.TestCase):
    def _getTargetClass(self):
        return ClockServer.ClockServer

    def _makeOne(self, *arg, **kw):
        return self._getTargetClass()(*arg, **kw)

    def test_ctor(self):
        logger = DummyLogger()
        server = self._makeOne(method='a', period=60, user='charlie',
                               password='brown', host='localhost',
                               logger=logger)
        auth = 'charlie:brown'.encode('base64')
        self.assertEqual(server.headers,
                         ['User-Agent: Zope Clock Server Client',
                          'Accept: text/html,text/plain',
                          'Host: localhost',
                          'Authorization: Basic %s' % auth])
                          
    def test_get_requests_and_response(self):
        logger = DummyLogger()
        server = self._makeOne(method='a', period=60, user='charlie',
                               password='brown', host='localhost',
                               logger=logger)
        req, zreq, resp = server.get_requests_and_response()

        from ZServer.medusa.http_server import http_request
        from ZServer.HTTPResponse import HTTPResponse
        from ZPublisher.HTTPRequest import HTTPRequest
        self.failUnless(isinstance(req, http_request))
        self.failUnless(isinstance(resp, HTTPResponse))
        self.failUnless(isinstance(zreq, HTTPRequest))

    def test_get_env(self):
        logger = DummyLogger()
        server = self._makeOne(method='a', period=60, user='charlie',
                               password='brown', host='localhost',
                               logger=logger)
        class dummy_request:
            def split_uri(self):
                return '/a%20', '/b', '?foo=bar', ''

            header = ['BAR:baz']
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
        self.assertEqual(env['PATH_INFO'], '/a /b')
        self.assertEqual(env['PATH_TRANSLATED'], '/a /b')
        self.assertEqual(env['QUERY_STRING'], 'foo=bar')
        self.assert_(env['channel.creation_time'])

    def test_handle_write(self):
        logger = DummyLogger()
        server = self._makeOne(method='a', period=60, user='charlie',
                               password='brown', host='localhost',
                               logger=logger)
        self.assertEqual(server.handle_write(), True)

    #def test_handle_error(self):  Can't be usefully tested

    def test_readable(self):
        logger = DummyLogger()
        class DummyHandler:
            def __init__(self):
                self.arg = []
            def __call__(self, *arg):
                self.arg = arg
        handler = DummyHandler()
        server = self._makeOne(method='a', period=1, user='charlie',
                               password='brown', host='localhost',
                               logger=logger, handler=handler)
        self.assertEqual(server.readable(), False)
        self.assertEqual(handler.arg, [])
        time.sleep(1.1) # allow timeslice to switch
        self.assertEqual(server.readable(), False)
        self.assertEqual(handler.arg[0], 'Zope2')
        from ZServer.HTTPResponse import HTTPResponse
        from ZPublisher.HTTPRequest import HTTPRequest
        self.assert_(isinstance(handler.arg[1], HTTPRequest))
        self.assert_(isinstance(handler.arg[2], HTTPResponse))

    def test_timeslice(self):
        from ZServer.ClockServer import timeslice
        aslice = timeslice(3, 6)
        self.assertEqual(aslice, 6)
        aslice = timeslice(3, 7)
        self.assertEqual(aslice, 6)
        aslice = timeslice(3, 8)
        self.assertEqual(aslice, 6)
        aslice = timeslice(3, 9)
        self.assertEqual(aslice, 9)
        aslice = timeslice(3, 10)
        self.assertEqual(aslice, 9)
        aslice = timeslice(3, 11)
        self.assertEqual(aslice, 9)
        aslice = timeslice(3, 12)
        self.assertEqual(aslice, 12)
        aslice = timeslice(3, 13)
        self.assertEqual(aslice, 12)
        aslice = timeslice(3, 14)
        self.assertEqual(aslice, 12)
        aslice = timeslice(3, 15)
        self.assertEqual(aslice, 15)
        aslice = timeslice(3, 16)
        self.assertEqual(aslice, 15)
        aslice = timeslice(3, 17)
        self.assertEqual(aslice, 15)
        aslice = timeslice(3, 18)
        self.assertEqual(aslice, 18)

def test_suite():
    suite = unittest.makeSuite(ClockServerTests)
    suite.addTest(unittest.makeSuite(LogHelperTests))
    return suite

if __name__ == "__main__":
    unittest.main(defaultTest="test_suite")
