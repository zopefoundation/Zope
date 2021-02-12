from io import BytesIO
from sys import exc_info
from sys import modules
from unittest import TestCase

import zExceptions
from Testing.ZopeTestCase import FunctionalTestCase
from Testing.ZopeTestCase import user_name
from Testing.ZopeTestCase import user_password
from ZODB.POSException import ConflictError
from zope.component import adapter
from zope.component import getSiteManager
from zope.event import subscribers
from zope.globalrequest import getRequest
from zope.interface import Interface
from zope.interface.verify import verifyObject
from zope.publisher.interfaces import INotFound
from zope.publisher.interfaces.browser import IDefaultBrowserLayer
from ZPublisher.BaseRequest import BaseRequest
from ZPublisher.HTTPRequest import WSGIRequest
from ZPublisher.HTTPResponse import WSGIResponse
from ZPublisher.interfaces import IPubAfterTraversal
from ZPublisher.interfaces import IPubBeforeCommit
from ZPublisher.interfaces import IPubBeforeStreaming
from ZPublisher.interfaces import IPubEnd
from ZPublisher.interfaces import IPubEvent
from ZPublisher.interfaces import IPubFailure
from ZPublisher.interfaces import IPubStart
from ZPublisher.interfaces import IPubSuccess
from ZPublisher.pubevents import PubAfterTraversal
from ZPublisher.pubevents import PubBeforeAbort
from ZPublisher.pubevents import PubBeforeCommit
from ZPublisher.pubevents import PubBeforeStreaming
from ZPublisher.pubevents import PubFailure
from ZPublisher.pubevents import PubStart
from ZPublisher.pubevents import PubSuccess
from ZPublisher.WSGIPublisher import publish_module


PUBMODULE = 'TEST_testpubevents'

_g = globals()


class TestInterface(TestCase):

    def testPubStart(self):
        verifyObject(IPubStart, PubStart(_Request()))

    def testPubSuccess(self):
        e = PubSuccess(_Request())
        verifyObject(IPubSuccess, e)
        verifyObject(IPubEnd, e)

    def testPubFailure(self):
        # get some exc info
        try:
            raise ValueError()
        except Exception:
            exc = exc_info()
        e = PubFailure(_Request(), exc, False)
        verifyObject(IPubFailure, e)
        verifyObject(IPubEnd, e)

    def testAfterTraversal(self):
        e = PubAfterTraversal(_Request())
        verifyObject(IPubAfterTraversal, e)

    def testBeforeCommit(self):
        e = PubBeforeCommit(_Request())
        verifyObject(IPubBeforeCommit, e)

    def testBeforeStreaming(self):
        e = PubBeforeStreaming(_Response())
        verifyObject(IPubBeforeStreaming, e)


