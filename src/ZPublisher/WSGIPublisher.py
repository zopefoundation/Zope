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
from io import BytesIO
from io import IOBase
import sys

from AccessControl.SecurityManagement import newSecurityManager
from AccessControl.SecurityManagement import noSecurityManager
from six import reraise
from six.moves._thread import allocate_lock
import transaction
from transaction.interfaces import TransientError
from zExceptions import (
    Unauthorized,
    upgradeException,
)
from ZODB.POSException import ConflictError
from zope.component import queryMultiAdapter
from zope.event import notify
from zope.globalrequest import setRequest, clearRequest
from zope.security.management import newInteraction, endInteraction
from zope.publisher.skinnable import setDefaultSkin

from ZPublisher.HTTPRequest import WSGIRequest
from ZPublisher.HTTPResponse import WSGIResponse
from ZPublisher.Iterators import IUnboundStreamIterator
from ZPublisher.mapply import mapply
from ZPublisher import pubevents
from ZPublisher.utils import recordMetaData

if sys.version_info >= (3, ):
    _FILE_TYPES = (IOBase, )
else:
    _FILE_TYPES = (IOBase, file)  # NOQA

_DEFAULT_DEBUG_MODE = False
_DEFAULT_REALM = None
_MODULE_LOCK = allocate_lock()
_MODULES = {}


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


def _exc_view_created_response(exc, request, response):
    view = queryMultiAdapter((exc, request), name=u'index.html')
    if view is not None:
        # Wrap the view in the context in which the exception happened.
        parents = request.get('PARENTS')
        if parents:
            view.__parent__ = parents[0]

        # Set status and headers from the exception on the response,
        # which would usually happen while calling the exception
        # with the (environ, start_response) WSGI tuple.
        response.setStatus(exc.__class__)
        if hasattr(exc, 'headers'):
            for key, value in exc.headers.items():
                response.setHeader(key, value)

        # Set the response body to the result of calling the view.
        response.setBody(view())
        return True
    return False


@contextmanager
def transaction_pubevents(request, response, tm=transaction.manager):
    try:
        setDefaultSkin(request)
        newInteraction()
        tm.begin()
        notify(pubevents.PubStart(request))

        yield

        notify(pubevents.PubBeforeCommit(request))
        if tm.isDoomed():
            tm.abort()
        else:
            tm.commit()
        notify(pubevents.PubSuccess(request))
    except Exception as exc:
        # Normalize HTTP exceptions
        # (For example turn zope.publisher NotFound into zExceptions NotFound)
        exc_type, _ = upgradeException(exc.__class__, None)
        if not isinstance(exc, exc_type):
            exc = exc_type(str(exc))

        # Create new exc_info with the upgraded exception.
        exc_info = (exc_type, exc, sys.exc_info()[2])

        if isinstance(exc, Unauthorized):
            # _unauthorized modifies the response in-place. If this hook
            # is used, an exception view for Unauthorized has to merge
            # the state of the response and the exception instance.
            exc.setRealm(response.realm)
            response._unauthorized()
            response.setStatus(exc.getStatus())

        try:
            # Handle exception view
            exc_view_created = _exc_view_created_response(
                exc, request, response)

            notify(pubevents.PubBeforeAbort(
                request, exc_info, request.supports_retry()))
            tm.abort()
            notify(pubevents.PubFailure(
                request, exc_info, request.supports_retry()))

            if not (exc_view_created or isinstance(exc, Unauthorized)):
                reraise(*exc_info)
        finally:
            # Avoid traceback / exception reference cycle.
            del exc, exc_info
    finally:
        endInteraction()


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


@contextmanager
def load_app(module_info):
    app_wrapper, realm, debug_mode = module_info
    # Loads the 'OFS.Application' from ZODB.
    app = app_wrapper()

    try:
        yield (app, realm, debug_mode)
    finally:
        if transaction.manager._txn is not None:
            # Only abort a transaction, if one exists. Otherwise the
            # abort creates a new transaction just to abort it.
            transaction.abort()
        app._p_jar.close()


def publish_module(environ, start_response,
                   _publish=publish,  # only for testing
                   _response=None,
                   _response_factory=WSGIResponse,
                   _request=None,
                   _request_factory=WSGIRequest,
                   _module_name='Zope2'):
    module_info = get_module_info(_module_name)
    result = ()

    with closing(BytesIO()) as stdout, closing(BytesIO()) as stderr:
        response = (_response if _response is not None else
                    _response_factory(stdout=stdout, stderr=stderr))
        response._http_version = environ['SERVER_PROTOCOL'].split('/')[1]
        response._server_version = environ.get('SERVER_SOFTWARE')

        request = (_request if _request is not None else
                   _request_factory(environ['wsgi.input'], environ, response))

        for i in range(getattr(request, 'retry_max_count', 3) + 1):
            setRequest(request)
            try:
                with load_app(module_info) as new_mod_info:
                    with transaction_pubevents(request, response):
                        response = _publish(request, new_mod_info)
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
                clearRequest()

        # Start the WSGI server response
        status, headers = response.finalize()
        start_response(status, headers)

        if (isinstance(response.body, _FILE_TYPES) or
                IUnboundStreamIterator.providedBy(response.body)):
            result = response.body
        else:
            # If somebody used response.write, that data will be in the
            # stdout BytesIO, so we put that before the body.
            result = (stdout.getvalue(), response.body)

        for func in response.after_list:
            func()

    # Return the result body iterable.
    return result
