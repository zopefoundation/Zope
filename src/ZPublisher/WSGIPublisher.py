##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
""" Python Object Publisher -- Publish Python objects on web servers
"""
from contextlib import contextmanager, closing
from cStringIO import StringIO
import sys
from thread import allocate_lock
import time

from AccessControl.SecurityManagement import newSecurityManager
from AccessControl.SecurityManagement import noSecurityManager
import transaction
from transaction.interfaces import TransientError
from zExceptions import (
    HTTPOk,
    HTTPRedirection,
    Unauthorized,
)
from ZODB.POSException import ConflictError
from zope.event import notify
from zope.security.management import newInteraction, endInteraction
from zope.publisher.skinnable import setDefaultSkin

from ZPublisher.HTTPRequest import HTTPRequest
from ZPublisher.HTTPResponse import HTTPResponse
from ZPublisher.Iterators import IUnboundStreamIterator, IStreamIterator
from ZPublisher.mapply import mapply
from ZPublisher import pubevents
from ZPublisher.utils import recordMetaData

_NOW = None  # overwrite for testing
MONTHNAME = [None, 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
             'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
WEEKDAYNAME = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

if sys.version_info >= (3, ):
    from io import IOBase
else:
    IOBase = file  # NOQA

_DEFAULT_DEBUG_MODE = False
_DEFAULT_REALM = None
_MODULE_LOCK = allocate_lock()
_MODULES = {}


def _now():
    if _NOW is not None:
        return _NOW
    return time.time()


def build_http_date(when):
    year, month, day, hh, mm, ss, wd, y, z = time.gmtime(when)
    return "%s, %02d %3s %4d %02d:%02d:%02d GMT" % (
        WEEKDAYNAME[wd], day, MONTHNAME[month], year, hh, mm, ss)


def call_object(obj, args, request):
    return obj(*args)


def dont_publish_class(klass, request):
    request.response.forbiddenError("class %s" % klass.__name__)


def missing_name(name, request):
    if name == 'self':
        return request['PARENTS'][0]
    request.response.badRequestError(name)


def validate_user(request, user):
    newSecurityManager(request, user)


def set_default_debug_mode(debug_mode):
    global _DEFAULT_DEBUG_MODE
    _DEFAULT_DEBUG_MODE = debug_mode


def set_default_authentication_realm(realm):
    global _DEFAULT_REALM
    _DEFAULT_REALM = realm


def get_module_info(module_name='Zope2'):
    global _MODULES
    info = _MODULES.get(module_name)
    if info is not None:
        return info

    with _MODULE_LOCK:
        module = __import__(module_name)
        app = getattr(module, 'bobo_application', module)
        realm = _DEFAULT_REALM if _DEFAULT_REALM is not None else module_name
        _MODULES[module_name] = info = (app, realm, _DEFAULT_DEBUG_MODE)
    return info


class WSGIRequest(HTTPRequest):
    """A request object for WSGI
    """
    pass


class WSGIResponse(HTTPResponse):
    """A response object for WSGI
    """
    _streaming = 0
    _http_version = None
    _server_version = None

    # Append any "cleanup" functions to this list.
    after_list = ()

    def finalize(self):
        # Set 204 (no content) status if 200 and response is empty
        # and not streaming.
        if ('content-type' not in self.headers and
                'content-length' not in self.headers and
                not self._streaming and self.status == 200):
            self.setStatus('nocontent')

        # Add content length if not streaming.
        content_length = self.headers.get('content-length')
        if content_length is None and not self._streaming:
            self.setHeader('content-length', len(self.body))

        return ('%s %s' % (self.status, self.errmsg), self.listHeaders())

    def listHeaders(self):
        result = []
        if self._server_version:
            result.append(('Server', self._server_version))

        result.append(('Date', build_http_date(_now())))
        result.extend(HTTPResponse.listHeaders(self))
        return result

    def _unauthorized(self, exc=None):
        status = exc.getStatus() if exc is not None else 401
        self.setStatus(status)
        if self.realm:
            self.setHeader('WWW-Authenticate',
                           'basic realm="%s"' % self.realm, 1)

    def write(self, data):
        """Add data to our output stream.

        HTML data may be returned using a stream-oriented interface.
        This allows the browser to display partial results while
        computation of a response proceeds.
        """
        if not self._streaming:
            notify(pubevents.PubBeforeStreaming(self))
            self._streaming = 1
            self.stdout.flush()

        self.stdout.write(data)

    def setBody(self, body, title='', is_error=0):
        if isinstance(body, IOBase):
            body.seek(0, 2)
            length = body.tell()
            body.seek(0)
            self.setHeader('Content-Length', '%d' % length)
            self.body = body
        elif IStreamIterator.providedBy(body):
            self.body = body
            HTTPResponse.setBody(self, '', title, is_error)
        elif IUnboundStreamIterator.providedBy(body):
            self.body = body
            self._streaming = 1
            HTTPResponse.setBody(self, '', title, is_error)
        else:
            HTTPResponse.setBody(self, body, title, is_error)

    def __str__(self):
        raise NotImplementedError


@contextmanager
def transaction_pubevents(request, tm=transaction.manager):
    ok_exception = None
    try:
        setDefaultSkin(request)
        newInteraction()
        tm.begin()
        notify(pubevents.PubStart(request))
        try:
            yield None
        except (HTTPOk, HTTPRedirection) as exc:
            ok_exception = exc

        notify(pubevents.PubBeforeCommit(request))
        if tm.isDoomed():
            tm.abort()
        else:
            tm.commit()
        notify(pubevents.PubSuccess(request))
    except Exception:
        exc_info = sys.exc_info()
        notify(pubevents.PubBeforeAbort(
            request, exc_info, request.supports_retry()))
        tm.abort()
        notify(pubevents.PubFailure(
            request, exc_info, request.supports_retry()))
        raise
    finally:
        endInteraction()
        if ok_exception is not None:
            raise ok_exception


def publish(request, module_info):
    obj, realm, debug_mode = module_info

    request.processInputs()
    response = request.response

    if debug_mode:
        response.debug_mode = debug_mode

    if realm and not request.get('REMOTE_USER', None):
        response.realm = realm

    noSecurityManager()

    # Get the path list.
    # According to RFC1738 a trailing space in the path is valid.
    path = request.get('PATH_INFO')
    request['PARENTS'] = [obj]

    obj = request.traverse(path, validated_hook=validate_user)
    notify(pubevents.PubAfterTraversal(request))
    recordMetaData(obj, request)

    result = mapply(obj,
                    request.args,
                    request,
                    call_object,
                    1,
                    missing_name,
                    dont_publish_class,
                    request,
                    bind=1)
    if result is not response:
        response.setBody(result)

    return response


def _publish_response(request, response, module_info, _publish=publish):
    try:
        with transaction_pubevents(request):
            response = _publish(request, module_info)
    except Unauthorized as exc:
        response._unauthorized(exc)
    except HTTPRedirection as exc:
        # TODO: HTTPOk is only handled by the httpexceptions
        # middleware, maybe it should be handled here.
        response.redirect(exc)

    return response


def publish_module(environ, start_response,
                   _publish=publish,  # only for testing
                   _response=None,
                   _response_factory=WSGIResponse,
                   _request=None,
                   _request_factory=WSGIRequest,
                   _module_name='Zope2'):
    module_info = get_module_info(_module_name)
    result = ()

    with closing(StringIO()) as stdout, closing(StringIO()) as stderr:
        response = (_response if _response is not None else
                    _response_factory(stdout=stdout, stderr=stderr))
        response._http_version = environ['SERVER_PROTOCOL'].split('/')[1]
        response._server_version = environ.get('SERVER_SOFTWARE')

        request = (_request if _request is not None else
                   _request_factory(environ['wsgi.input'], environ, response))

        for i in range(getattr(request, 'retry_max_count', 3) + 1):
            try:
                response = _publish_response(
                    request, response, module_info, _publish=_publish)
                break
            except (ConflictError, TransientError) as exc:
                if request.supports_retry():
                    new_request = request.retry()
                    request.close()
                    request = new_request
                    response = new_request.response
                else:
                    raise
            finally:
                request.close()

        # Start the WSGI server response
        status, headers = response.finalize()
        start_response(status, headers)

        if (isinstance(response.body, IOBase) or
                IUnboundStreamIterator.providedBy(response.body)):
            result = response.body
        else:
            # If somebody used response.write, that data will be in the
            # stdout StringIO, so we put that before the body.
            result = (stdout.getvalue(), response.body)

        for func in response.after_list:
            func()

    # Return the result body iterable.
    return result
