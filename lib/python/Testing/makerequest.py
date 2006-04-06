##############################################################################
#
# Copyright (c) 2002 Zope Corporation and Contributors. All Rights Reserved.
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

Usage:

    import makerequest
    app = makerequest.makerequest(Zope2.app())

You can optionally pass stdout to be used by the response,
and an environ mapping to be used in the request.
Defaults are sys.stdout and os.environ.

If you don't want to start a zope app in your test, you can wrap other
objects, but they must support acquisition and you should only wrap
your root object.


$Id$

"""

import os
from sys import stdin, stdout
from ZPublisher.HTTPRequest import HTTPRequest
from ZPublisher.HTTPResponse import HTTPResponse
from ZPublisher.BaseRequest import RequestContainer

def makerequest(app, stdout=stdout):
    resp = HTTPResponse(stdout=stdout)
    environ = os.environ
    environ['SERVER_NAME'] = 'foo'
    environ['SERVER_PORT'] = '80'
    environ['REQUEST_METHOD'] =  'GET'
    req = HTTPRequest(stdin, environ, resp)
    req._steps = ['noobject']  # Fake a published object.
    req['ACTUAL_URL'] = req.get('URL') # Zope 2.7.4
    
    # set Zope3-style default skin so that the request is usable for
    # Zope3-style view look-ups.
    from zope.app.publication.browser import setDefaultSkin
    setDefaultSkin(req)

    requestcontainer = RequestContainer(REQUEST = req)
    # Workaround for collector 2057: ensure that we don't break
    # getPhysicalPath if app has that method.
    # We could instead fix Traversable.getPhysicalPath() to check for
    # existence of p.getPhysicalPath before calling it; but it's such
    # a commonly called method that I don't want to impact performance
    # for something that AFAICT only affects makerequest() in
    # practice.
    if getattr(app, 'getPhysicalPath', None) is not None:
        requestcontainer.getPhysicalPath = lambda: ()

    return app.__of__(requestcontainer)
