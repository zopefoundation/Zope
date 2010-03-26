'''Publication events.

They are notified in 'ZPublisher.Publish.publish' and 
inform about publications and their fate.

Subscriptions can be used for all kinds of request supervision,
e.g. request and error rate determination, writing high resolution logfiles
for detailed time related analysis, inline request monitoring.
'''
from zope.interface import implements

from interfaces import IPubStart, IPubSuccess, IPubFailure, \
     IPubAfterTraversal, IPubBeforeCommit, IPubBeforeAbort, \
     IPubBeforeStreaming

class _Base(object):
    """PubEvent base class."""

    def __init__(self, request):
        self.request = request

class PubStart(_Base):
    '''notified at the beginning of 'ZPublisher.Publish.publish'.'''
    implements(IPubStart)

class PubSuccess(_Base):
    '''notified at successful request end.'''
    implements(IPubSuccess)

class PubFailure(object):
    '''notified at failed request end.'''
    implements(IPubFailure)

    def __init__(self, request, exc_info, retry):
        self.request, self.exc_info, self.retry = request, exc_info, retry


class PubAfterTraversal(_Base):
    """notified after traversal and an (optional) authentication."""
    implements(IPubAfterTraversal)


class PubBeforeCommit(_Base):
    """notified immediately before the commit."""
    implements(IPubBeforeCommit)

class PubBeforeAbort(_Base):
    """notified immediately before an abort."""
    implements(IPubBeforeAbort)
    
    def __init__(self, request, exc_info, retry):
        self.request, self.exc_info, self.retry = request, exc_info, retry

class PubBeforeStreaming(object):
    """Notified immediately before streaming via response.write() commences
    """
    implements(IPubBeforeStreaming)
    
    def __init__(self, response):
        self.response = response
