from ZPublisher import Retry
from ZODB.POSException import ConflictError

class Tracer:
    """Trace used to record pathway taken through the publisher
    machinery. And provide framework for spewing out exceptions at
    just the right time.
    """

    def __init__(self):
        self.reset()

    def reset(self):
        self.tracedPath = []
        self.exceptions = {}

    def append(self, arg):
        self.tracedPath.append(arg)

    def showTracedPath(self):
        for arg in self.tracedPath:
            print arg

    def possiblyRaiseException(self, context):
        exceptions = tracer.exceptions.get(context, None)
        if exceptions:
            exception = exceptions[0]
            exceptions.remove(exception)
            exceptionShortName = str(exception).split('.')[-1]
            self.append('raising %s from %s' % (exceptionShortName, context))
            raise exception


tracer = Tracer()

class TransactionsManager:
    """Mock TransactionManager to replace
    Zope2.App.startup.TransactionsManager.
    """

    def abort(self):
        tracer.append('abort')

    def begin(self):
        tracer.append('begin')

    def commit(self):
        tracer.append('commit')
        tracer.possiblyRaiseException('commit')

    def recordMetaData(self, obj, request):
        pass

zpublisher_transactions_manager = TransactionsManager()

def zpublisher_exception_hook(published, request, t, v, traceback):
    """Mock zpublisher_exception_hook to replace
    Zope2.App.startup.zpublisher_exception_hook
    """

    if issubclass(t, ConflictError):
        raise Retry(t, v, traceback)
    if t is Retry:
        v.reraise()
    tracer.append('zpublisher_exception_hook')
    tracer.possiblyRaiseException('zpublisher_exception_hook')
    return 'zpublisher_exception_hook'

class Object:
    """Mock object for traversing to.
    """

    def __call__(self):
        tracer.append('__call__')
        tracer.possiblyRaiseException('__call__')
        return '__call__'

class Response:
    """Mock Response to replace ZPublisher.HTTPResponse.HTTPResponse.
    """

    def setBody(self, a):
        pass

class Request:
    """Mock Request to replace ZPublisher.HTTPRequest.HTTPRequest.
    """

    args = ()

    def __init__(self):
        self.response = Response()

    def processInputs(self):
        pass

    def get(self, a, b=''):
        return ''

    def __setitem__(self, name, value):
        pass

    def traverse(self, path, validated_hook):
        return Object()

    def close(self):
        pass

    retry_count = 0
    retry_max_count = 3

    def supports_retry(self):
        return self.retry_count < self.retry_max_count

    def retry(self):
        self.retry_count += 1
        r = self.__class__()
        r.retry_count = self.retry_count
        return r

module_name = __name__
after_list = [None]


def testPublisher():
    """
    Tests to ensure that the ZPublisher correctly manages the ZODB
    transaction boundaries.

    >>> from ZPublisher.Publish import publish

    ZPublisher will commit the transaction after it has made a
    rendering of the object.

    >>> tracer.reset()
    >>> request = Request()
    >>> response = publish(request, module_name, after_list)
    >>> tracer.showTracedPath()
    begin
    __call__
    commit

    If ZPublisher sees an exception when rendering the requested
    object then it will try rendering an error message. The
    transaction is eventually aborted after rendering the error
    message. (Note that this handling of the transaction boundaries is
    different to how Zope3 does things. Zope3 aborts the transaction
    before rendering the error message.)

    >>> tracer.reset()
    >>> tracer.exceptions['__call__'] = [ValueError]
    >>> request = Request()
    >>> response = publish(request, module_name, after_list)
    >>> tracer.showTracedPath()
    begin
    __call__
    raising ValueError from __call__
    zpublisher_exception_hook
    abort

    If there is a futher exception raised while trying to render the
    error then ZPublisher is still required to abort the
    transaction. And the exception propagates out of publish.

    >>> tracer.reset()
    >>> tracer.exceptions['__call__'] = [ValueError]
    >>> tracer.exceptions['zpublisher_exception_hook'] = [ValueError]
    >>> request = Request()
    >>> response = publish(request, module_name, after_list)
    Traceback (most recent call last):
    ...
    ValueError
    >>> tracer.showTracedPath()
    begin
    __call__
    raising ValueError from __call__
    zpublisher_exception_hook
    raising ValueError from zpublisher_exception_hook
    abort

    ZPublisher can also deal with database ConflictErrors. The original
    transaction is aborted and a second is made in which the request
    is attempted again. (There is a fair amount of collaboration to
    implement the retry functionality. Relies on Request and
    zpublisher_exception_hook also doing the right thing.)

    >>> tracer.reset()
    >>> tracer.exceptions['__call__'] = [ConflictError]
    >>> request = Request()
    >>> response = publish(request, module_name, after_list)
    >>> tracer.showTracedPath()
    begin
    __call__
    raising ConflictError from __call__
    abort
    begin
    __call__
    commit

    Same behaviour if there is a conflict when attempting to commit
    the transaction. (Again this relies on collaboration from
    zpublisher_exception_hook.)

    >>> tracer.reset()
    >>> tracer.exceptions['commit'] = [ConflictError]
    >>> request = Request()
    >>> response = publish(request, module_name, after_list)
    >>> tracer.showTracedPath()
    begin
    __call__
    commit
    raising ConflictError from commit
    abort
    begin
    __call__
    commit

    ZPublisher will retry the request several times. After 3 retries it
    gives up and the exception propogates out.

    >>> tracer.reset()
    >>> tracer.exceptions['__call__'] = [ConflictError, ConflictError,
    ...                                  ConflictError, ConflictError]
    >>> request = Request()
    >>> response = publish(request, module_name, after_list)
    Traceback (most recent call last):
    ...
    ConflictError: database conflict error
    >>> tracer.showTracedPath()
    begin
    __call__
    raising ConflictError from __call__
    abort
    begin
    __call__
    raising ConflictError from __call__
    abort
    begin
    __call__
    raising ConflictError from __call__
    abort
    begin
    __call__
    raising ConflictError from __call__
    abort

    However ZPublisher does not retry ConflictErrors that are raised
    while trying to render an error message.

    >>> tracer.reset()
    >>> tracer.exceptions['__call__'] = [ValueError]
    >>> tracer.exceptions['zpublisher_exception_hook'] = [ConflictError]
    >>> request = Request()
    >>> response = publish(request, module_name, after_list)
    Traceback (most recent call last):
    ...
    ConflictError: database conflict error
    >>> tracer.showTracedPath()
    begin
    __call__
    raising ValueError from __call__
    zpublisher_exception_hook
    raising ConflictError from zpublisher_exception_hook
    abort

    """
    pass


from zope.testing import doctest

def test_suite():
    return doctest.DocTestSuite()
