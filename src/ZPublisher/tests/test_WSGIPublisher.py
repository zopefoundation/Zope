##############################################################################
#
# Copyright (c) 2009 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
import io
import unittest
from urllib.parse import quote

import Testing.testbrowser
import transaction
from Testing.ZopeTestCase import FunctionalTestCase
from Testing.ZopeTestCase import ZopeTestCase
from Testing.ZopeTestCase import user_name
from zExceptions import NotFound
from ZODB.POSException import ConflictError
from zope.interface.common.interfaces import IException
from zope.publisher.interfaces import INotFound
from zope.security.interfaces import IForbidden
from zope.security.interfaces import IUnauthorized
from ZPublisher.WSGIPublisher import get_module_info


class WSGIResponseTests(unittest.TestCase):

    _old_NOW = None

    def tearDown(self):
        if self._old_NOW is not None:
            self._setNOW(self._old_NOW)

    def _getTargetClass(self):
        from ZPublisher.HTTPResponse import WSGIResponse
        return WSGIResponse

    def _makeOne(self, *args, **kw):
        return self._getTargetClass()(*args, **kw)

    def _setNOW(self, value):
        from ZPublisher import HTTPResponse
        HTTPResponse._NOW, self._old_NOW = value, HTTPResponse._NOW

    def test_finalize_sets_204_on_empty_not_streaming(self):
        response = self._makeOne()
        response.finalize()
        self.assertEqual(response.status, 204)

    def test_finalize_sets_204_on_empty_not_streaming_ignores_non_200(self):
        response = self._makeOne()
        response.setStatus(302)
        response.finalize()
        self.assertEqual(response.status, 302)

    def test_finalize_sets_content_length_if_missing(self):
        response = self._makeOne()
        response.setBody('TESTING')
        response.finalize()
        self.assertEqual(response.getHeader('Content-Length'), '7')

    def test_finalize_skips_content_length_if_missing_w_streaming(self):
        response = self._makeOne()
        response._streaming = True
        response.body = 'TESTING'
        response.finalize()
        self.assertFalse(response.getHeader('Content-Length'))

    def test_listHeaders_skips_Server_header_wo_server_version_set(self):
        response = self._makeOne()
        response.setBody('TESTING')
        headers = response.listHeaders()
        sv = [x for x in headers if x[0] == 'Server']
        self.assertFalse(sv)

    def test_listHeaders_includes_Server_header_w_server_version_set(self):
        response = self._makeOne()
        response._server_version = 'TESTME'
        response.setBody('TESTING')
        headers = response.listHeaders()
        sv = [x for x in headers if x[0] == 'Server']
        self.assertTrue(('Server', 'TESTME') in sv)

    def test_listHeaders_includes_Date_header(self):
        import time
        WHEN = time.localtime()
        self._setNOW(time.mktime(WHEN))
        response = self._makeOne()
        response.setBody('TESTING')
        headers = response.listHeaders()
        whenstr = time.strftime('%a, %d %b %Y %H:%M:%S GMT',
                                time.gmtime(time.mktime(WHEN)))
        self.assertIn(('Date', whenstr), headers)

    def test_setBody_IUnboundStreamIterator(self):
        from zope.interface import implementer
        from ZPublisher.Iterators import IUnboundStreamIterator

        @implementer(IUnboundStreamIterator)
        class TestStreamIterator:
            data = "hello"
            done = 0

            def __next__(self):
                if not self.done:
                    self.done = 1
                    return self.data
                raise StopIteration

            next = __next__

        response = self._makeOne()
        response.setStatus(200)
        body = TestStreamIterator()
        response.setBody(body)
        response.finalize()
        self.assertTrue(body is response.body)
        self.assertEqual(response._streaming, 1)

    def test_setBody_IStreamIterator(self):
        from zope.interface import implementer
        from ZPublisher.Iterators import IStreamIterator

        @implementer(IStreamIterator)
        class TestStreamIterator:
            data = "hello"
            done = 0

            def __next__(self):
                if not self.done:
                    self.done = 1
                    return self.data
                raise StopIteration

            next = __next__

            def __len__(self):
                return len(self.data)

        response = self._makeOne()
        response.setStatus(200)
        body = TestStreamIterator()
        response.setBody(body)
        response.finalize()
        self.assertTrue(body is response.body)
        self.assertEqual(response._streaming, 0)
        self.assertEqual(response.getHeader('Content-Length'),
                         '%d' % len(TestStreamIterator.data))

    def test_setBody_w_locking(self):
        response = self._makeOne()
        response.setBody(b'BEFORE', lock=True)
        result = response.setBody(b'AFTER')
        self.assertFalse(result)
        self.assertEqual(response.body, b'BEFORE')

    def test___str___raises(self):
        response = self._makeOne()
        response.setBody('TESTING')
        self.assertRaises(NotImplementedError, lambda: str(response))

    def test_exception_calls_unauthorized(self):
        from zExceptions import Unauthorized
        response = self._makeOne()
        _unauthorized = DummyCallable()
        response._unauthorized = _unauthorized
        with self.assertRaises(Unauthorized):
            response.exception(info=(Unauthorized, Unauthorized('fail'), None))
        self.assertEqual(_unauthorized._called_with, ((), {}))

    def test_debugError(self):
        response = self._makeOne()
        try:
            response.debugError('testing')
        except NotFound as raised:
            self.assertEqual(response.status, 404)
            self.assertIn(
                "Zope has encountered a problem publishing your object. <p>'testing'</p>",  # noqa: E501
                raised.detail,
            )
        else:
            self.fail("Didn't raise NotFound")
        try:
            response.debugError(("testing",))
        except NotFound as raised:
            self.assertEqual(response.status, 404)
            self.assertIn(
                "Zope has encountered a problem publishing your object. <p>(\'testing\',)</p>",  # noqa: E501
                raised.detail,
            )
        else:
            self.fail("Didn't raise NotFound")
        try:
            response.debugError(("foo", "bar"))
        except NotFound as raised:
            self.assertEqual(response.status, 404)
            self.assertIn(
                "Zope has encountered a problem publishing your object. <p>(\'foo\', \'bar\')</p>",  # noqa: E501
                raised.detail,
            )
        else:
            self.fail("Didn't raise NotFound")


