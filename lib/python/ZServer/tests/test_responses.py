##############################################################################
#
# Copyright (c) 2003 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
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

def test_suite():
    return unittest.makeSuite(ZServerResponseTestCase)

if __name__ == "__main__":
    unittest.main(defaultTest="test_suite")
