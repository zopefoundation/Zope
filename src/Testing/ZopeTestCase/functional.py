##############################################################################
#
# Copyright (c) 2005 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Support for functional unit testing in ZTC

After Marius Gedminas' functional.py module for Zope3.
"""

import sys, re, base64
import transaction
import sandbox
import interfaces

from zope.interface import implements


def savestate(func):
    '''Decorator saving thread local state before executing func
       and restoring it afterwards.
    '''
    from AccessControl.SecurityManagement import getSecurityManager
    from AccessControl.SecurityManagement import setSecurityManager
    from zope.site.hooks import getSite
    from zope.site.hooks import setSite

    def wrapped_func(*args, **kw):
        sm, site = getSecurityManager(), getSite()
        try:
            return func(*args, **kw)
        finally:
            setSecurityManager(sm)
            setSite(site)
    return wrapped_func


class Functional(sandbox.Sandboxed):
    '''Derive from this class and an xTestCase to get functional
       testing support::

           class MyTest(Functional, ZopeTestCase):
               ...
    '''

    implements(interfaces.IFunctional)

    @savestate
    def publish(self, path, basic=None, env=None, extra=None,
                request_method='GET', stdin=None, handle_errors=True):
        '''Publishes the object at 'path' returning a response object.'''

        from StringIO import StringIO
        from ZPublisher.Request import Request
        from ZPublisher.Response import Response
        from ZPublisher.Publish import publish_module

        # Commit the sandbox for good measure
        transaction.commit()

        if env is None:
            env = {}
        if extra is None:
            extra = {}

        request = self.app.REQUEST

        env['SERVER_NAME'] = request['SERVER_NAME']
        env['SERVER_PORT'] = request['SERVER_PORT']
        env['REQUEST_METHOD'] = request_method

        p = path.split('?')
        if len(p) == 1:
            env['PATH_INFO'] = p[0]
        elif len(p) == 2:
            [env['PATH_INFO'], env['QUERY_STRING']] = p
        else:
            raise TypeError, ''

        if basic:
            env['HTTP_AUTHORIZATION'] = "Basic %s" % base64.encodestring(basic)

        if stdin is None:
            stdin = StringIO()

        outstream = StringIO()
        response = Response(stdout=outstream, stderr=sys.stderr)
        request = Request(stdin, env, response)
        for k, v in extra.items():
            request[k] = v

        publish_module('Zope2',
                       debug=not handle_errors,
                       request=request,
                       response=response,
                      )

        return ResponseWrapper(response, outstream, path)


class ResponseWrapper:
    '''Decorates a response object with additional introspective methods.'''

    _bodyre = re.compile('\r\n\r\n(.*)', re.MULTILINE | re.DOTALL)

    def __init__(self, response, outstream, path):
        self._response = response
        self._outstream = outstream
        self._path = path

    def __getattr__(self, name):
        return getattr(self._response, name)

    def getOutput(self):
        '''Returns the complete output, headers and all.'''
        return self._outstream.getvalue()

    def getBody(self):
        '''Returns the page body, i.e. the output par headers.'''
        body = self._bodyre.search(self.getOutput())
        if body is not None:
            body = body.group(1)
        return body

    def getPath(self):
        '''Returns the path used by the request.'''
        return self._path

    def getHeader(self, name):
        '''Returns the value of a response header.'''
        return self.headers.get(name.lower())

    def getCookie(self, name):
        '''Returns a response cookie.'''
        return self.cookies.get(name)