class TestPublish(unittest.TestCase):

    def _callFUT(self, request, module_info=None):
        from ZPublisher.WSGIPublisher import publish
        if module_info is None:
            module_info = get_module_info()

        return publish(request, module_info)

    def test_wo_REMOTE_USER(self):
        request = DummyRequest(PATH_INFO='/')
        response = request.response = DummyResponse()
        _object = DummyCallable()
        _object._result = 'RESULT'
        request._traverse_to = _object
        _realm = 'TESTING'
        _debug_mode = True
        returned = self._callFUT(request, (_object, _realm, _debug_mode))
        self.assertTrue(returned is response)
        self.assertTrue(request._processedInputs)
        self.assertTrue(response.debug_mode)
        self.assertEqual(response.realm, 'TESTING')
        self.assertEqual(request['PARENTS'], [_object])
        self.assertEqual(request._traversed[:2], ('/', None))
        self.assertEqual(_object._called_with, ((), {}))
        self.assertEqual(response._body, 'RESULT')

    def test_w_REMOTE_USER(self):
        request = DummyRequest(PATH_INFO='/', REMOTE_USER='phred')
        response = request.response = DummyResponse()
        _object = DummyCallable()
        _object._result = 'RESULT'
        request._traverse_to = _object
        _realm = 'TESTING'
        _debug_mode = True
        self._callFUT(request, (_object, _realm, _debug_mode))
        self.assertEqual(response.realm, None)


