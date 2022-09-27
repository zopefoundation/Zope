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

import sys
from functools import partial
from urllib.parse import unquote_to_bytes

import transaction
from Testing.ZopeTestCase import interfaces
from Testing.ZopeTestCase import sandbox
from zope.interface import implementer
from ZPublisher.httpexceptions import HTTPExceptionHandler
from ZPublisher.utils import basic_auth_encode


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

        query = ''
        if '?' in path:
            path, query = path.split("?", 1)
        env['PATH_INFO'] = unquote_to_bytes(path).decode('latin-1')
        env['QUERY_STRING'] = query

        if basic:
            env['HTTP_AUTHORIZATION'] = basic_auth_encode(basic)

        if not handle_errors:
            # Tell the publisher to skip exception views
            env['x-wsgiorg.throw_errors'] = True

        if stdin is None:
            stdin = BytesIO()
        env['wsgi.input'] = stdin

        outstream = BytesIO()
        response = WSGIResponse(stdout=outstream, stderr=sys.stderr)

        def request_factory(*args):
            request = Request(*args)
            for k, v in extra.items():
                request[k] = v
            return request

        wsgi_headers = BytesIO()

        def start_response(status, headers):
            # Keep the fake response in-sync with the actual values
            # from the WSGI start_response call.
            response.setStatus(status.split()[0])
            for key, value in headers:
                response.setHeader(key, value)

            wsgi_headers.write(
                b'HTTP/1.1 ' + status.encode('ascii') + b'\r\n')
            headers = b'\r\n'.join([
                (k + ': ' + v).encode('ascii') for k, v in headers])
            wsgi_headers.write(headers)
            wsgi_headers.write(b'\r\n\r\n')

        publish = partial(
            publish_module,
            _request_factory=request_factory,
            _response=response)
        if handle_errors:
            publish = HTTPExceptionHandler(publish)

        wsgi_result = publish(env, start_response)

        return ResponseWrapper(response, outstream, path,
                               wsgi_result, wsgi_headers)


class ResponseWrapper:
    '''Decorates a response object with additional introspective methods.'''

    def __init__(self, response, outstream, path,
                 wsgi_result=(), wsgi_headers=''):
        self._response = response
        self._outstream = outstream
        self._path = path
        self._wsgi_result = wsgi_result
        self._wsgi_headers = wsgi_headers

    def __getattr__(self, name):
        # This delegates introspection like getStatus to the fake
        # response class, though the actual values are part of the
        # _wsgi_headers / _wsgi_result. Might be better to ignore
        # the response and parse values out of the WSGI data instead.
        return getattr(self._response, name)

    def __bytes__(self):
        return self.getOutput()

    def __str__(self):
        return self._decode(self.getOutput())

    def getOutput(self):
        '''Returns the complete output, headers and all.'''
        return self._wsgi_headers.getvalue() + self.getBody()

    def getBody(self):
        '''Returns the page body, i.e. the output par headers.'''
        return b''.join(self._wsgi_result)

    def getPath(self):
        '''Returns the path used by the request.'''
        return self._path

    def getHeader(self, name):
        '''Returns the value of a response header.'''
        return self.headers.get(name.lower())

    def getCookie(self, name):
        '''Returns a response cookie.'''
        return self.cookies.get(name)

    def _decode(self, data):
        # This is a hack. This method is called to print a response
        # as part of a doctest. But if that response contains an
        # actual binary body, like a GIF image, there's no good
        # way to print that into the doctest output.
        try:
            return data.decode('utf-8')
        except UnicodeDecodeError:
            return data.decode('latin-1')
