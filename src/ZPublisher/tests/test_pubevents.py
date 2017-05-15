from io import BytesIO
from sys import modules, exc_info
from unittest import TestCase

from ZODB.POSException import ConflictError
from zope.interface.verify import verifyObject
from zope.event import subscribers

from ZPublisher.BaseRequest import BaseRequest
from ZPublisher.HTTPResponse import WSGIResponse
from ZPublisher.interfaces import (
    IPubStart, IPubEnd, IPubSuccess, IPubFailure,
    IPubAfterTraversal, IPubBeforeCommit,
    IPubBeforeStreaming,
)
from ZPublisher.pubevents import (
    PubStart, PubSuccess, PubFailure,
    PubAfterTraversal, PubBeforeCommit, PubBeforeAbort,
    PubBeforeStreaming,
)
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


def _succeed():
    ''' '''
    return 'success'


class _Application(object):
    pass


class _Reporter(object):
    def __init__(self):
        self.events = []

    def __call__(self, event):
        self.events.append(event)


class _Response(object):
    def setBody(*unused):
        pass


class _Request(BaseRequest):
    response = WSGIResponse()
    _hacked_path = False
    args = ()

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
