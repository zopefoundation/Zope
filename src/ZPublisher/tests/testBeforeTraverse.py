import doctest

from Acquisition import Implicit
from ZPublisher.BaseRequest import BaseRequest
from ZPublisher.HTTPResponse import HTTPResponse


def makeBaseRequest(root):
    response = HTTPResponse()
    environment = {
        'URL': '',
        'PARENTS': [root],
        'steps': [],
        '_hacked_path': 0,
        '_test_counter': 0,
        'response': response,
    }
    return BaseRequest(environment)


class DummyObjectBasic(Implicit):
    """ Dummy class with docstring.
    """
    pass


class BrokenHook:

    def __call__(self, *args):
        print('%s called' % self.__class__.__name__)
        raise TypeError(self.__class__.__name__)


def testBeforeTraverse(self):
    """
    Zope supports a 'before traverse' hook that is used for several
    features, including 'Site Access Rules'. It is implemented using a
    special API for registering hooks, and the hooks themselves are
    called during traversal by ZPublisher.

    >>> import sys
    >>> import logging
    >>> from ZPublisher import BeforeTraverse

    >>> root = DummyObjectBasic()
    >>> request = makeBaseRequest(root)

    >>> container = DummyObjectBasic()
    >>> root.container = container

    >>> obj = DummyObjectBasic()
    >>> container.obj = obj

    Setup a broken hook as the before traverse hook for the
    container. That will create a 'MultiHook' object:

    >>> BeforeTraverse.registerBeforeTraverse(container, BrokenHook(),
    ...    'broken_hook')

    >>> container.__before_publishing_traverse__
    <ZPublisher.BeforeTraverse.MultiHook ...>

    >>> container.__before_traverse__
    {(99, 'broken_hook'): <ZPublisher.tests.testBeforeTraverse.BrokenHook ...>}

    Setup logging so we can see the actual exception being logged:

    >>> logger = logging.getLogger('ZPublisher')
    >>> level = logger.level
    >>> handlers = logger.handlers[:]

    >>> logger.addHandler(logging.StreamHandler(sys.stdout))
    >>> logger.setLevel(logging.ERROR)

    Now do the actual traversal:

    >>> _ = request.traverse('container/obj')
    BrokenHook called
    '__before_publishing_traverse__' call ... failed.
    Traceback (most recent call last):
    ...
    TypeError: BrokenHook

    Unregister the broken hook:

    >>> _ = BeforeTraverse.unregisterBeforeTraverse(container, 'broken_hook')

    The list of 'before traverse' hooks is empty:

    >>> container.__before_traverse__
    {}

    But the 'MultiHook' is not removed:

    >>> container.__before_publishing_traverse__
    <ZPublisher.BeforeTraverse.MultiHook ...>

    If you have an object in the same container that you want to call
    during traversal you can register a 'NameCaller' as the hook
    instead, and it will delegate to the callable by looking it up as
    an attribute of the container:

    >>> container.broken_callable = BrokenHook()
    >>> BeforeTraverse.registerBeforeTraverse(container,
    ...         BeforeTraverse.NameCaller('broken_callable'),
    ...         'broken_callable')

    >>> container.__before_traverse__
    {(99, 'broken_callable'): <ZPublisher.BeforeTraverse.NameCaller ...>}

    Now do the actual traversal:

    >>> _ = request.traverse('container/obj')
    BrokenHook called
    BeforeTraverse: Error while invoking hook: "broken_callable"
    Traceback (most recent call last):
    ...
    TypeError: BrokenHook

    Unregister the broken hook:

    >>> _ = BeforeTraverse.unregisterBeforeTraverse(
    ...         container, 'broken_callable')

    The list of 'before traverse' hooks is empty:

    >>> container.__before_traverse__
    {}

    But the 'MultiHook' is not removed:

    >>> container.__before_publishing_traverse__
    <ZPublisher.BeforeTraverse.MultiHook ...>

    Finally, restore the logger state:

    >>> logger.setLevel(level)
    >>> logger.handlers = handlers[:]

    """


def test_suite():
    return doctest.DocTestSuite(optionflags=doctest.ELLIPSIS)
