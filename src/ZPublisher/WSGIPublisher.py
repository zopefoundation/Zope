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
import sys
from _thread import allocate_lock
from contextlib import closing
from contextlib import contextmanager
from io import BytesIO
from io import IOBase

import transaction
from AccessControl.SecurityManagement import getSecurityManager
from AccessControl.SecurityManagement import newSecurityManager
from AccessControl.SecurityManagement import noSecurityManager
from Acquisition import aq_acquire
from transaction.interfaces import TransientError
from zExceptions import Unauthorized
from zExceptions import upgradeException
from zope.component import queryMultiAdapter
from zope.event import notify
from zope.globalrequest import clearRequest
from zope.globalrequest import setRequest
from zope.publisher.skinnable import setDefaultSkin
from zope.security.management import endInteraction
from zope.security.management import newInteraction
from ZPublisher import pubevents
from ZPublisher.HTTPRequest import WSGIRequest
from ZPublisher.HTTPResponse import WSGIResponse
from ZPublisher.Iterators import IUnboundStreamIterator
from ZPublisher.mapply import mapply
from ZPublisher.utils import recordMetaData


_FILE_TYPES = (IOBase, )
_DEFAULT_DEBUG_EXCEPTIONS = False
_DEFAULT_DEBUG_MODE = False
_DEFAULT_REALM = None
_MODULE_LOCK = allocate_lock()
_MODULES = {}
_WEBDAV_SOURCE_PORT = 0


# This is copied from the six module
def reraise(tp, value, tb=None):
    try:
        if value is None:
            value = tp()
        if value.__traceback__ is not tb:
            raise value.with_traceback(tb)
        raise value
    finally:
        value = None
        tb = None


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


def set_default_debug_exceptions(debug_exceptions):
    global _DEFAULT_DEBUG_EXCEPTIONS
    _DEFAULT_DEBUG_EXCEPTIONS = debug_exceptions


def set_webdav_source_port(port):
    global _WEBDAV_SOURCE_PORT
    _WEBDAV_SOURCE_PORT = port


