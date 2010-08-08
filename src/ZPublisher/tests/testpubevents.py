from StringIO import StringIO
from sys import modules, exc_info
from unittest import TestCase, TestSuite, makeSuite, main

from ZODB.POSException import ConflictError
from zope.interface.verify import verifyObject
from zope.event import subscribers

from ZPublisher.Publish import publish, Retry
from ZPublisher.BaseRequest import BaseRequest
from ZPublisher.HTTPResponse import HTTPResponse
from ZPublisher.pubevents import PubStart, PubSuccess, PubFailure, \
     PubAfterTraversal, PubBeforeCommit, PubBeforeAbort, \
     PubBeforeStreaming
from ZPublisher.interfaces import \
     IPubStart, IPubEnd, IPubSuccess, IPubFailure, \
     IPubAfterTraversal, IPubBeforeCommit, \
     IPubBeforeStreaming

PUBMODULE = 'TEST_testpubevents'

_g=globals()

class TestInterface(TestCase):
    def testPubStart(self):
        verifyObject(IPubStart, PubStart(_Request()))

    def testPubSuccess(self):
        e = PubSuccess(_Request())
        verifyObject(IPubSuccess, e)
        verifyObject(IPubEnd, e)

    def testPubFailure(self):
        # get some exc info
        try: raise ValueError()
        except: exc = exc_info()
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
        if PUBMODULE in modules: del modules[PUBMODULE]
        subscribers[:] = self._saved_subscribers

    def testSuccess(self):
        r = self.request; r.action = 'succeed'
        publish(r, PUBMODULE, [None])
        events = self.reporter.events
        self.assertEqual(len(events), 4)
        self.assert_(isinstance(events[0], PubStart))
        self.assertEqual(events[0].request, r)
        self.assert_(isinstance(events[-1], PubSuccess))
        self.assertEqual(events[-1].request, r)
        # test AfterTraversal and BeforeCommit as well
        self.assert_(isinstance(events[1], PubAfterTraversal))
        self.assertEqual(events[1].request, r)
        self.assert_(isinstance(events[2], PubBeforeCommit))
        self.assertEqual(events[2].request, r)

    def testFailureReturn(self):
        r = self.request; r.action = 'fail_return'
        publish(r, PUBMODULE, [None])
        events = self.reporter.events
        self.assertEqual(len(events), 3)
        self.assert_(isinstance(events[0], PubStart))
        self.assertEqual(events[0].request, r)
        self.assert_(isinstance(events[1], PubBeforeAbort))
        self.assertEqual(events[1].request, r)
        self.assertEqual(events[1].retry, False)
        self.assert_(isinstance(events[2], PubFailure))
        self.assertEqual(events[2].request, r)
        self.assertEqual(events[2].retry, False)
        self.assertEqual(len(events[2].exc_info), 3)

    def testFailureException(self):
        r = self.request; r.action = 'fail_exception'
        self.assertRaises(Exception, publish, r, PUBMODULE, [None])
        events = self.reporter.events
        self.assertEqual(len(events), 3)
        self.assert_(isinstance(events[0], PubStart))
        self.assertEqual(events[0].request, r)
        self.assert_(isinstance(events[1], PubBeforeAbort))
        self.assertEqual(events[1].request, r)
        self.assertEqual(events[1].retry, False)
        self.assertEqual(len(events[1].exc_info), 3)
        self.assert_(isinstance(events[2], PubFailure))
        self.assertEqual(events[2].request, r)
        self.assertEqual(events[2].retry, False)
        self.assertEqual(len(events[2].exc_info), 3)

    def testFailureConflict(self):
        r = self.request; r.action = 'conflict'
        publish(r, PUBMODULE, [None])
        events = self.reporter.events
        self.assertEqual(len(events), 7)
        
        self.assert_(isinstance(events[0], PubStart))
        self.assertEqual(events[0].request, r)
        
        self.assert_(isinstance(events[1], PubBeforeAbort))
        self.assertEqual(events[1].request, r)
        self.assertEqual(events[1].retry, True)
        self.assertEqual(len(events[1].exc_info), 3)
        self.assert_(isinstance(events[1].exc_info[1], ConflictError))
        
        self.assert_(isinstance(events[2], PubFailure))
        self.assertEqual(events[2].request, r)
        self.assertEqual(events[2].retry, True)
        self.assertEqual(len(events[2].exc_info), 3)
        self.assert_(isinstance(events[2].exc_info[1], ConflictError))
        
        self.assert_(isinstance(events[3], PubStart))
        self.assert_(isinstance(events[4], PubAfterTraversal))
        self.assert_(isinstance(events[5], PubBeforeCommit))
        self.assert_(isinstance(events[6], PubSuccess))

    def testStreaming(self):
        
        out = StringIO()
        response = HTTPResponse(stdout=out)
        response.write('datachunk1')
        response.write('datachunk2')
        
        events = self.reporter.events
        self.assertEqual(len(events), 1)
        self.assert_(isinstance(events[0], PubBeforeStreaming))
        self.assertEqual(events[0].response, response)
        
        self.assertTrue('datachunk1datachunk2' in out.getvalue())


# Auxiliaries
def _succeed():
    ''' '''
    return 'success'

class _Application(object): pass

class _Reporter(object):
    def __init__(self): self.events = []
    def __call__(self, event): self.events.append(event)

class _Response(object):
    def setBody(*unused): pass


class _Request(BaseRequest):
    response = _Response()
    _hacked_path = False
    args = ()

    def __init__(self, *args, **kw):
        BaseRequest.__init__(self, *args, **kw)
        self['PATH_INFO'] = self['URL'] = ''
        self.steps = []

    def supports_retry(self): return True
    def retry(self):
        r = self.__class__()
        r.action = 'succeed'
        return r

    def traverse(self, *unused, **unused_kw):
        action = self.action
        if action.startswith('fail'): raise Exception(action)
        if action == 'conflict': raise ConflictError()
        if action == 'succeed': return _succeed
        else: raise ValueError('unknown action: %s' % action)

    # override to get rid of the 'EndRequestEvent' notification
    def close(self): pass
    
# define things necessary for publication
bobo_application = _Application()
def zpublisher_exception_hook(parent, request, *unused):
    action = request.action
    if action == 'fail_return': return 0
    if action == 'fail_exception': raise Exception()
    if action == 'conflict': raise Retry()
    raise ValueError('unknown action: %s' % action)

def test_suite():
    return TestSuite((makeSuite(c) for c in (TestPubEvents, TestInterface)))

        

