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

import base64
from functools import partial
import sys
import transaction

from zope.interface import implementer

from Testing.ZopeTestCase import interfaces
from Testing.ZopeTestCase import sandbox
from ZPublisher.httpexceptions import HTTPExceptionHandler


def savestate(func):
    '''Decorator saving thread local state before executing func
       and restoring it afterwards.
    '''
    from AccessControl.SecurityManagement import getSecurityManager
    from AccessControl.SecurityManagement import setSecurityManager
    from zope.component.hooks import getSite
    from zope.component.hooks import setSite

    def wrapped_func(*args, **kw):
        sm, site = getSecurityManager(), getSite()
        try:
            return func(*args, **kw)
        finally:
            setSecurityManager(sm)
            setSite(site)
    return wrapped_func


@implementer(interfaces.IFunctional)
class Functional(sandbox.Sandboxed):
    '''Derive from this class and an xTestCase to get functional
       testing support::

           class MyTest(Functional, ZopeTestCase):
               ...
    '''

    @savestate
    def publish(self, path, basic=None, env=None, extra=None,
                request_method='GET', stdin=None, handle_errors=True):
        '''Publishes the object at 'path' returning a response object.'''

        from io import BytesIO
        from ZPublisher.HTTPRequest import WSGIRequest as Request
        from ZPublisher.HTTPResponse import WSGIResponse
        from ZPublisher.WSGIPublisher import publish_module

        # Commit the sandbox for good measure
        transaction.commit()

        if env is None:
            env = {}
        if extra is None:
            extra = {}

        request = self.app.REQUEST

        env['SERVER_NAME'] = request['SERVER_NAME']
        env['SERVER_PORT'] = request['SERVER_PORT']
        env['SERVER_PROTOCOL'] = 'HTTP/1.1'
        env['REQUEST_METHOD'] = request_method

        p = path.split('?')
        if len(p) == 1:
            env['PATH_INFO'] = p[0]
        elif len(p) == 2:
            [env['PATH_INFO'], env['QUERY_STRING']] = p
        else:
            raise TypeError('')

        if basic:
            env['HTTP_AUTHORIZATION'] = "Basic %s" % base64.encodestring(basic)

        if stdin is None:
            stdin = BytesIO()

        outstream = BytesIO()
        response = WSGIResponse(stdout=outstream, stderr=sys.stderr)
        request = Request(stdin, env, response)
        for k, v in extra.items():
            request[k] = v

        wsgi_headers = BytesIO()

        def start_response(status, headers):
            response.setStatus(status.split()[0])
            for name, value in headers:
                response.setHeader(name, value)

            wsgi_headers.write('HTTP/1.1 %s\r\n' % status)
            headers = '\r\n'.join([': '.join(x) for x in headers])
            wsgi_headers.write(headers)
            wsgi_headers.write('\r\n\r\n')

        publish = partial(publish_module, _request=request, _response=response)
        if handle_errors:
            publish = HTTPExceptionHandler(publish)

        wsgi_result = publish(env, start_response)

        return ResponseWrapper(response, outstream, path,
                               wsgi_result, wsgi_headers)


class ResponseWrapper(object):
    '''Decorates a response object with additional introspective methods.'''

    def __init__(self, response, outstream, path,
                 wsgi_result=(), wsgi_headers=''):
        self._response = response
        self._outstream = outstream
        self._path = path
        self._wsgi_result = wsgi_result
        self._wsgi_headers = wsgi_headers

    def __getattr__(self, name):
        return getattr(self._response, name)

    def __str__(self):
        return self.getOutput()

    def getOutput(self):
        '''Returns the complete output, headers and all.'''
        return self._wsgi_headers.getvalue() + self.getBody()

    def getBody(self):
        '''Returns the page body, i.e. the output par headers.'''
        return ''.join(self._wsgi_result)

    def getPath(self):
        '''Returns the path used by the request.'''
        return self._path

    def getHeader(self, name):
        '''Returns the value of a response header.'''
        return self.headers.get(name.lower())

    def getCookie(self, name):
        '''Returns a response cookie.'''
        return self.cookies.get(name)
