##############################################################################
#
# Copyright (c) 2001 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
"""
Facilitates unit tests which requires an acquirable REQUEST from
ZODB objects

Usage:

    import makerequest
    app = makerequest.makerequest(Zope2.app())

$Id$

"""

import os
from os import environ
from sys import stdin, stdout
from ZPublisher.HTTPRequest import HTTPRequest
from ZPublisher.HTTPResponse import HTTPResponse
from ZPublisher.BaseRequest import RequestContainer

def makerequest(app, stdout=stdout):
    resp = HTTPResponse(stdout=stdout)
    environ['SERVER_NAME']='foo'
    environ['SERVER_PORT']='80'
    environ['REQUEST_METHOD'] = 'GET'
    req = HTTPRequest(stdin, environ, resp)
    return app.__of__(RequestContainer(REQUEST = req))
