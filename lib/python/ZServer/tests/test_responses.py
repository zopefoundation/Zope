##############################################################################
#
# Copyright (c) 2003 Zope Corporation and Contributors.
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
import unittest
from cStringIO import StringIO

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
    __implements__ = IStreamIterator
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
        response.accumulated_headers = 'foo-bar: bar\n\tbaz\nFoo-bar: monty\n'
        response.cookies = dict(foo=dict(value='bar'))
        response.body = 'A body\nwith multiple lines\n'
        
        result = str(response)
        headers, body = result.rsplit('\r\n\r\n')
        
        self.assertEqual(body, response.body)
        
        self.assertTrue(headers.startswith('HTTP/1.0 200 OK\r\n'))
        
        # 15 header lines all delimited by \r\n
        self.assertEqual(
            ['\n' in line for line in headers.split('\r\n')],
            15 * [False])

        self.assertTrue('Multilined: eggs\r\n\tham\r\n' in headers)
        self.assertTrue('Foo-Bar: bar\r\n\tbaz\r\n' in headers)
    
def test_suite():
    suite = unittest.TestSuite()
    suite.addTests((
        unittest.makeSuite(ZServerResponseTestCase),
        unittest.makeSuite(ZServerHTTPResponseTestCase)
    ))
    return suite

if __name__ == "__main__":
    unittest.main(defaultTest="test_suite")
