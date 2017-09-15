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
import unittest

import transaction
from zope.interface.common.interfaces import IException
from zope.publisher.interfaces import INotFound
from zope.security.interfaces import IUnauthorized
from zope.security.interfaces import IForbidden

from ZPublisher.WSGIPublisher import get_module_info
from Testing.ZopeTestCase import ZopeTestCase


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
        self.assertTrue(('Date', whenstr) in headers)

    def test_setBody_IUnboundStreamIterator(self):
        from ZPublisher.Iterators import IUnboundStreamIterator
        from zope.interface import implementer

        @implementer(IUnboundStreamIterator)
        class TestStreamIterator(object):
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
        from ZPublisher.Iterators import IStreamIterator
        from zope.interface import implementer

        @implementer(IStreamIterator)
        class TestStreamIterator(object):
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
                    return publish_module(environ, start_response, _publish,
                                          _response_factory, _request_factory)
                return publish_module(environ, start_response, _publish,
                                      _response_factory)
            else:
                if _request_factory is not None:
                    return publish_module(environ, start_response, _publish,
                                          _request_factory=_request_factory)
                return publish_module(environ, start_response, _publish)
        return publish_module(environ, start_response)

    def _registerView(self, factory, name, provides=None):
        from zope.component import provideAdapter
        from zope.interface import Interface
        from zope.publisher.browser import IDefaultBrowserLayer
        from OFS.interfaces import IApplication
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
        from ZPublisher.Iterators import IStreamIterator
        from zope.interface import implementer

        @implementer(IStreamIterator)
        class TestStreamIterator(object):
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
        from ZPublisher.Iterators import IUnboundStreamIterator
        from zope.interface import implementer

        @implementer(IUnboundStreamIterator)
        class TestUnboundStreamIterator(object):
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


class TestLoadApp(unittest.TestCase):

    def _getTarget(self):
        from ZPublisher.WSGIPublisher import load_app
        return load_app

    def _makeModuleInfo(self):
        class Connection(object):
            def close(self):
                pass

        class App(object):
            _p_jar = Connection()

        return (App, 'Zope', False)

    def test_open_transaction_is_aborted(self):
        load_app = self._getTarget()

        transaction.begin()
        self.assertIsNotNone(transaction.manager._txn)
        with load_app(self._makeModuleInfo()):
            pass
        self.assertIsNone(transaction.manager._txn)

    def test_no_second_transaction_is_created_if_closed(self):
        load_app = self._getTarget()

        class TransactionCounter(object):

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
        self.assertIsNotNone(transaction.manager._txn)
        with load_app(self._makeModuleInfo()):
            transaction.abort()

        self.assertIsNone(transaction.manager._txn)
        self.assertEqual(counter.counts(), (1, 1))


class CustomExceptionView(object):

    def __init__(self, context, request):
        self.context = context
        self.__parent__ = None
        self.request = request

    def __call__(self):
        return ('Exception View: %s\nContext: %s' % (
                self.context.__class__.__name__,
                self.__parent__.__class__.__name__))


def registerExceptionView(for_):
    from zope.interface import Interface
    from zope.component import getGlobalSiteManager
    from zope.publisher.interfaces.browser import IDefaultBrowserLayer
    gsm = getGlobalSiteManager()
    gsm.registerAdapter(
        CustomExceptionView,
        required=(for_, IDefaultBrowserLayer),
        provided=Interface,
        name=u'index.html',
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


class DummyResponse(object):
    debug_mode = False
    after_list = ()
    realm = None
    _body = None
    _finalized = False
    _status = '204 No Content'
    _headers = [('Content-Length', '0')]

    def finalize(self):
        self._finalized = True
        return self._status, self._headers

    def setBody(self, body):
        self._body = body

    body = property(lambda self: self._body, setBody)


class DummyCallable(object):
    _called_with = _raise = _result = None

    def __call__(self, *args, **kw):
        self._called_with = (args, kw)
        if self._raise:
            raise self._raise
        return self._result


def noopStartResponse(status, headers):
    pass
