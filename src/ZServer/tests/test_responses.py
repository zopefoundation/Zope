##############################################################################
#
# Copyright (c) 2003 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################

"""Test general ZServer machinery."""

from ZServer.HTTPResponse import ZServerHTTPResponse
from ZServer.FTPResponse import FTPResponse
from ZServer.PCGIServer import PCGIResponse
from ZServer.FCGIServer import FCGIResponse
from ZPublisher.Iterators import IStreamIterator
from ZPublisher.pubevents import PubBeforeStreaming
from zope.interface import implements
import unittest
from cStringIO import StringIO

from zope.event import subscribers


class ZServerResponseTestCase(unittest.TestCase):
    """Test ZServer response objects."""

    def test_http_response_write_unicode(self):
        response = ZServerHTTPResponse()
        self.assertRaises(TypeError, response.write, u'bad')
    
    def test_ftp_response_write_unicode(self):
        response = FTPResponse()
        self.assertRaises(TypeError, response.write, u'bad')

    def test_pcgi_response_write_unicode(self):
        response = PCGIResponse()
        self.assertRaises(TypeError, response.write, u'bad')

    def test_fcgi_response_write_unicode(self):
        response = FCGIResponse()
        self.assertRaises(TypeError, response.write, u'bad')

    def test_setBodyIterator(self):
        channel = DummyChannel()
        one = ZServerHTTPResponse(stdout=channel)
        one.setHeader('content-length', 5)
        one.setBody(test_streamiterator())
        one.outputBody()
        all = channel.all()
        lines = all.split('\r\n')
        self.assertEqual(lines[-2], '')    # end of headers
        self.assertEqual(lines[-1], 'hello') # payload

    def test_setBodyIteratorFailsWithoutContentLength(self):
        one = ZServerHTTPResponse(stdout=DummyChannel())
        self.assertRaises(AssertionError,
                          one.setBody, test_streamiterator())
    
class DummyChannel:
    def __init__(self):
        self.out = StringIO()

    def all(self):
        self.out.seek(0)
        return self.out.read()

    def read(self):
        pass

    def write(self, data, len=None):
        try:
            if isinstance(data, str):
                self.out.write(data)
                return
        except TypeError:
            pass
        while 1:
            s = data.more()
            if not s:
                break
            self.out.write(s)

class test_streamiterator:
    implements(IStreamIterator)
    data = "hello"
    done = 0

    def next(self):
        if not self.done:
            self.done = 1
            return self.data
        raise StopIteration

