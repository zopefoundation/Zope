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
"""Python Object Publisher -- Publish Python objects on web servers
"""
import os
import sys
from thread import allocate_lock
import transaction
from urlparse import urlparse

from six import reraise
from zExceptions import (
    HTTPOk,
    HTTPRedirection,
    Redirect,
)
from zope.event import notify
from zope.publisher.interfaces import ISkinnable
from zope.publisher.interfaces.browser import IBrowserPage
from zope.publisher.skinnable import setDefaultSkin
from zope.security.management import newInteraction, endInteraction

from ZPublisher.mapply import mapply
from ZPublisher import pubevents
from ZPublisher import Retry
from ZPublisher.HTTPRequest import HTTPRequest as Request
from ZPublisher.HTTPResponse import HTTPResponse as Response


def call_object(object, args, request):
    return object(*args)


def missing_name(name, request):
    if name == 'self':
        return request['PARENTS'][0]
    request.response.badRequestError(name)


def dont_publish_class(klass, request):
    request.response.forbiddenError("class %s" % klass.__name__)

_default_debug_mode = False
_default_realm = None


def set_default_debug_mode(debug_mode):
    global _default_debug_mode
    _default_debug_mode = debug_mode


def set_default_authentication_realm(realm):
    global _default_realm
    _default_realm = realm


def publish(request, module_name, after_list, debug=0,
            # Optimize:
            call_object=call_object,
            missing_name=missing_name,
            dont_publish_class=dont_publish_class,
            mapply=mapply,
            ):

    (bobo_before, bobo_after, object, realm, debug_mode, err_hook,
     validated_hook, transactions_manager) = get_module_info(module_name)

    parents = None
    response = None

    try:
        notify(pubevents.PubStart(request))
        # TODO pass request here once BaseRequest implements IParticipation
        newInteraction()

        request.processInputs()

        request_get = request.get
        response = request.response

        # First check for "cancel" redirect:
        if request_get('SUBMIT', '').strip().lower() == 'cancel':
            cancel = request_get('CANCEL_ACTION', '')
            if cancel:
                # Relative URLs aren't part of the spec, but are accepted by
                # some browsers.
                for part, base in zip(urlparse(cancel)[:3],
                                      urlparse(request['BASE1'])[:3]):
                    if not part:
                        continue
                    if not part.startswith(base):
                        cancel = ''
                        break
            if cancel:
                raise Redirect(cancel)

        after_list[0] = bobo_after
        if debug_mode:
            response.debug_mode = debug_mode
        if realm and not request.get('REMOTE_USER', None):
            response.realm = realm

        if bobo_before is not None:
            bobo_before()

        # Get the path list.
        # According to RFC1738 a trailing space in the path is valid.
        path = request_get('PATH_INFO')

        request['PARENTS'] = parents = [object]

        if transactions_manager:
            transactions_manager.begin()

        object = request.traverse(path, validated_hook=validated_hook)

        if IBrowserPage.providedBy(object):
            request.postProcessInputs()

        notify(pubevents.PubAfterTraversal(request))

        if transactions_manager:
            transactions_manager.recordMetaData(object, request)

        ok_exception = None
        try:
            result = mapply(object, request.args, request,
                            call_object, 1,
                            missing_name,
                            dont_publish_class,
                            request, bind=1)
        except (HTTPOk, HTTPRedirection) as exc:
            ok_exception = exc
        else:
            if result is not response:
                response.setBody(result)

        notify(pubevents.PubBeforeCommit(request))

        if transactions_manager:
            transactions_manager.commit()

        notify(pubevents.PubSuccess(request))
        endInteraction()

        if ok_exception:
            raise ok_exception

        return response
    except:
        # save in order to give 'PubFailure' the original exception info
        exc_info = sys.exc_info()
        # DM: provide nicer error message for FTP
        sm = None
        if response is not None:
            sm = getattr(response, "setMessage", None)

        if sm is not None:
            from asyncore import compact_traceback
            cl, val = sys.exc_info()[:2]
            sm('%s: %s %s' % (
                getattr(cl, '__name__', cl), val,
                debug_mode and compact_traceback()[-1] or ''))

        # debug is just used by tests (has nothing to do with debug_mode!)
        if not debug and err_hook is not None:
            retry = False
            if parents:
                parents = parents[0]
            try:
                try:
                    return err_hook(parents, request,
                                    sys.exc_info()[0],
                                    sys.exc_info()[1],
                                    sys.exc_info()[2],
                                    )
                except Retry:
                    if not request.supports_retry():
                        return err_hook(parents, request,
                                        sys.exc_info()[0],
                                        sys.exc_info()[1],
                                        sys.exc_info()[2],
                                        )
                    retry = True
            finally:
                # Note: 'abort's can fail.
                # Nevertheless, we want end request handling.
                try:
                    try:
                        notify(pubevents.PubBeforeAbort(
                            request, exc_info, retry))
                    finally:
                        if transactions_manager:
                            transactions_manager.abort()
                finally:
                    endInteraction()
                    notify(pubevents.PubFailure(request, exc_info, retry))

            # Only reachable if Retry is raised and request supports retry.
            newrequest = request.retry()
            request.close()  # Free resources held by the request.

            # Set the default layer/skin on the newly generated request
            if ISkinnable.providedBy(newrequest):
                setDefaultSkin(newrequest)
            try:
                return publish(newrequest, module_name, after_list, debug)
            finally:
                newrequest.close()

        else:
            # Note: 'abort's can fail.
            # Nevertheless, we want end request handling.
            try:
                try:
                    notify(pubevents.PubBeforeAbort(request, exc_info, False))
                finally:
                    if transactions_manager:
                        transactions_manager.abort()
            finally:
                endInteraction()
                notify(pubevents.PubFailure(request, exc_info, False))
            raise