class TestPubEvents(TestCase):

    def setUp(self):
        self._saved_subscribers = subscribers[:]
        self.reporter = r = _Reporter()
        subscribers[:] = [r]
        modules[PUBMODULE] = __import__(__name__, _g, _g, ('__doc__', ))
        self.request = _Request()

    def tearDown(self):
        if PUBMODULE in modules:
            del modules[PUBMODULE]
        subscribers[:] = self._saved_subscribers

    def _publish(self, request, module_name):
        def start_response(status, headers):
            pass

        publish_module({
            'SERVER_PROTOCOL': 'HTTP/1.1',
            'SERVER_NAME': 'localhost',
            'SERVER_PORT': 'localhost',
            'REQUEST_METHOD': 'GET',
        }, start_response, _request=request, _module_name=module_name)

    def testSuccess(self):
        r = self.request
        r.action = 'succeed'
        self._publish(r, PUBMODULE)
        events = self.reporter.events
        self.assertIsInstance(events[0], PubStart)
        self.assertEqual(events[0].request, r)
        self.assertIsInstance(events[1], PubAfterTraversal)
        self.assertEqual(events[1].request, r)
        self.assertIsInstance(events[2], PubBeforeCommit)
        self.assertEqual(events[2].request, r)
        self.assertIsInstance(events[3], PubSuccess)
        self.assertEqual(events[3].request, r)

    def testFailureReturn(self):
        r = self.request
        r.action = 'fail_return'
        self.assertRaises(Exception, self._publish, r, PUBMODULE)
        events = self.reporter.events
        self.assertIsInstance(events[0], PubStart)
        self.assertEqual(events[0].request, r)
        self.assertIsInstance(events[1], PubBeforeAbort)
        self.assertEqual(events[1].request, r)
        self.assertIsInstance(events[2], PubFailure)
        self.assertEqual(events[2].request, r)
        self.assertEqual(len(events[2].exc_info), 3)

    def testFailureException(self):
        r = self.request
        r.action = 'fail_exception'
        self.assertRaises(Exception, self._publish, r, PUBMODULE)
        events = self.reporter.events
        self.assertIsInstance(events[0], PubStart)
        self.assertEqual(events[0].request, r)
        self.assertIsInstance(events[1], PubBeforeAbort)
        self.assertEqual(events[1].request, r)
        self.assertEqual(len(events[1].exc_info), 3)
        self.assertIsInstance(events[2], PubFailure)
        self.assertEqual(events[2].request, r)
        self.assertEqual(len(events[2].exc_info), 3)

    def testFailureConflict(self):
        r = self.request
        r.action = 'conflict'
        self.assertRaises(ConflictError, self._publish, r, PUBMODULE)
        events = self.reporter.events
        self.assertIsInstance(events[0], PubStart)
        self.assertEqual(events[0].request, r)
        self.assertIsInstance(events[1], PubBeforeAbort)
        self.assertEqual(events[1].request, r)
        self.assertEqual(len(events[1].exc_info), 3)
        self.assertIsInstance(events[1].exc_info[1], ConflictError)
        self.assertIsInstance(events[2], PubFailure)
        self.assertEqual(events[2].request, r)
        self.assertEqual(len(events[2].exc_info), 3)
        self.assertIsInstance(events[2].exc_info[1], ConflictError)

    def testStreaming(self):
        out = BytesIO()
        response = WSGIResponse(stdout=out)
        response.write(b'datachunk1')
        response.write(b'datachunk2')

        events = self.reporter.events
        self.assertEqual(len(events), 1)
        self.assertIsInstance(events[0], PubBeforeStreaming)
        self.assertEqual(events[0].response, response)

        self.assertTrue(b'datachunk1datachunk2' in out.getvalue())


class ExceptionView:

    def __init__(self, context, request):
        self.context = context  # exception instance
        self.__parent__ = None
        self.request = request

    def __call__(self):
        global_request = getRequest()
        self.request.response.events.append('exc_view')
        return (
            f'Exception: {self.context.__class__}\n'
            f'Request: {global_request!r}')


