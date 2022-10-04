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
"""Support for (functional) doc tests
"""

import doctest
import email.parser
import re
import sys
import warnings
from doctest import ELLIPSIS
from doctest import NORMALIZE_WHITESPACE
from doctest import REPORT_NDIFF
from functools import partial
from io import BytesIO

import transaction
from Testing.ZopeTestCase import Functional
from Testing.ZopeTestCase import FunctionalTestCase
from Testing.ZopeTestCase import ZopeTestCase
from Testing.ZopeTestCase import folder_name
from Testing.ZopeTestCase import standard_permissions
from Testing.ZopeTestCase import user_name
from Testing.ZopeTestCase import user_password
from Testing.ZopeTestCase import user_role
from Testing.ZopeTestCase.functional import ResponseWrapper
from Testing.ZopeTestCase.functional import savestate
from Testing.ZopeTestCase.sandbox import AppZapper
from ZPublisher.httpexceptions import HTTPExceptionHandler
from ZPublisher.utils import basic_auth_encode


class HTTPHeaderOutput:

    status = '200'
    reason = 'OK'

    def __init__(self, protocol, omit):
        self.headers = {}
        self.headersl = []
        self.protocol = protocol
        self.omit = omit

    def setResponseStatus(self, status, reason):
        self.status, self.reason = status, reason

    def setResponseHeaders(self, mapping):
        self.headers.update({
            '-'.join([s.capitalize() for s in name.split('-')]): v
            for name, v in mapping.items()
            if name.lower() not in self.omit
        })

    def appendResponseHeaders(self, lst):
        if lst and isinstance(lst[0], str):
            headers = [split_header(header) for header in lst]
        else:
            headers = lst
        self.headersl.extend(
            [('-'.join([s.capitalize() for s in name.split('-')]), v)
             for name, v in headers
             if name.lower() not in self.omit]
        )

    def __str__(self):
        out = ["%s: %s" % header for header in self.headers.items()]
        out.extend(["%s: %s" % header for header in self.headersl])
        out.sort()
        out.insert(0, f"{self.protocol} {self.status} {self.reason}")
        return '\n'.join(out)


class DocResponseWrapper(ResponseWrapper):
    """Response Wrapper for use in doctests
    """

    def __init__(self, response, outstream, path, header_output,
                 wsgi_result=(), wsgi_headers=''):
        ResponseWrapper.__init__(self, response, outstream, path,
                                 wsgi_result, wsgi_headers)
        self.header_output = header_output

    def __str__(self):
        body = self._decode(self.getBody())
        if body:
            return f"{self.header_output}\n\n{body}"
        return "%s\n" % (self.header_output)


basicre = re.compile(r'Basic (.+)?:(.+)?$')
headerre = re.compile(r'(\S+): (.+)$')


def split_header(header):
    return headerre.match(header).group(1, 2)


def auth_header(header):
    match = basicre.match(header)
    if match:
        u, p = match.group(1, 2)
        if u is None:
            u = ''
        if p is None:
            p = ''
        return basic_auth_encode(u, p)
    return header


def getRootFolder():
    return AppZapper().app()


def sync():
    getRootFolder()._p_jar.sync()


@savestate
def http(request_string, handle_errors=True):
    """Execute an HTTP request string via the publisher

    This is used for HTTP doc tests.
    """
    from urllib.parse import unquote_to_bytes

    from ZPublisher.HTTPRequest import WSGIRequest as Request
    from ZPublisher.HTTPResponse import WSGIResponse
    from ZPublisher.WSGIPublisher import publish_module

    # Commit work done by previous python code.
    transaction.commit()

    # Discard leading white space to make call layout simpler
    request_string = request_string.lstrip()

    # Split off and parse the command line
    newline = request_string.find('\n')
    command_line = request_string[:newline].rstrip()
    request_string = request_string[newline + 1:]
    method, path, protocol = command_line.split()

    env = {
        'HTTP_HOST': 'localhost',
        'HTTP_REFERER': 'localhost',
        'REQUEST_METHOD': method,
        'SERVER_PROTOCOL': protocol,
    }

    query = ''
    if '?' in path:
        path, query = path.split("?", 1)
    env['PATH_INFO'] = unquote_to_bytes(path).decode('latin-1')
    env['QUERY_STRING'] = query

    header_output = HTTPHeaderOutput(
        protocol, ('x-content-type-warning', 'x-powered-by'))

    # With a HeaderParser the payload is always a string, Parser would create a
    # list of messages for multipart messages.
    parser = email.parser.HeaderParser()
    msg = parser.parsestr(request_string)
    headers = msg.items()
    body = msg.get_payload()

    if isinstance(body, str):
        body = body.encode('utf-8')

    # Store request body without headers
    instream = BytesIO(body)

    for name, value in headers:
        name = ('_'.join(name.upper().split('-')))
        if name not in ('CONTENT_TYPE', 'CONTENT_LENGTH'):
            name = 'HTTP_' + name
        env[name] = value.rstrip()

    if 'HTTP_AUTHORIZATION' in env:
        env['HTTP_AUTHORIZATION'] = auth_header(env['HTTP_AUTHORIZATION'])

    if not handle_errors:
        # Tell the publisher to skip exception views
        env['x-wsgiorg.throw_errors'] = True

    outstream = BytesIO()
    response = WSGIResponse(stdout=outstream, stderr=sys.stderr)

    env['wsgi.input'] = instream
    wsgi_headers = BytesIO()

    def start_response(status, headers):
        wsgi_headers.write(
            b'HTTP/1.1 ' + status.encode('ascii') + b'\r\n')
        headers = b'\r\n'.join([
            (k + ': ' + v).encode('ascii') for k, v in headers])
        wsgi_headers.write(headers)
        wsgi_headers.write(b'\r\n\r\n')

    publish = partial(
        publish_module,
        _request_factory=Request,
        _response=response)
    if handle_errors:
        publish = HTTPExceptionHandler(publish)

    wsgi_result = publish(env, start_response)

    header_output.setResponseStatus(response.getStatus(), response.errmsg)
    header_output.setResponseHeaders(response.headers)
    header_output.headersl.extend(response._cookie_list())
    header_output.appendResponseHeaders(response.accumulated_headers)

    sync()

    return DocResponseWrapper(
        response, outstream, path, header_output, wsgi_result, wsgi_headers)


