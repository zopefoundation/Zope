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
from cStringIO import StringIO
import sys
from thread import allocate_lock
import time

import transaction
from zExceptions import (
    HTTPOk,
    HTTPRedirection,
    Unauthorized,
)
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
        g = globals()
        module = __import__(module_name, g, g, ('__doc__',))

        # Let the app specify a realm
        realm = module_name
        if _DEFAULT_REALM is not None:
            realm = _DEFAULT_REALM

        app = getattr(module, 'bobo_application', module)
        bobo_before = getattr(module, '__bobo_before__', None)
        bobo_after = getattr(module, '__bobo_after__', None)
        error_hook = getattr(module, 'zpublisher_exception_hook', None)
        validated_hook = getattr(module, 'zpublisher_validated_hook', None)
        transactions_manager = getattr(
            module, 'zpublisher_transactions_manager', transaction.manager)

        info = (bobo_before, bobo_after, app, realm, _DEFAULT_DEBUG_MODE,
                error_hook, validated_hook, transactions_manager)

        _MODULES[module_name] = info
        return info


class WSGIResponse(HTTPResponse):
    """A response object for WSGI

    This Response object knows nothing about ZServer, but tries to be
    compatible with the ZServerHTTPResponse.
    """
    _streaming = 0
    _http_version = None
    _server_version = None

    # Append any "cleanup" functions to this list.
    after_list = ()

    def finalize(self):

        headers = self.headers
        body = self.body

        # set 204 (no content) status if 200 and response is empty
        # and not streaming
        if ('content-type' not in headers and
                'content-length' not in headers and
                not self._streaming and self.status == 200):
            self.setStatus('nocontent')

        # add content length if not streaming
        content_length = headers.get('content-length')

        if content_length is None and not self._streaming:
            self.setHeader('content-length', len(body))

        return '%s %s' % (self.status, self.errmsg), self.listHeaders()

    def listHeaders(self):
        result = []
        if self._server_version:
            result.append(('Server', self._server_version))

        result.append(('Date', build_http_date(_now())))
        result.extend(HTTPResponse.listHeaders(self))
        return result

    def _unauthorized(self):
        self.setStatus(401)
        realm = self.realm
        if realm:
            self.setHeader('WWW-Authenticate', 'basic realm="%s"' % realm, 1)

    def write(self, data):
        """ Add data to our output stream.

        HTML data may be returned using a stream-oriented interface.
        This allows the browser to display partial results while
        computation of a response to proceed.
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


def publish(request, module_info):
    (bobo_before,
     bobo_after,
     object,
     realm,
     debug_mode,
     err_hook,
     validated_hook,
     transactions_manager) = module_info

    notify(pubevents.PubStart(request))
    newInteraction()
    try:
        request.processInputs()
        response = request.response

        if bobo_after is not None:
            response.after_list += (bobo_after,)

        if debug_mode:
            response.debug_mode = debug_mode

        if realm and not request.get('REMOTE_USER', None):
            response.realm = realm

        if bobo_before is not None:
            bobo_before()

        # Get the path list.
        # According to RFC1738 a trailing space in the path is valid.
        path = request.get('PATH_INFO')

        request['PARENTS'] = [object]

        if transactions_manager:
            transactions_manager.begin()

        object = request.traverse(path, validated_hook=validated_hook)
        notify(pubevents.PubAfterTraversal(request))

        if transactions_manager:
            recordMetaData(object, request)

        ok_exception = None
        try:
            result = mapply(object,
                            request.args,
                            request,
                            call_object,
                            1,
                            missing_name,
                            dont_publish_class,
                            request,
                            bind=1)
        except (HTTPOk, HTTPRedirection) as exc:
            # 2xx and 3xx responses raised as exceptions are considered
            # successful.
            ok_exception = exc
        else:
            if result is not response:
                response.setBody(result)

        notify(pubevents.PubBeforeCommit(request))

        if transactions_manager:
            transactions_manager.commit()
            notify(pubevents.PubSuccess(request))

        if ok_exception:
            raise ok_exception

    finally:
        endInteraction()

    return response


def publish_module(environ, start_response,
                   _publish=publish,  # only for testing
                   _response=None,
                   _response_factory=WSGIResponse,
                   _request=None,
                   _request_factory=HTTPRequest,
                   _module_name='Zope2',
                   ):
    module_info = get_module_info(_module_name)
    transactions_manager = module_info[7]

    status = 200
    stdout = StringIO()
    stderr = StringIO()
    if _response is None:
        response = _response_factory(stdout=stdout, stderr=stderr)
    else:
        response = _response
    response._http_version = environ['SERVER_PROTOCOL'].split('/')[1]
    response._server_version = environ.get('SERVER_SOFTWARE')

    if _request is None:
        request = _request_factory(environ['wsgi.input'], environ, response)
    else:
        request = _request

    setDefaultSkin(request)

    try:
        try:
            response = _publish(request, module_info)
        except Exception:
            try:
                exc_info = sys.exc_info()
                notify(pubevents.PubBeforeAbort(
                    request, exc_info, request.supports_retry()))

                if transactions_manager:
                    transactions_manager.abort()

                notify(pubevents.PubFailure(
                    request, exc_info, request.supports_retry()))
            finally:
                del exc_info
            raise
    except Unauthorized:
        response._unauthorized()
    except HTTPRedirection as exc:
        response.redirect(exc)

    # Start the WSGI server response
    status, headers = response.finalize()
    start_response(status, headers)

    body = response.body

    if isinstance(body, IOBase) or IUnboundStreamIterator.providedBy(body):
        result = body
    else:
        # If somebody used response.write, that data will be in the
        # stdout StringIO, so we put that before the body.
        result = (stdout.getvalue(), response.body)

    request.close()  # this aborts the transaction!
    stdout.close()

    for func in response.after_list:
        func()

    # Return the result body iterable.
    return result
