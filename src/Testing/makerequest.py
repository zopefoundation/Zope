##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
"""
Facilitates unit tests which requires an acquirable REQUEST from
ZODB objects
"""

import os
from sys import stdin, stdout
from ZPublisher.HTTPRequest import HTTPRequest
from ZPublisher.HTTPResponse import HTTPResponse
from ZPublisher.BaseRequest import RequestContainer

def makerequest(app, stdout=stdout, environ=None):
    """
    Adds an HTTPRequest at app.REQUEST, and returns
    app.__of__(app.REQUEST). Useful for tests that need to acquire
    REQUEST.
    
    Usage:
      import makerequest
      app = makerequest.makerequest(app)

    You should only wrap the object used as 'root' in your tests.
    
    app is commonly a Zope2.app(), but that's not strictly necessary
    and frequently may be overkill; you can wrap other objects as long
    as they support acquisition and provide enough of the features of
    Zope2.app for your tests to run.  For example, if you want to call
    getPhysicalPath() on child objects, app must provide a
    non-recursive implementation of getPhysicalPath().

    *stdout* is an optional file-like object and is used by
    REQUEST.RESPONSE. The default is sys.stdout.

    *environ* is an optional mapping to be used in the request.
    Default is a fresh dictionary. Passing os.environ is not
    recommended; tests should not pollute the real os.environ.
    """
    if environ is None:
        environ = {}
    resp = HTTPResponse(stdout=stdout)
    environ.setdefault('SERVER_NAME', 'foo')
    environ.setdefault('SERVER_PORT', '80')
    environ.setdefault('REQUEST_METHOD',  'GET')
    req = HTTPRequest(stdin, environ, resp)
    req._steps = ['noobject']  # Fake a published object.
    req['ACTUAL_URL'] = req.get('URL') # Zope 2.7.4
    
    # set Zope3-style default skin so that the request is usable for
    # Zope3-style view look-ups.
    from zope.publisher.browser import setDefaultSkin
    setDefaultSkin(req)

    requestcontainer = RequestContainer(REQUEST = req)
    return app.__of__(requestcontainer)
