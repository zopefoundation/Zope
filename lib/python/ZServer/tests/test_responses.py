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
import unittest


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



def test_suite():
    return unittest.makeSuite(ZServerResponseTestCase)

if __name__ == "__main__":
    unittest.main(defaultTest="test_suite")