def publish_module_standard(
        module_name,
        stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr,
        environ=os.environ, debug=0, request=None, response=None):
    must_die = 0
    status = 200
    after_list = [None]
    try:
        try:
            if response is None:
                response = Response(stdout=stdout, stderr=stderr)
            else:
                stdout = response.stdout

            # debug is just used by tests (has nothing to do with debug_mode!)
            response.handle_errors = not debug

            if request is None:
                request = Request(stdin, environ, response)

            # make sure that the request we hand over has the
            # default layer/skin set on it; subsequent code that
            # wants to look up views will likely depend on it
            if ISkinnable.providedBy(request):
                setDefaultSkin(request)

            response = publish(request, module_name, after_list, debug=debug)
        except (SystemExit, ImportError):
            # XXX: Rendered ImportErrors were never caught here because they
            # were re-raised as string exceptions. Maybe we should handle
            # ImportErrors like all other exceptions. Currently they are not
            # re-raised at all, so they don't show up here.
            must_die = sys.exc_info()
            request.response.exception(1)
        except:
            # debug is just used by tests (has nothing to do with debug_mode!)
            if debug:
                raise
            request.response.exception()
            status = response.getStatus()

        if response:
            outputBody = getattr(response, 'outputBody', None)
            if outputBody is not None:
                outputBody()
            else:
                response = str(response)
                if response:
                    stdout.write(response)

        # The module defined a post-access function, call it
        if after_list[0] is not None:
            after_list[0]()

    finally:
        if request is not None:
            request.close()

    if must_die:
        # Try to turn exception value into an exit code.
        try:
            if hasattr(must_die[1], 'code'):
                code = must_die[1].code
            else:
                code = int(must_die[1])
        except:
            code = must_die[1] and 1 or 0
        if hasattr(request.response, '_requestShutdown'):
            request.response._requestShutdown(code)

        try:
            reraise(must_die[0], must_die[1], must_die[2])
        finally:
            must_die = None

    return status

_l = allocate_lock()


def get_module_info(module_name, modules={},
                    acquire=_l.acquire,
                    release=_l.release):

    if module_name in modules:
        return modules[module_name]

    if module_name[-4:] == '.cgi':
        module_name = module_name[:-4]

    acquire()
    tb = None
    g = globals()
    try:
        try:
            module = __import__(module_name, g, g, ('__doc__',))

            # Let the app specify a realm
            if hasattr(module, '__bobo_realm__'):
                realm = module.__bobo_realm__
            elif _default_realm is not None:
                realm = _default_realm
            else:
                realm = module_name

            # Check for debug mode
            debug_mode = None
            if hasattr(module, '__bobo_debug_mode__'):
                debug_mode = bool(module.__bobo_debug_mode__)
            else:
                debug_mode = _default_debug_mode

            bobo_before = getattr(module, "__bobo_before__", None)
            bobo_after = getattr(module, "__bobo_after__", None)

            if hasattr(module, 'bobo_application'):
                object = module.bobo_application
            elif hasattr(module, 'web_objects'):
                object = module.web_objects
            else:
                object = module

            error_hook = getattr(module, 'zpublisher_exception_hook', None)
            validated_hook = getattr(module, 'zpublisher_validated_hook', None)

            transactions_manager = getattr(
                module, 'zpublisher_transactions_manager', None)
            if not transactions_manager:
                # Create a default transactions manager for use
                # by software that uses ZPublisher and ZODB but
                # not the rest of Zope.
                transactions_manager = DefaultTransactionsManager()

            info = (bobo_before, bobo_after, object, realm, debug_mode,
                    error_hook, validated_hook, transactions_manager)

            modules[module_name] = modules[module_name + '.cgi'] = info

            return info
        except Exception:
            t, v, tb = sys.exc_info()
            reraise(t, str(v), tb)
    finally:
        tb = None
        release()


class DefaultTransactionsManager:

    def begin(self):
        transaction.begin()

    def commit(self):
        transaction.commit()

    def abort(self):
        transaction.abort()

    def recordMetaData(self, object, request):
        # Is this code needed?
        request_get = request.get
        T = transaction.get()
        T.note(request_get('PATH_INFO'))
        auth_user = request_get('AUTHENTICATED_USER', None)
        if auth_user is not None:
            T.setUser(auth_user, request_get('AUTHENTICATION_PATH'))


def publish_module(module_name,
                   stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr,
                   environ=os.environ, debug=0, request=None, response=None):
    """ publish a Python module """
    return publish_module_standard(module_name, stdin, stdout, stderr,
                                   environ, debug, request, response)
