'''Publication events.

They are notified in 'ZPublisher.Publish.publish' and
inform about publications and their fate.

Subscriptions can be used for all kinds of request supervision,
e.g. request and error rate determination, writing high resolution logfiles
for detailed time related analysis, inline request monitoring.
'''
from zope.interface import implementer
from ZPublisher.interfaces import IPubAfterTraversal
from ZPublisher.interfaces import IPubBeforeAbort
from ZPublisher.interfaces import IPubBeforeCommit
from ZPublisher.interfaces import IPubBeforeStreaming
from ZPublisher.interfaces import IPubFailure
from ZPublisher.interfaces import IPubStart
from ZPublisher.interfaces import IPubSuccess


class _Base:
    """PubEvent base class."""

    def __init__(self, request):
        self.request = request


@implementer(IPubStart)
class PubStart(_Base):
    '''notified at the beginning of 'ZPublisher.Publish.publish'.'''


@implementer(IPubSuccess)
class PubSuccess(_Base):
    '''notified at successful request end.'''


@implementer(IPubFailure)
class PubFailure:
    '''notified at failed request end.'''

    def __init__(self, request, exc_info, retry):
        self.request, self.exc_info, self.retry = request, exc_info, retry


@implementer(IPubAfterTraversal)
class PubAfterTraversal(_Base):
    """notified after traversal and an (optional) authentication."""


@implementer(IPubBeforeCommit)
class PubBeforeCommit(_Base):
    """notified immediately before the commit."""


@implementer(IPubBeforeAbort)
class PubBeforeAbort(_Base):
    """notified immediately before an abort."""

    def __init__(self, request, exc_info, retry):
        self.request, self.exc_info, self.retry = request, exc_info, retry


@implementer(IPubBeforeStreaming)
class PubBeforeStreaming:
    """Notified immediately before streaming via response.write() commences
    """

    def __init__(self, response):
        self.response = response
