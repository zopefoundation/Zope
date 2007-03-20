#############################################################################
#
# Copyright (c) 2007 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################

from ZPublisher.HTTPRequest import HTTPRequest

def makerequest(method):
    environ = dict(SERVER_NAME='foo', SERVER_PORT='80', REQUEST_METHOD=method)
    return HTTPRequest(None, environ, None)

def test_suite():
    from doctest import DocFileSuite
    return DocFileSuite('../requestmethod.txt',
                        globs=dict(GET=makerequest('GET'),
                                   POST=makerequest('POST')))

if __name__ == '__main__':
    import unittest
    unittest.main(defaultTest='test_suite')