class ZServerHTTPResponseTestCase(unittest.TestCase):
    """Test ZServer HTTPResponse object"""
    
    def _makeOne(self):
        return ZServerHTTPResponse()
    
    def testToString(self):
        response = self._makeOne()
        response.headers = {
            'content-type': 'text/plain',
            'all-lower-case': 'foo',
            'Title-Cased': 'bar',
            'mixed-CasED': 'spam',
            'multilined': 'eggs\n\tham'}
        response.accumulated_headers = [('foo-bar', 'bar'),
                                        ('Foo-bar', 'monty')]
        response.cookies = dict(foo=dict(value='bar'))
        response.body = 'A body\nwith multiple lines\n'
        
        result = str(response)
        headers, body = result.rsplit('\r\n\r\n')
        
        self.assertEqual(body, response.body)
        
        self.assertTrue(headers.startswith('HTTP/1.0 200 OK\r\n'))
        
        # 14 header lines all delimited by \r\n
        self.assertEqual(
            ['\n' in line for line in headers.split('\r\n')],
            14 * [False])
        
        self.assertTrue('Multilined: eggs\r\n\tham\r\n' in headers)
        self.assertTrue('Foo-bar: monty\r\n' in headers)
        self.assertTrue('Foo-Bar: bar\r\n' in headers)

    def _assertResponsesAreEqual(self, got, expected):
        got = got.split('\r\n')
        # Sort the headers into alphabetical order.
        headers = got[1:got.index('')]
        headers.sort()
        got[1:len(headers)+1] = headers
        # Compare line by line.
        for n in range(len(expected)):
            if expected[n].endswith('...'):
                m = len(expected[n]) - 3
                self.assertEqual(got[n][:m], expected[n][:m])
            else:
                self.assertEqual(got[n], expected[n])
        self.assertEqual(len(got), len(expected))

    def test_emptyResponse(self):
        # Empty repsonses have no Content-Length.
        response = self._makeOne()
        self._assertResponsesAreEqual(str(response),
                                      ('HTTP/1.0 204 No Content',
                                       'Connection: close',
                                       'Date: ...',
                                       'Server: ...',
                                       '',
                                       ''))

    def test_304(self):
        # Now we set the status to 304. 304 responses, according to RFC 2616,
        # should not have a content-length header. __str__ should not add it
        # back in if it is missing.
        response = self._makeOne()
        response.setStatus(304)
        self._assertResponsesAreEqual(str(response),
                                      ('HTTP/1.0 304 Not Modified',
                                       'Connection: close',
                                       'Date: ...',
                                       'Server: ...',
                                       '',
                                       ''))

    def test_304ContentLength(self):
        # __str__ should strip out Content-Length
        response = self._makeOne()
        response.setStatus(304)
        response.setHeader('content-length', '123')
        self._assertResponsesAreEqual(str(response),
                                      ('HTTP/1.0 304 Not Modified',
                                       'Connection: close',
                                       'Date: ...',
                                       'Server: ...',
                                       '',
                                       ''))

    def test_304ContentType(self):
        # __str__ should strip out Content-Type
        response = self._makeOne()
        response.setStatus(304)
        response.setHeader('content-type', 'text/plain')
        self._assertResponsesAreEqual(str(response),
                                      ('HTTP/1.0 304 Not Modified',
                                       'Connection: close',
                                       'Date: ...',
                                       'Server: ...',
                                       '',
                                       ''))
        
    def test_304ExplicitKeepAlive(self):
        # Explicit keep-alive connection header for HTTP 1.0.
        response = self._makeOne()
        response._http_connection = 'keep-alive'
        response.setStatus(304)
        self._assertResponsesAreEqual(str(response),
                                      ('HTTP/1.0 304 Not Modified',
                                       'Connection: Keep-Alive',
                                       'Date: ...',
                                       'Server: ...',
                                       '',
                                       ''))

    def test_304ImplicitKeepAlive(self):
        # Keep-alive is implicit for HTTP 1.1.
        response = self._makeOne()
        response._http_version = '1.1'
        response._http_connection = 'keep-alive'
        response.setStatus(304)
        self._assertResponsesAreEqual(str(response),
                                      ('HTTP/1.1 304 Not Modified',
                                       'Date: ...',
                                       'Server: ...',
                                       '',
                                       ''))

    def test_contentLength(self):
        # Check that __str__ adds in the correct Content-Length header.
        response = self._makeOne()
        response._http_version = '1.1'
        response._http_connection = 'keep-alive'
        response.body = '123456789'
        response.setHeader('Content-Type', 'text/plain')
        self._assertResponsesAreEqual(str(response),
                                      ('HTTP/1.1 200 OK',
                                       'Content-Length: 9',
                                       'Content-Type: text/plain',
                                       'Date: ...',
                                       'Server: ...',
                                       '',
                                       '123456789'))

    def test_emptyBody(self):
        # Check that a response with an empty message body returns a
        # Content-Length of 0. A common example of this is a 302 redirect.
        response = self._makeOne()
        response._http_version = '1.1'
        response._http_connection = 'keep-alive'
        response.redirect('somewhere')
        self._assertResponsesAreEqual(str(response),
                                      ('HTTP/1.1 302 Moved Temporarily',
                                       'Content-Length: 0',
                                       'Date: ...',
                                       'Location: somewhere',
                                       'Server: ...',
                                       '',
                                       ''))

    def test_HEAD(self):
        # A response to a HEAD request will have a non zero content
        # length and an empty body.
        response = self._makeOne()
        response._http_version = '1.1'
        response._http_connection = 'keep-alive'
        response.setHeader('Content-Type', 'text/plain')
        response.setHeader('Content-Length', 123)
        self._assertResponsesAreEqual(str(response),
                                      ('HTTP/1.1 200 OK',
                                       'Content-Length: 123',
                                       'Content-Type: text/plain',
                                       'Date: ...',
                                       'Server: ...',
                                       '',
                                       ''))

    def test_uses_accumulated_headers_correctly(self):
        response = self._makeOne()
        response.setStatus(304)
        response.addHeader('foo', 'bar')
        self.assertTrue('Foo: bar' in str(response))

class _Reporter(object):
    def __init__(self): self.events = []
    def __call__(self, event): self.events.append(event)

class ZServerHTTPResponseEventsTestCase(unittest.TestCase):

    def setUp(self):
        self._saved_subscribers = subscribers[:]
        self.reporter = r = _Reporter()
        subscribers[:] = [r]

    def tearDown(self):
        subscribers[:] = self._saved_subscribers
    
    def testStreaming(self):
        out = StringIO()
        response = ZServerHTTPResponse(stdout=out)
        response.write('datachunk1')
        response.write('datachunk2')
        
        events = self.reporter.events
        self.assertEqual(len(events), 1)
        self.assert_(isinstance(events[0], PubBeforeStreaming))
        self.assertEqual(events[0].response, response)
        
        self.assertTrue('datachunk1datachunk2' in out.getvalue())

def test_suite():
    suite = unittest.TestSuite()
    suite.addTests((
        unittest.makeSuite(ZServerResponseTestCase),
        unittest.makeSuite(ZServerHTTPResponseTestCase),
        unittest.makeSuite(ZServerHTTPResponseEventsTestCase)
    ))
    return suite