class ZopeSuiteFactory:

    def __init__(self, *args, **kw):
        self._args = args
        self._kw = kw
        self._layer = None
        self.setup_globs()
        self.setup_test_class()
        self.setup_optionflags()

    def doctestsuite(self):
        suite = doctest.DocTestSuite(*self._args, **self._kw)
        if self._layer is not None:
            suite.layer = self._layer
        return suite

    def docfilesuite(self):
        suite = doctest.DocFileSuite(*self._args, **self._kw)
        if self._layer is not None:
            suite.layer = self._layer
        return suite

    def setup_globs(self):
        globs = self._kw.setdefault('globs', {})
        globs['folder_name'] = folder_name
        globs['user_name'] = user_name
        globs['user_password'] = user_password
        globs['user_role'] = user_role
        globs['standard_permissions'] = standard_permissions

    def setup_test_class(self):
        test_class = self._kw.get('test_class', ZopeTestCase)

        if 'test_class' in self._kw:
            del self._kw['test_class']

        if hasattr(test_class, 'layer'):
            self._layer = test_class.layer

        # If the test_class does not have a runTest method, we add
        # a dummy attribute so that TestCase construction works.
        # runTest may get called, so set it to something that works.
        if not hasattr(test_class, 'runTest'):
            setattr(test_class, 'runTest', lambda x: None)

        # Create a TestCase instance which will be used to execute
        # the setUp and tearDown methods, as well as be passed into
        # the test globals as 'self'.
        test_instance = test_class()

        kwsetUp = self._kw.get('setUp')

        def setUp(test):
            test_instance.setUp()
            test.globs['test'] = test
            test.globs['self'] = test_instance
            if hasattr(test_instance, 'app'):
                test.globs['app'] = test_instance.app
            if hasattr(test_instance, 'folder'):
                test.globs['folder'] = test_instance.folder
            if hasattr(test_instance, 'portal'):
                test.globs['portal'] = test_instance.portal
                test.globs['portal_name'] = test_instance.portal.getId()
            test_instance.globs = test.globs
            if kwsetUp is not None:
                kwsetUp(test_instance)

        self._kw['setUp'] = setUp

        kwtearDown = self._kw.get('tearDown')

        def tearDown(test):
            if kwtearDown is not None:
                kwtearDown(test_instance)
            test_instance.tearDown()

        self._kw['tearDown'] = tearDown

    def setup_optionflags(self):
        if 'optionflags' not in self._kw:
            self._kw['optionflags'] = (ELLIPSIS | NORMALIZE_WHITESPACE)


class FunctionalSuiteFactory(ZopeSuiteFactory):

    def setup_globs(self):
        ZopeSuiteFactory.setup_globs(self)
        globs = self._kw.setdefault('globs', {})
        globs['http'] = http
        globs['getRootFolder'] = getRootFolder
        globs['sync'] = sync
        globs['user_auth'] = basic_auth_encode(user_name, user_password)

    def setup_test_class(self):
        test_class = self._kw.get('test_class', FunctionalTestCase)

        # If the passed-in test_class doesn't subclass Functional,
        # we mix it in for you, but we will issue a warning.
        if not issubclass(test_class, Functional):
            name = test_class.__name__
            warnings.warn(("The test_class you are using doesn't "
                           "subclass from ZopeTestCase.Functional. "
                           "Please fix that."), UserWarning, 4)
            if 'Functional' not in name:
                name = 'Functional%s' % name
            test_class = type(name, (Functional, test_class), {})

        self._kw['test_class'] = test_class
        ZopeSuiteFactory.setup_test_class(self)

    def setup_optionflags(self):
        if 'optionflags' not in self._kw:
            self._kw['optionflags'] = (
                ELLIPSIS | REPORT_NDIFF | NORMALIZE_WHITESPACE)


def ZopeDocTestSuite(module=None, **kw):
    module = doctest._normalize_module(module)
    return ZopeSuiteFactory(module, **kw).doctestsuite()


def ZopeDocFileSuite(*paths, **kw):
    if kw.get('module_relative', True):
        kw['package'] = doctest._normalize_module(kw.get('package'))
    return ZopeSuiteFactory(*paths, **kw).docfilesuite()


def FunctionalDocTestSuite(module=None, **kw):
    module = doctest._normalize_module(module)
    return FunctionalSuiteFactory(module, **kw).doctestsuite()


def FunctionalDocFileSuite(*paths, **kw):
    if kw.get('module_relative', True):
        kw['package'] = doctest._normalize_module(kw.get('package'))
    return FunctionalSuiteFactory(*paths, **kw).docfilesuite()


__all__ = [
    'ZopeDocTestSuite',
    'ZopeDocFileSuite',
    'FunctionalDocTestSuite',
    'FunctionalDocFileSuite',
]