class TestPublishModule(ZopeTestCase):

    def _callFUT(self, environ, start_response,
                 _publish=None, _response_factory=None, _request_factory=None):
        from ZPublisher.WSGIPublisher import publish_module
        if _publish is not None:
            if _response_factory is not None:
                if _request_factory is not None:
                    return publish_module(environ, start_response,
                                          _publish=_publish,
                                          _response_factory=_response_factory,
                                          _request_factory=_request_factory)
                return publish_module(environ, start_response,
                                      _publish=_publish,
                                      _response_factory=_response_factory)
            else:
                if _request_factory is not None:
                    return publish_module(environ, start_response,
                                          _publish=_publish,
                                          _request_factory=_request_factory)
                return publish_module(environ, start_response,
                                      _publish=_publish)
        return publish_module(environ, start_response)

    def _registerView(self, factory, name, provides=None):
        from OFS.interfaces import IApplication
        from zope.component import provideAdapter
        from zope.interface import Interface
        from zope.publisher.browser import IDefaultBrowserLayer
        if provides is None:
            provides = Interface
        requires = (IApplication, IDefaultBrowserLayer)
        provideAdapter(factory, requires, provides, name)

    def _makeEnviron(self, **kw):
        from io import BytesIO
        environ = {
            'SCRIPT_NAME': '',
            'REQUEST_METHOD': 'GET',
            'QUERY_STRING': '',
            'SERVER_NAME': '127.0.0.1',
            'REMOTE_ADDR': '127.0.0.1',
            'wsgi.url_scheme': 'http',
            'SERVER_PORT': '8080',
            'HTTP_HOST': '127.0.0.1:8080',
            'SERVER_PROTOCOL': 'HTTP/1.1',
            'wsgi.input': BytesIO(b''),
            'CONTENT_LENGTH': '0',
            'HTTP_CONNECTION': 'keep-alive',
            'CONTENT_TYPE': ''
        }
        environ.update(kw)
        return environ

    def test_calls_setDefaultSkin(self):
        from zope.traversing.interfaces import ITraversable
        from zope.traversing.namespace import view

        class TestView:
            __name__ = 'testing'

            def __init__(self, context, request):
                pass

            def __call__(self):
                return 'foobar'

        # Define the views
        self._registerView(TestView, 'testing')

        # Bind the 'view' namespace (for @@ traversal)
        self._registerView(view, 'view', ITraversable)

        environ = self._makeEnviron(PATH_INFO='/@@testing')
        self.assertEqual(self._callFUT(environ, noopStartResponse),
                         (b'', b'foobar'))

    def test_publish_can_return_new_response(self):
        from ZPublisher.HTTPRequest import HTTPRequest
        _response = DummyResponse()
        _response.body = b'BODY'
        _after1 = DummyCallable()
        _after2 = DummyCallable()
        _response.after_list = (_after1, _after2)
        environ = self._makeEnviron()
        start_response = DummyCallable()
        _publish = DummyCallable()
        _publish._result = _response
        app_iter = self._callFUT(environ, start_response, _publish)
        self.assertEqual(app_iter, (b'', b'BODY'))
        (status, headers), kw = start_response._called_with
        self.assertEqual(status, '204 No Content')
        self.assertEqual(headers, [('Content-Length', '0')])
        self.assertEqual(kw, {})
        (request, module_info), kw = _publish._called_with
        self.assertIsInstance(request, HTTPRequest)
        self.assertEqual(kw, {})
        self.assertTrue(_response._finalized)
        self.assertEqual(_after1._called_with, ((), {}))
        self.assertEqual(_after2._called_with, ((), {}))

    def test_publish_returns_data_witten_to_response_before_body(self):
        # This also happens if publish creates a new response object.
        from ZPublisher.HTTPResponse import WSGIResponse
        environ = self._makeEnviron()
        start_response = DummyCallable()

        def _publish(request, mod_info):
            response = WSGIResponse()
            response.write(b'WRITTEN')
            response.body = b'BODY'
            return response

        app_iter = self._callFUT(environ, start_response, _publish)
        self.assertEqual(app_iter, (b'WRITTEN', b'BODY'))

    def test_raises_unauthorized(self):
        from zExceptions import Unauthorized
        environ = self._makeEnviron()
        start_response = DummyCallable()
        _publish = DummyCallable()
        _publish._raise = Unauthorized('TESTING')
        try:
            self._callFUT(environ, start_response, _publish)
        except Unauthorized as exc:
            self.assertEqual(exc.getStatus(), 401)
            self.assertEqual(
                exc.headers['WWW-Authenticate'], 'basic realm="Zope"')

    def test_raises_redirect(self):
        from zExceptions import Redirect
        environ = self._makeEnviron()
        start_response = DummyCallable()
        _publish = DummyCallable()
        _publish._raise = Redirect('/redirect_to')
        try:
            self._callFUT(environ, start_response, _publish)
        except Redirect as exc:
            self.assertEqual(exc.getStatus(), 302)
            self.assertEqual(exc.headers['Location'], '/redirect_to')

    def test_upgrades_ztk_not_found(self):
        from zExceptions import NotFound
        from zope.publisher.interfaces import NotFound as ZTK_NotFound
        environ = self._makeEnviron()
        start_response = DummyCallable()
        _publish = DummyCallable()
        _publish._raise = ZTK_NotFound(object(), 'name_not_found')
        try:
            self._callFUT(environ, start_response, _publish)
        except ZTK_NotFound:
            self.fail('ZTK exception raised, expected zExceptions.')
        except NotFound as exc:
            self.assertTrue('name_not_found' in str(exc))

    def test_response_body_is_file(self):
        from io import BytesIO

        class DummyFile(BytesIO):
            def __init__(self):
                pass

            def read(self, *args, **kw):
                raise NotImplementedError()

        _response = DummyResponse()
        _response._status = '200 OK'
        _response._headers = [('Content-Length', '4')]
        body = _response.body = DummyFile()
        environ = self._makeEnviron()
        start_response = DummyCallable()
        _publish = DummyCallable()
        _publish._result = _response
        app_iter = self._callFUT(environ, start_response, _publish)
        self.assertTrue(app_iter is body)

    def test_response_is_stream(self):
        from zope.interface import implementer
        from ZPublisher.Iterators import IStreamIterator

        @implementer(IStreamIterator)
        class TestStreamIterator:
            data = "hello"
            done = 0

            def __next__(self):
                if not self.done:
                    self.done = 1
                    return self.data
                raise StopIteration

            next = __next__

        _response = DummyResponse()
        _response._status = '200 OK'
        _response._headers = [('Content-Length', '4')]
        body = _response.body = TestStreamIterator()
        environ = self._makeEnviron()
        start_response = DummyCallable()
        _publish = DummyCallable()
        _publish._result = _response
        app_iter = self._callFUT(environ, start_response, _publish)
        self.assertTrue(app_iter is body)

    def test_response_is_unboundstream(self):
        from zope.interface import implementer
        from ZPublisher.Iterators import IUnboundStreamIterator

        @implementer(IUnboundStreamIterator)
        class TestUnboundStreamIterator:
            data = "hello"
            done = 0

            def __next__(self):
                if not self.done:
                    self.done = 1
                    return self.data
                raise StopIteration

            next = __next__

        _response = DummyResponse()
        _response._status = '200 OK'
        body = _response.body = TestUnboundStreamIterator()
        environ = self._makeEnviron()
        start_response = DummyCallable()
        _publish = DummyCallable()
        _publish._result = _response
        app_iter = self._callFUT(environ, start_response, _publish)
        self.assertTrue(app_iter is body)

    def test_stream_file_wrapper(self):
        from zope.interface import implementer
        from ZPublisher.HTTPResponse import WSGIResponse
        from ZPublisher.Iterators import IStreamIterator

        @implementer(IStreamIterator)
        class TestStreamIterator:
            data = "hello" * 20

            def __len__(self):
                return len(self.data)

            def read(self):
                return self.data

        class Wrapper:
            def __init__(self, file):
                self.file = file

        _response = WSGIResponse()
        _response.setHeader('Content-Type', 'text/plain')
        body = _response.body = TestStreamIterator()
        environ = self._makeEnviron(**{'wsgi.file_wrapper': Wrapper})
        start_response = DummyCallable()
        _publish = DummyCallable()
        _publish._result = _response
        app_iter = self._callFUT(environ, start_response, _publish)
        self.assertTrue(app_iter.file is body)
        self.assertTrue(isinstance(app_iter, Wrapper))
        self.assertEqual(
            int(_response.headers['content-length']), len(body))
        self.assertTrue(
            _response.headers['content-type'].startswith('text/plain'))
        self.assertEqual(_response.status, 200)

    def test_unboundstream_file_wrapper(self):
        from zope.interface import implementer
        from ZPublisher.HTTPResponse import WSGIResponse
        from ZPublisher.Iterators import IUnboundStreamIterator

        @implementer(IUnboundStreamIterator)
        class TestUnboundStreamIterator:
            data = "hello"

            def __len__(self):
                return len(self.data)

            def read(self):
                return self.data

        class Wrapper:
            def __init__(self, file):
                self.file = file

        _response = WSGIResponse()
        _response.setStatus(200)
        # UnboundStream needs Content-Length header
        _response.setHeader('Content-Length', '5')
        _response.setHeader('Content-Type', 'text/plain')
        body = _response.body = TestUnboundStreamIterator()
        environ = self._makeEnviron(**{'wsgi.file_wrapper': Wrapper})
        start_response = DummyCallable()
        _publish = DummyCallable()
        _publish._result = _response
        app_iter = self._callFUT(environ, start_response, _publish)
        self.assertTrue(app_iter.file is body)
        self.assertTrue(isinstance(app_iter, Wrapper))
        self.assertEqual(
            int(_response.headers['content-length']), len(body))
        self.assertTrue(
            _response.headers['content-type'].startswith('text/plain'))
        self.assertEqual(_response.status, 200)

    def test_stream_file_wrapper_without_read(self):
        from zope.interface import implementer
        from ZPublisher.HTTPResponse import WSGIResponse
        from ZPublisher.Iterators import IStreamIterator

        @implementer(IStreamIterator)
        class TestStreamIterator:
            data = "hello" * 20

            def __len__(self):
                return len(self.data)

        class Wrapper:
            def __init__(self, file):
                self.file = file

        _response = WSGIResponse()
        _response.setHeader('Content-Type', 'text/plain')
        body = _response.body = TestStreamIterator()
        environ = self._makeEnviron(**{'wsgi.file_wrapper': Wrapper})
        start_response = DummyCallable()
        _publish = DummyCallable()
        _publish._result = _response
        app_iter = self._callFUT(environ, start_response, _publish)
        # The stream iterator has no ``read`` and will not be used
        # for ``wsgi.file_wrapper``. It is returned as-is.
        self.assertTrue(app_iter is body)
        self.assertTrue(isinstance(app_iter, TestStreamIterator))
        self.assertEqual(
            int(_response.headers['content-length']), len(body))
        self.assertTrue(
            _response.headers['content-type'].startswith('text/plain'))
        self.assertEqual(_response.status, 200)

    def test_request_closed(self):
        environ = self._makeEnviron()
        start_response = DummyCallable()
        _request = DummyRequest()
        _request._closed = False

        def _close():
            _request._closed = True
        _request.close = _close

        def _request_factory(stdin, environ, response):
            return _request
        _publish = DummyCallable()
        _publish._result = DummyResponse()
        self._callFUT(environ, start_response, _publish,
                      _request_factory=_request_factory)
        self.assertTrue(_request._closed)

    def test_handle_ConflictError(self):
        environ = self._makeEnviron()
        start_response = DummyCallable()

        def _publish(request, module_info):
            if request.retry_count < 1:
                raise ConflictError
            response = DummyResponse()
            response.setBody(request.other.get('method'))
            return response

        try:
            from ZPublisher.HTTPRequest import HTTPRequest
            original_retry_max_count = HTTPRequest.retry_max_count
            HTTPRequest.retry_max_count = 1
            # After the retry the request has a filled `other` dict, thus the
            # new request is not closed before processing it:
            self.assertEqual(
                self._callFUT(environ, start_response, _publish), (b'', 'GET'))
        finally:
            HTTPRequest.retry_max_count = original_retry_max_count

    def testCustomExceptionViewConflictErrorHandling(self):
        # Make sure requests are retried as often as configured
        # even if an exception view has been registered that
        # matches ConflictError
        from zope.interface import directlyProvides
        from zope.publisher.browser import IDefaultBrowserLayer
        registerExceptionView(Exception)
        environ = self._makeEnviron()
        start_response = DummyCallable()
        _publish = DummyCallable()
        _publish._raise = ConflictError('oops')
        _request = DummyRequest()
        directlyProvides(_request, IDefaultBrowserLayer)
        _request.response = DummyResponse()
        _request.retry_count = 0
        _request.retry_max_count = 2
        _request.environ = {}

        def _close():
            pass
        _request.close = _close

        def _retry():
            _request.retry_count += 1
            return _request
        _request.retry = _retry

        def _supports_retry():
            return _request.retry_count < _request.retry_max_count
        _request.supports_retry = _supports_retry

        def _request_factory(stdin, environ, response):
            return _request

        # At first, retry_count is zero. Request has never been retried.
        self.assertEqual(_request.retry_count, 0)
        app_iter = self._callFUT(environ, start_response, _publish,
                                 _request_factory=_request_factory)

        # In the end the error view is rendered, but the request should
        # have been retried up to retry_max_count times
        self.assertTrue(app_iter[1].startswith(
            'Exception View: ConflictError'))
        self.assertEqual(_request.retry_count, _request.retry_max_count)

        # The Content-Type response header should be set to text/html
        self.assertIn('text/html', _request.response.getHeader('Content-Type'))

        unregisterExceptionView(Exception)

    def testCustomExceptionViewUnauthorized(self):
        from AccessControl import Unauthorized
        registerExceptionView(IUnauthorized)
        environ = self._makeEnviron()
        start_response = DummyCallable()
        _publish = DummyCallable()
        _publish._raise = Unauthorized('argg')
        app_iter = self._callFUT(environ, start_response, _publish)
        body = b''.join(app_iter)
        self.assertEqual(start_response._called_with[0][0], '401 Unauthorized')
        self.assertTrue(b'Exception View: Unauthorized' in body)
        unregisterExceptionView(IUnauthorized)

    def testCustomExceptionViewForbidden(self):
        from zExceptions import Forbidden
        registerExceptionView(IForbidden)
        environ = self._makeEnviron()
        start_response = DummyCallable()
        _publish = DummyCallable()
        _publish._raise = Forbidden('argh')
        app_iter = self._callFUT(environ, start_response, _publish)
        body = b''.join(app_iter)
        self.assertEqual(start_response._called_with[0][0], '403 Forbidden')
        self.assertTrue(b'Exception View: Forbidden' in body)
        unregisterExceptionView(IForbidden)

    def testCustomExceptionViewNotFound(self):
        from zExceptions import NotFound
        registerExceptionView(INotFound)
        environ = self._makeEnviron()
        start_response = DummyCallable()
        _publish = DummyCallable()
        _publish._raise = NotFound('argh')
        app_iter = self._callFUT(environ, start_response, _publish)
        body = b''.join(app_iter)
        self.assertEqual(start_response._called_with[0][0], '404 Not Found')
        self.assertTrue(b'Exception View: NotFound' in body)
        unregisterExceptionView(INotFound)

    def testCustomExceptionViewZTKNotFound(self):
        from zope.publisher.interfaces import NotFound as ZTK_NotFound
        registerExceptionView(INotFound)
        environ = self._makeEnviron()
        start_response = DummyCallable()
        _publish = DummyCallable()
        _publish._raise = ZTK_NotFound(object(), 'argh')
        app_iter = self._callFUT(environ, start_response, _publish)
        body = b''.join(app_iter)
        self.assertEqual(start_response._called_with[0][0], '404 Not Found')
        self.assertTrue(b'Exception View: NotFound' in body)
        unregisterExceptionView(INotFound)

    def testCustomExceptionViewBadRequest(self):
        from zExceptions import BadRequest
        registerExceptionView(IException)
        environ = self._makeEnviron()
        start_response = DummyCallable()
        _publish = DummyCallable()
        _publish._raise = BadRequest('argh')
        app_iter = self._callFUT(environ, start_response, _publish)
        body = b''.join(app_iter)
        self.assertEqual(start_response._called_with[0][0], '400 Bad Request')
        self.assertTrue(b'Exception View: BadRequest' in body)
        unregisterExceptionView(IException)

    def testCustomExceptionViewInternalError(self):
        from zExceptions import InternalError
        registerExceptionView(IException)
        environ = self._makeEnviron()
        start_response = DummyCallable()
        _publish = DummyCallable()
        _publish._raise = InternalError('argh')
        app_iter = self._callFUT(environ, start_response, _publish)
        body = b''.join(app_iter)
        self.assertEqual(
            start_response._called_with[0][0], '500 Internal Server Error')
        self.assertTrue(b'Exception View: InternalError' in body)
        unregisterExceptionView(IException)

    def testRedirectExceptionView(self):
        from zExceptions import Redirect
        registerExceptionView(IException)
        environ = self._makeEnviron()
        start_response = DummyCallable()
        _publish = DummyCallable()
        _publish._raise = Redirect('http://localhost:9/')
        app_iter = self._callFUT(environ, start_response, _publish)
        body = b''.join(app_iter)
        status, headers = start_response._called_with[0]
        self.assertEqual(status, '302 Found')
        self.assertTrue(b'Exception View: Redirect' in body)
        headers = dict(headers)
        self.assertEqual(headers['Location'], 'http://localhost:9/')
        unregisterExceptionView(IException)

    def testHandleErrorsFalseBypassesExceptionResponse(self):
        from AccessControl import Unauthorized
        environ = self._makeEnviron(**{
            'x-wsgiorg.throw_errors': True,
        })
        start_response = DummyCallable()
        _publish = DummyCallable()
        _publish._raise = Unauthorized('argg')
        with self.assertRaises(Unauthorized):
            self._callFUT(environ, start_response, _publish)

    def testDebugExceptionsBypassesExceptionResponse(self):
        from zExceptions import BadRequest

        # Register an exception view for BadRequest
        registerExceptionView(IException)
        environ = self._makeEnviron()
        start_response = DummyCallable()
        _publish = DummyCallable()
        _publish._raise = BadRequest('debugbypass')

        # Responses will always have debug_exceptions set
        def response_factory(stdout, stderr):
            response = DummyResponse()
            response.debug_exceptions = True
            return response

        try:
            # With debug_exceptions, the exception view is not called.
            with self.assertRaises(BadRequest):
                self._callFUT(environ, start_response, _publish,
                              _response_factory=response_factory)
        finally:
            # Clean up view registration
            unregisterExceptionView(IException)

    def test_set_REMOTE_USER_environ(self):
        environ = self._makeEnviron()
        start_response = DummyCallable()
        _response = DummyResponse()
        _publish = DummyCallable()
        _publish._result = _response
        self.assertFalse('REMOTE_USER' in environ)
        self._callFUT(environ, start_response, _publish)
        self.assertEqual(environ['REMOTE_USER'], user_name)
        # After logout there is no REMOTE_USER in environ
        environ = self._makeEnviron()
        self.logout()
        self._callFUT(environ, start_response, _publish)
        self.assertFalse('REMOTE_USER' in environ)

    def test_webdav_source_port(self):
        from ZPublisher import WSGIPublisher
        old_webdav_source_port = WSGIPublisher._WEBDAV_SOURCE_PORT
        start_response = DummyCallable()
        _response = DummyResponse()
        _publish = DummyCallable()
        _publish._result = _response

        # WebDAV source port not configured
        environ = self._makeEnviron(PATH_INFO='/test')
        self.assertNotIn('WEBDAV_SOURCE_PORT', environ)
        self.assertEqual(WSGIPublisher._WEBDAV_SOURCE_PORT, 0)
        self._callFUT(environ, start_response, _publish)
        self.assertNotIn('WEBDAV_SOURCE_PORT', environ)
        self.assertEqual(environ['PATH_INFO'], '/test')

        # Configuring the port
        WSGIPublisher.set_webdav_source_port(9800)
        self.assertEqual(WSGIPublisher._WEBDAV_SOURCE_PORT, 9800)

        # Coming through the wrong port
        environ = self._makeEnviron(SERVER_PORT=8080, PATH_INFO='/test')
        self._callFUT(environ, start_response, _publish)
        self.assertNotIn('WEBDAV_SOURCE_PORT', environ)
        self.assertEqual(environ['PATH_INFO'], '/test')

        # Using the wrong request method, environ gets marked
        # but the path doesn't get changed
        environ = self._makeEnviron(SERVER_PORT=9800,
                                    PATH_INFO='/test',
                                    REQUEST_METHOD='POST')
        self._callFUT(environ, start_response, _publish)
        self.assertIn('WEBDAV_SOURCE_PORT', environ)
        self.assertEqual(environ['PATH_INFO'], '/test')

        # All stars aligned
        environ = self._makeEnviron(SERVER_PORT=9800,
                                    PATH_INFO='/test',
                                    REQUEST_METHOD='GET')
        self._callFUT(environ, start_response, _publish)
        self.assertTrue(environ['WEBDAV_SOURCE_PORT'])
        self.assertEqual(environ['PATH_INFO'], '/test/manage_DAVget')

        # Clean up
        WSGIPublisher.set_webdav_source_port(old_webdav_source_port)


