from zope.interface import Attribute
from zope.interface import Interface


#############################################################################
# Publication events
#  These are events notified in 'ZPublisher.Publish.publish'.


class IPubEvent(Interface):
    '''Base class for publication events.

    Publication events are notified in 'ZPublisher.Publish.publish' to
    inform about publications (aka requests) and their fate.
    '''
    request = Attribute('The request being affected')


class IPubStart(IPubEvent):
    '''Event notified at the beginning of 'ZPublisher.Publish.publish'.'''


class IPubEnd(IPubEvent):
    '''Event notified after request processing.

    Note that a retried request ends before the retrial, the retrial
    itself is considered a new event.
    '''


class IPubSuccess(IPubEnd):
    '''A successful request processing.'''


class IPubFailure(IPubEnd):
    '''A failed request processing.

    Note: If a subscriber to 'IPubSuccess' raises an exception,
    then 'IPubFailure' may be notified in addition to 'IPubSuccess'.
    '''
    exc_info = Attribute(
        '''The exception info as returned by 'sys.exc_info()'.''')
    retry = Attribute('Whether the request will be retried')


class IPubAfterTraversal(IPubEvent):
    """notified after traversal and an (optional) authentication."""


class IPubBeforeCommit(IPubEvent):
    """notified immediately before the transaction commit (i.e. after the main
    request processing is finished).
    """


class IPubBeforeAbort(IPubEvent):
    """notified immediately before the transaction abort (i.e. after the main
    request processing is finished, and there was an error).
    """
    exc_info = Attribute(
        '''The exception info as returned by 'sys.exc_info()'.''')
    retry = Attribute('Whether the request will be retried')


class IPubBeforeStreaming(Interface):
    """Event fired just before a streaming response is initiated, i.e. when
    something calls response.write() for the first time. Note that this is
    carries a reference to the *response*, not the request.
    """
    response = Attribute("The current HTTP response")


class UseTraversalDefault(Exception):
    """Indicate default traversal in ``__bobo_traverse__``

    This exception can be raised by '__bobo_traverse__' implementations to
    indicate that it has no special casing for the given name and that standard
    traversal logic should be applied.
    """


###############################################################################
# XML-RPC control

class IXmlrpcChecker(Interface):
    """Utility interface to control Zope's built-in XML-RPC support."""
    def __call__(request):
        """return true, when Zope's internal XML-RPC support should be used.

        Only called for a non-SOAP POST request whose `Content-Type`
        contains `text/xml` (any other request automatically does not
        use Zope's built-in XML-RPC).

        Note: this is called very early during request handling when most
        typical attributes of *request* are not yet set up -- e.g. it
        cannot rely on information in `form` or `other`.
        Usually, it will look up information in `request.environ`
        which at this time is guaranteed (only) to contain the
        typical CGI information, such as `PATH_INFO` and `QUERY_STRING`.
        """


###############################################################################
# Cookie policies

class ICookieParamPolicy(Interface):
    """Utility interface to customize cookie parameter handling."""

    def parameters(name, attrs):
        """generate the parameters for the cookie with *name* and *attrs*.

        Each parameter is described by a pair
        *normalized_name*, *normalized_value*.
        ``ZPublisher.cookie.convertCookieParameter`` can be used to achieve
        the normalization.

        *attrs* is a mapping describing the cookie's value
        (key ``value``) and its parameters.
        The  key and value for a parameter are its
        "normalized name" and "normalized value".
        The normalized name corresponds to the official
        parameter name, usually defined by a standard such as RFC 6265.
        You can use
        ``ZPublisher.cookie.normalizeCookieParameterName`` to
        normalize a parameter name.
        The normalized value is either ``None`` (drop the parameter),
        ``True`` (drop the parameter's value) or an ASCII string (use
        as the parameter's value).

        The policy can use ``parameters`` e.g. to add security parameters
        such as ``HttpOnly``, ``Secure``, ``SameSite``.

        Some security parameters may depend on request
        details (e.g. whether ``https`` is used).
        In those cases, you can use e.g. ``zope.globalrequest``
        to access the request.
        """

    def check_consistency(name, attrs):
        """raise ``ValueError`` if the cookie definition is inconsistent.

        E.g. ``SameSite=None`` is allowed only together with ``Secure``.
        """


class ICookieValuePolicy(Interface):
    """Utility interface to customize cookie value handling.

    Note: cookies are processed very early during request processing.
    At this time, only the global utility registry is available.
    For this reason, a utility for this interface is looked up
    only in the global component registry.
    Local utility registrations are ignored.
    """
    def dump(name, value):
        """Used to serialize *value* for cookie with name *name*.

        RFC 6265 requires that the cookie value representation
        in the response consists only of ASCII characters
        excluding control characters, blank, double quote,
        comma, semicolon, and backslash.
        ``dump`` is used to ensure this.
        """

    def load(name, value):
        """Used to deserialize *value* for cookie named *name*.

        The inverse of ``dump``.
        """