class TestGlobalRequestPubEventsAndExceptionUpgrading(FunctionalTestCase):

    def afterSetUp(self):
        # Remember the handler, so we can unregister it and not
        # get a new bound method instance in beforeTearDown.
        self.event_handler = self.pub_event
        sm = getSiteManager()
        sm.registerHandler(self.event_handler)
        self.exc_view_for = None
        self.expected_exception_type = None

    def beforeTearDown(self):
        sm = getSiteManager()
        sm.unregisterHandler(self.event_handler)
        if self.exc_view_for:
            # If an exception view was registered, remove it.
            sm.unregisterAdapter(
                ExceptionView,
                required=(self.exc_view_for, IDefaultBrowserLayer),
                provided=Interface,
                name='index.html',
            )

    def _registerExceptionView(self, for_):
        self.exc_view_for = for_
        sm = getSiteManager()
        sm.registerAdapter(
            ExceptionView,
            required=(for_, IDefaultBrowserLayer),
            provided=Interface,
            name='index.html',
        )

    @adapter(IPubEvent)
    def pub_event(self, event):
        global_request = getRequest()
        # The request is the exact same instance on the event and
        # in the thread local.
        self.assertIsInstance(global_request, WSGIRequest)
        self.assertIs(global_request, event.request)
        # Keep track of all the different pub events.
        response = event.request.response
        if not hasattr(response, 'events'):
            setattr(response, 'events', [])
        response.events.append(event.__class__.__name__)

        if hasattr(event, 'exc_info'):
            exception_type, exception_instance, traceback = event.exc_info
            self.assertIsInstance(exception_instance, exception_type)
            self.assertIsInstance(exception_instance,
                                  self.expected_exception_type)

    def test_all_pub_events_have_access_to_valid_global_request(self):
        self.folder.addDTMLDocument('index_html', file='index')
        response = self.publish(
            self.folder.absolute_url_path(),
            basic=f'{user_name}:{user_password}')
        self.assertEqual(response.getStatus(), 200)
        self.assertEqual(response._response.events,
                         ['PubStart', 'PubAfterTraversal',
                          'PubBeforeCommit', 'PubSuccess'])

    def test_unauthorized_exception_is_handled_as_other_exceptions(self):
        self.expected_exception_type = zExceptions.Unauthorized
        response = self.publish('/manage_main')
        self.assertEqual(response.getStatus(), 401)
        self.assertEqual(response._response.events,
                         ['PubStart', 'PubBeforeAbort', 'PubFailure'])

    def test_BeforeAbort_and_Failure_events_can_access_zope_globalReq(self):
        self.expected_exception_type = zExceptions.NotFound
        response = self.publish('/notexisting')
        self.assertEqual(response.getStatus(), 404)
        self.assertEqual(response._response.events,
                         ['PubStart', 'PubBeforeAbort', 'PubFailure'])

    def test_BeforeAbort_and_Failure_events_are_called_after_exc_view(self):
        self.expected_exception_type = zExceptions.NotFound
        # zope.globalrequest works inside an exception view.
        self._registerExceptionView(INotFound)
        response = self.publish('/notexisting')
        self.assertEqual(response._response.events,
                         ['PubStart', 'exc_view',
                          'PubBeforeAbort', 'PubFailure'])
        self.assertEqual(response.getStatus(), 404)
        self.assertEqual(
            response.getBody(),
            (b"Exception: <class 'zExceptions.NotFound'>\n"
             b"Request: <WSGIRequest, URL=http://nohost/notexisting>"))

    def test_exception_views_and_event_handlers_get_upgraded_exceptions(self):
        self.expected_exception_type = zExceptions.HTTPVersionNotSupported

        def raiser(*args, **kwargs):
            "Allow publishing"
            class HTTPVersionNotSupported(Exception):
                pass
            raise HTTPVersionNotSupported()
        self.folder.__class__.index_html = raiser

        def cleanup():
            del self.folder.__class__.index_html

        self.addCleanup(cleanup)

        from zope.publisher.interfaces.http import IHTTPException
        self._registerExceptionView(IHTTPException)
        response = self.publish(self.folder.absolute_url_path())
        self.assertEqual(response._response.events,
                         ['PubStart', 'PubAfterTraversal', 'exc_view',
                          'PubBeforeAbort', 'PubFailure'])
        self.assertEqual(response.getStatus(), 505)
        self.assertEqual(
            response.getBody(),
            (b"Exception: <class 'zExceptions.HTTPVersionNotSupported'>\n"
             b"Request: <WSGIRequest, "
             b"URL=http://nohost/test_folder_1_/index_html>"))


def _succeed():
    ''' '''
    return 'success'


# Poor man's mock.
class _Application:
    def __getattr__(self, name):
        return self

    def __call__(self, *args, **kwargs):
        return self


class _Reporter:
    def __init__(self):
        self.events = []

    def __call__(self, event):
        self.events.append(event)


class _Response:
    def setBody(*unused):
        pass


class _Request(BaseRequest):
    response = WSGIResponse()
    _hacked_path = False
    args = ()
    environ = {}

    def __init__(self, *args, **kw):
        BaseRequest.__init__(self, *args, **kw)
        self['PATH_INFO'] = self['URL'] = ''
        self.steps = []

    def traverse(self, *unused, **unused_kw):
        action = self.action
        if action.startswith('fail'):
            raise Exception(action)
        if action == 'conflict':
            raise ConflictError()
        if action == 'succeed':
            return _succeed
        else:
            raise ValueError('unknown action: %s' % action)

    def close(self):
        # override to get rid of the 'EndRequestEvent' notification
        pass


# define things necessary for publication
bobo_application = _Application()