class ExcViewCreatedTests(ZopeTestCase):

    def _callFUT(self, exc):
        from zope.interface import directlyProvides
        from zope.publisher.browser import IDefaultBrowserLayer
        from ZPublisher.WSGIPublisher import _exc_view_created_response
        req = self.app.REQUEST
        req['PARENTS'] = [self.app]
        directlyProvides(req, IDefaultBrowserLayer)
        return _exc_view_created_response(exc, req, req.RESPONSE)

    def _registerStandardErrorView(self):
        from OFS.browser import StandardErrorMessageView
        from zope.interface import Interface
        registerExceptionView(Interface, factory=StandardErrorMessageView,
                              name='standard_error_message')

    def _unregisterStandardErrorView(self):
        from OFS.browser import StandardErrorMessageView
        from zope.interface import Interface
        unregisterExceptionView(Interface, factory=StandardErrorMessageView,
                                name='standard_error_message')

    def testNoStandardErrorMessage(self):
        from zExceptions import NotFound
        self._registerStandardErrorView()

        try:
            self.assertFalse(self._callFUT(NotFound))
        finally:
            self._unregisterStandardErrorView()

    def testWithStandardErrorMessage(self):
        from OFS.DTMLMethod import addDTMLMethod
        from zExceptions import NotFound
        self._registerStandardErrorView()
        response = self.app.REQUEST.RESPONSE

        addDTMLMethod(self.app, 'standard_error_message', file='OOPS')

        # The response content-type header is not set before rendering
        # the standard error template
        self.assertFalse(response.getHeader('Content-Type'))

        try:
            self.assertTrue(self._callFUT(NotFound))
        finally:
            self._unregisterStandardErrorView()

        # After rendering the response content-type header is set
        self.assertIn('text/html', response.getHeader('Content-Type'))

    def testWithEmptyErrorMessage(self):
        from OFS.DTMLMethod import addDTMLMethod
        from zExceptions import NotFound
        self._registerStandardErrorView()
        response = self.app.REQUEST.RESPONSE
        addDTMLMethod(self.app, 'standard_error_message', file='')
        self.app.standard_error_message.raw = ''

        # The response content-type header is not set before rendering
        # the standard error template
        self.assertFalse(response.getHeader('Content-Type'))

        try:
            self.assertTrue(self._callFUT(NotFound))
        finally:
            self._unregisterStandardErrorView()

        # After rendering the response still no content-type header is set
        self.assertFalse(response.getHeader('Content-Type'))