def get_debug_exceptions():
    global _DEFAULT_DEBUG_EXCEPTIONS
    return _DEFAULT_DEBUG_EXCEPTIONS


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
    view = queryMultiAdapter((exc, request), name='index.html')
    parents = request.get('PARENTS')

    if view is None and parents:
        # Try a fallback based on the old standard_error_message
        # DTML Method in the ZODB
        view = queryMultiAdapter((exc, request),
                                 name='standard_error_message')
        root_parent = parents[0]
        try:
            aq_acquire(root_parent, 'standard_error_message')
        except (AttributeError, KeyError):
            view = None

    if view is not None:
        # Wrap the view in the context in which the exception happened.
        if parents:
            view.__parent__ = parents[0]

        # Set status and headers from the exception on the response,
        # which would usually happen while calling the exception
        # with the (environ, start_response) WSGI tuple.
        response.setStatus(exc.__class__)
        if hasattr(exc, 'headers'):
            for key, value in exc.headers.items():
                response.setHeader(key, value)

        # Call the view so we can use it as the response body.
        body = view()

        # Explicitly set the content type header if it's not there yet so
        # the response does not get served with the text/plain default.
        # But only do this when there is a body.
        # An empty body may indicate a 304 NotModified response,
        # and setting a content type header will change the stored header
        # in caching servers such as Varnish.
        # See https://github.com/zopefoundation/Zope/issues/1089
        if body and not response.getHeader('Content-Type'):
            response.setHeader('Content-Type', 'text/html')

        # Note: setBody would set the Content-Type header to text/plain
        # if it is not set yet, except when the body is empty.
        response.setBody(body)
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

        try:
            # Raise exception from app if handle-errors is False
            # (set by zope.testbrowser in some cases)
            if request.environ.get('x-wsgiorg.throw_errors', False):
                reraise(*exc_info)

            retry = False
            unauth = False
            debug_exc = getattr(response, 'debug_exceptions', False)

            # If the exception is transient and the request can be retried,
            # shortcut further processing. It makes no sense to have an
            # exception view registered for this type of exception.
            if isinstance(exc, TransientError) and request.supports_retry():
                retry = True
            else:
                # Handle exception view. Make sure an exception view that
                # blows up doesn't leave the user e.g. unable to log in.
                try:
                    exc_view_created = _exc_view_created_response(
                        exc, request, response)
                except Exception:
                    exc_view_created = False

                # _unauthorized modifies the response in-place. If this hook
                # is used, an exception view for Unauthorized has to merge
                # the state of the response and the exception instance.
                if isinstance(exc, Unauthorized):
                    unauth = True
                    exc.setRealm(response.realm)
                    response._unauthorized()
                    response.setStatus(exc.getStatus())

            # Notify subscribers that this request is failing.
            notify(pubevents.PubBeforeAbort(request, exc_info, retry))
            tm.abort()
            notify(pubevents.PubFailure(request, exc_info, retry))

            if retry or \
               (not unauth and (debug_exc or not exc_view_created)):
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

    response.debug_exceptions = get_debug_exceptions()

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

    # Set debug information from the active request on the open connection
    # Used to be done in ZApplicationWrapper.__bobo_traverse__ for ZServer
    try:
        # Grab the connection from the last (root application) object,
        # which usually has a connection available.
        request['PARENTS'][-1]._p_jar.setDebugInfo(request.environ,
                                                   request.other)
    except AttributeError:
        # If there is no connection don't worry
        pass

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
        if transaction.manager.manager._txn is not None:
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

    path_info = environ.get('PATH_INFO')
    if path_info:
        # BIG Comment, see discussion at
        # https://github.com/zopefoundation/Zope/issues/575
        #
        # The WSGI server automatically treats headers, including the
        # PATH_INFO, as latin-1 encoded bytestrings, according to PEP-3333. As
        # this causes headache I try to show the steps a URI takes in WebOb,
        # which is similar in other wsgi server implementations.
        # UTF-8 URL-encoded object-id 'täst':
        #   http://localhost/t%C3%A4st
        # unquote('/t%C3%A4st'.decode('ascii')) results in utf-8 encoded bytes
        #   b'/t\xc3\xa4st'
        # b'/t\xc3\xa4st'.decode('latin-1') latin-1 decoding due to PEP-3333
        #   '/tÃ¤st'
        # We now have a latin-1 decoded text, which was actually utf-8 encoded.
        # To reverse this we have to encode with latin-1 first.
        path_info = path_info.encode('latin-1')

        # So we can now decode with the right (utf-8) encoding to get text.
        # This encode/decode two-step with different encodings works because
        # of the way PEP-3333 restricts the type of string allowable for
        # request and response metadata. The allowed characters match up in
        # both latin-1 and utf-8.
        path_info = path_info.decode('utf-8')

        environ['PATH_INFO'] = path_info

    # See if this should be be marked up as WebDAV request.
    try:
        server_port = int(environ['SERVER_PORT'])
    except (KeyError, ValueError):
        server_port = 0

    if _WEBDAV_SOURCE_PORT and _WEBDAV_SOURCE_PORT == server_port:
        environ['WEBDAV_SOURCE_PORT'] = 1

        # GET needs special treatment. Traversal is forced to the
        # manage_DAVget method to get the unrendered sources.
        if environ['REQUEST_METHOD'].upper() == 'GET':
            environ['PATH_INFO'] = '%s/manage_DAVget' % environ['PATH_INFO']

    with closing(BytesIO()) as stdout, closing(BytesIO()) as stderr:
        new_response = (
            _response
            if _response is not None
            else _response_factory(stdout=stdout, stderr=stderr))
        new_response._http_version = environ['SERVER_PROTOCOL'].split('/')[1]
        new_response._server_version = environ.get('SERVER_SOFTWARE')

        new_request = (
            _request
            if _request is not None
            else _request_factory(environ['wsgi.input'],
                                  environ,
                                  new_response))

        for i in range(getattr(new_request, 'retry_max_count', 3) + 1):
            request = new_request
            response = new_response
            setRequest(request)
            try:
                with load_app(module_info) as new_mod_info:
                    with transaction_pubevents(request, response):
                        response = _publish(request, new_mod_info)

                        user = getSecurityManager().getUser()
                        if user is not None and \
                           user.getUserName() != 'Anonymous User':
                            environ['REMOTE_USER'] = user.getUserName()
                break
            except TransientError:
                if request.supports_retry():
                    request.delay_retry()  # Insert a time delay
                    new_request = request.retry()
                    new_response = new_request.response
                else:
                    raise
            finally:
                request.close()
                clearRequest()

        # Start the WSGI server response
        status, headers = response.finalize()
        start_response(status, headers)

        if isinstance(response.body, _FILE_TYPES) or \
           IUnboundStreamIterator.providedBy(response.body):
            if hasattr(response.body, 'read') and \
               'wsgi.file_wrapper' in environ:
                result = environ['wsgi.file_wrapper'](response.body)
            else:
                result = response.body
        else:
            # If somebody used response.write, that data will be in the
            # response.stdout BytesIO, so we put that before the body.
            result = (response.stdout.getvalue(), response.body)

        for func in response.after_list:
            func()

    # Return the result body iterable.
    return result
