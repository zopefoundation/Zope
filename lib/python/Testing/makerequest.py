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
from sys import stdin, stdout
from ZPublisher.HTTPRequest import HTTPRequest
from ZPublisher.HTTPResponse import HTTPResponse
from ZPublisher.BaseRequest import RequestContainer

def makerequest(app, stdout=stdout, **kw):
    resp = HTTPResponse(stdout=stdout)
    env = os.environ.copy()
    env['SERVER_NAME']='foo'
    env['SERVER_PORT']='80'
    env['REQUEST_METHOD'] = 'GET'
    env.update(kw)
    req = HTTPRequest(stdin, env, resp)
    return app.__of__(RequestContainer(REQUEST = req))