class WSGIPublisherTests(FunctionalTestCase):

    def test_can_handle_non_ascii_URLs(self):
        from OFS.Image import manage_addFile
        manage_addFile(self.app, 'täst', 'çöńtêñt'.encode())

        browser = Testing.testbrowser.Browser()
        browser.login('manager', 'manager_pass')

        browser.open(f'http://localhost/{quote("täst")}')
        self.assertEqual(browser.contents.decode('utf-8'), 'çöńtêñt')


class TestLoadApp(unittest.TestCase):

    def _getTarget(self):
        from ZPublisher.WSGIPublisher import load_app
        return load_app

    def _makeModuleInfo(self):
        class Connection:
            def close(self):
                pass

        class App:
            _p_jar = Connection()

        return (App, 'Zope', False)

    def test_open_transaction_is_aborted(self):
        load_app = self._getTarget()

        transaction.begin()
        self.assertIsNotNone(transaction.manager.manager._txn)
        with load_app(self._makeModuleInfo()):
            pass
        self.assertIsNone(transaction.manager.manager._txn)

    def test_no_second_transaction_is_created_if_closed(self):
        load_app = self._getTarget()

        class TransactionCounter:

            after = 0
            before = 0

            def newTransaction(self, transaction):
                pass

            def beforeCompletion(self, transaction):
                self.before += 1

            def afterCompletion(self, transaction):
                self.after += 1

            def counts(self):
                return (self.after, self.before)

        counter = TransactionCounter()
        self.addCleanup(lambda: transaction.manager.unregisterSynch(counter))

        transaction.manager.registerSynch(counter)

        transaction.begin()
        self.assertIsNotNone(transaction.manager.manager._txn)
        with load_app(self._makeModuleInfo()):
            transaction.abort()

        self.assertIsNone(transaction.manager.manager._txn)
        self.assertEqual(counter.counts(), (1, 1))


class CustomExceptionView:

    def __init__(self, context, request):
        self.context = context
        self.__parent__ = None
        self.request = request

    def __call__(self):
        return (
            f'Exception View: {self.context.__class__.__name__}\n'
            f'Context: {self.__parent__.__class__.__name__}')


def registerExceptionView(for_, factory=CustomExceptionView,
                          name='index.html'):
    from zope.component import getGlobalSiteManager
    from zope.interface import Interface
    from zope.publisher.interfaces.browser import IDefaultBrowserLayer
    gsm = getGlobalSiteManager()
    gsm.registerAdapter(
        factory,
        required=(for_, IDefaultBrowserLayer),
        provided=Interface,
        name=name,
    )


def unregisterExceptionView(for_, factory=CustomExceptionView,
                            name='index.html'):
    from zope.component import getGlobalSiteManager
    from zope.interface import Interface
    from zope.publisher.interfaces.browser import IDefaultBrowserLayer
    gsm = getGlobalSiteManager()
    gsm.unregisterAdapter(
        factory,
        required=(for_, IDefaultBrowserLayer),
        provided=Interface,
        name=name,
    )


class DummyRequest(dict):
    _processedInputs = False
    _traversed = None
    _traverse_to = None
    args = ()

    def processInputs(self):
        self._processedInputs = True

    def traverse(self, path, response=None, validated_hook=None):
        self._traversed = (path, response, validated_hook)
        return self._traverse_to

    def delay_retry(self):
        return None


class DummyResponse:
    debug_mode = False
    after_list = ()
    realm = None
    _body = None
    _finalized = False
    _status = '204 No Content'
    _headers = [('Content-Length', '0')]

    def __init__(self):
        self.stdout = io.BytesIO()

    def finalize(self):
        self._finalized = True
        return self._status, self._headers

    def setBody(self, body):
        self._body = body

    body = property(lambda self: self._body, setBody)

    def setStatus(self, status, reason=None, lock=None):
        self._status = status

    status = property(lambda self: self._status, setStatus)

    def getHeader(self, header):
        return dict(self._headers).get(header, None)

    def setHeader(self, header, value):
        headers = dict(self._headers)
        headers[header] = value
        self._headers = tuple(headers.items())


class DummyCallable:
    _called_with = _raise = _result = None

    def __call__(self, *args, **kw):
        self._called_with = (args, kw)
        if self._raise:
            raise self._raise
        return self._result


def noopStartResponse(status, headers):
    pass
