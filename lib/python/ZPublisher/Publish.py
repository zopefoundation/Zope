##############################################################################
#
# Copyright (c) 2002 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
__doc__="""Python Object Publisher -- Publish Python objects on web servers

$Id$"""

import sys, os
import transaction
from Response import Response
from Request import Request
from maybe_lock import allocate_lock
from mapply import mapply
from zExceptions import Redirect
from ZServer.HTTPResponse import ZServerHTTPResponse
from cStringIO import StringIO

class Retry(Exception):
    """Raise this to retry a request
    """

    def __init__(self, t=None, v=None, tb=None):
        self._args=t, v, tb

    def reraise(self):
        t, v, tb = self._args
        if t is None: t=Retry
        if tb is None: raise t, v
        try: raise t, v, tb
        finally: tb=None

def call_object(object, args, request):
    result=apply(object,args) # Type s<cr> to step into published object.
    return result

def missing_name(name, request):
    if name=='self': return request['PARENTS'][0]
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
     validated_hook, transactions_manager)= get_module_info(module_name)

    parents=None
    response=None
    try:
        request.processInputs()

        request_get=request.get
        response=request.response

        # First check for "cancel" redirect:
        if request_get('SUBMIT','').strip().lower()=='cancel':
            cancel=request_get('CANCEL_ACTION','')
            if cancel:
                raise Redirect, cancel

        after_list[0]=bobo_after
        if debug_mode:
            response.debug_mode=debug_mode
        if realm and not request.get('REMOTE_USER',None):
            response.realm=realm

        if bobo_before is not None:
            bobo_before()

        # Get the path list.
        # According to RFC1738 a trailing space in the path is valid.
        path=request_get('PATH_INFO')

        request['PARENTS']=parents=[object]

        if transactions_manager:
            transactions_manager.begin()

        object=request.traverse(path, validated_hook=validated_hook)

        if transactions_manager:
            transactions_manager.recordMetaData(object, request)

        result=mapply(object, request.args, request,
                      call_object,1,
                      missing_name,
                      dont_publish_class,
                      request, bind=1)

        if result is not response:
            response.setBody(result)

        if transactions_manager:
            transactions_manager.commit()

        return response
    except:

        # DM: provide nicer error message for FTP
        sm = None
        if response is not None:
            sm = getattr(response, "setMessage", None)

        if sm is not None:
            from asyncore import compact_traceback
            cl,val= sys.exc_info()[:2]
            sm('%s: %s %s' % (
                getattr(cl,'__name__',cl), val,
                debug_mode and compact_traceback()[-1] or ''))

        if err_hook is not None:
            if parents:
                parents=parents[0]
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
            finally:
                if transactions_manager:
                    transactions_manager.abort()

            # Only reachable if Retry is raised and request supports retry.
            newrequest=request.retry()
            request.close()  # Free resources held by the request.
            try:
                return publish(newrequest, module_name, after_list, debug)
            finally:
                newrequest.close()

        else:
            if transactions_manager:
                transactions_manager.abort()
            raise

from HTTPRequest import HTTPRequest
from ZServer.HTTPResponse import make_response

class WSGIPublisherApplication(object):
    """A WSGI application implementation for the zope2 publisher

    Instances of this class can be used as a WSGI application object.
    """
    #implements(interfaces.IWSGIApplication)

    def __call__(self, environ, start_response):
        """See zope.app.wsgi.interfaces.IWSGIApplication"""
        
        response = ZServerHTTPResponse(stdout=environ['wsgi.output'], stderr=StringIO())
        response._http_version = environ['SERVER_PROTOCOL'].split('/')[1]
        response._http_connection = environ.get('CONNECTION_TYPE', 'close')
        response._server_version = environ['SERVER_SOFTWARE']

        request = Request(environ['wsgi.input'], environ, response)

        # Let's support post-mortem debugging
        handle_errors = environ.get('wsgi.handleErrors', True)
        
        try:
            response = publish(request, 'Zope2', after_list=[None], 
                               debug=handle_errors)
        except SystemExit, v:
            must_die=sys.exc_info()
            request.response.exception(must_die)
        except ImportError, v:
            if isinstance(v, tuple) and len(v)==3: must_die=v
            elif hasattr(sys, 'exc_info'): must_die=sys.exc_info()
            else: must_die = SystemExit, v, sys.exc_info()[2]
            request.response.exception(1, v)
        except:
            request.response.exception()
            status=response.getStatus()

        if response:
            # Start the WSGI server response
            start_response(response.getHeader('status'), 
                           response.headers.items())
            result=str(response)
        # Return the result body iterable.
        request.close()
        response._finish(0)
        return (result,)
    

def fakeWrite(body):
    raise NotImplementedError(
        "Zope 2's HTTP Server does not support the WSGI write() function.")

def publish_module_standard(module_name,
                   stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr,
                   environ=os.environ, debug=0, request=None, response=None):

    # The WSGI way!
    def wsgi_start_response(status,response_headers,exc_info=None):
        return fakeWrite

    must_die=0
    status=200
    after_list=[None]
    if request is None:
        env = environ.copy()
    else:
        env = request
    env['wsgi.errors']       = sys.stderr
    env['wsgi.version']      = (1,0)
    env['wsgi.multithread']  = True
    env['wsgi.multiprocess'] = True
    env['wsgi.run_once']     = True
    env['wsgi.url_scheme']   = env['SERVER_PROTOCOL'].split('/')[0]
    if not env.has_key('wsgi.output'):
        env['wsgi.output'] = stdout
    if not env.has_key('wsgi.input'):
        env['wsgi.input']        = stdin

    application = WSGIPublisherApplication()
    body = application(env, wsgi_start_response)
    for b in body:
        env['wsgi.output'].write(b)
    env['wsgi.output'].close()
    # The module defined a post-access function, call it
    if after_list[0] is not None: after_list[0]()

    if must_die:
        # Try to turn exception value into an exit code.
        try:
            if hasattr(must_die[1], 'code'):
                code = must_die[1].code
            else: code = int(must_die[1])
        except:
            code = must_die[1] and 1 or 0
        if hasattr(request.response, '_requestShutdown'):
            request.response._requestShutdown(code)

        try: raise must_die[0], must_die[1], must_die[2]
        finally: must_die=None

    return status


_l=allocate_lock()
def get_module_info(module_name, modules={},
                    acquire=_l.acquire,
                    release=_l.release,
                    ):

    if modules.has_key(module_name): return modules[module_name]

    if module_name[-4:]=='.cgi': module_name=module_name[:-4]

    acquire()
    tb=None
    g = globals()
    try:
        try:
            module=__import__(module_name, g, g, ('__doc__',))

            # Let the app specify a realm
            if hasattr(module,'__bobo_realm__'):
                realm=module.__bobo_realm__
            elif _default_realm is not None:
                realm=_default_realm
            else:
                realm=module_name

            # Check for debug mode
            debug_mode=None
            if hasattr(module,'__bobo_debug_mode__'):
                debug_mode=not not module.__bobo_debug_mode__
            else:
                debug_mode = _default_debug_mode

            bobo_before = getattr(module, "__bobo_before__", None)
            bobo_after = getattr(module, "__bobo_after__", None)

            if hasattr(module,'bobo_application'):
                object=module.bobo_application
            elif hasattr(module,'web_objects'):
                object=module.web_objects
            else: object=module

            error_hook=getattr(module,'zpublisher_exception_hook', None)
            validated_hook=getattr(module,'zpublisher_validated_hook', None)

            transactions_manager=getattr(
                module,'zpublisher_transactions_manager', None)
            if not transactions_manager:
                # Create a default transactions manager for use
                # by software that uses ZPublisher and ZODB but
                # not the rest of Zope.
                transactions_manager = DefaultTransactionsManager()

            info= (bobo_before, bobo_after, object, realm, debug_mode,
                   error_hook, validated_hook, transactions_manager)

            modules[module_name]=modules[module_name+'.cgi']=info

            return info
        except:
            t,v,tb=sys.exc_info()
            v=str(v)
            raise ImportError, (t, v), tb
    finally:
        tb=None
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
        T= transaction.get()
        T.note(request_get('PATH_INFO'))
        auth_user=request_get('AUTHENTICATED_USER',None)
        if auth_user is not None:
            T.setUser(auth_user, request_get('AUTHENTICATION_PATH'))

# profiling support

_pfile = None # profiling filename
_plock=allocate_lock() # profiling lock
_pfunc=publish_module_standard
_pstat=None

def install_profiling(filename):
    global _pfile
    _pfile = filename
    
def pm(module_name, stdin, stdout, stderr,
       environ, debug, request, response):
    try:
        r=_pfunc(module_name, stdin=stdin, stdout=stdout,
                 stderr=stderr, environ=environ, debug=debug,
                 request=request, response=response)
    except: r=None
    sys._pr_=r

def publish_module_profiled(module_name, stdin=sys.stdin, stdout=sys.stdout,
                            stderr=sys.stderr, environ=os.environ, debug=0,
                            request=None, response=None):
    import profile, pstats
    global _pstat
    _plock.acquire()
    try:
        if request is not None:
            path_info=request.get('PATH_INFO')
        else: path_info=environ.get('PATH_INFO')
        if path_info[-14:]=='manage_profile':
            return _pfunc(module_name, stdin=stdin, stdout=stdout,
                          stderr=stderr, environ=environ, debug=debug,
                          request=request, response=response)
        pobj=profile.Profile()
        pobj.runcall(pm, module_name, stdin, stdout, stderr,
                     environ, debug, request, response)
        result=sys._pr_
        pobj.create_stats()
        if _pstat is None:
            _pstat=sys._ps_=pstats.Stats(pobj)
        else: _pstat.add(pobj)
    finally:
        _plock.release()

    if result is None:
        try:
            error=sys.exc_info()
            file=open(_pfile, 'w')
            file.write(
            "See the url "
            "http://www.python.org/doc/current/lib/module-profile.html"
            "\n for information on interpreting profiler statistics.\n\n"
                )
            sys.stdout=file
            _pstat.strip_dirs().sort_stats('cumulative').print_stats(250)
            _pstat.strip_dirs().sort_stats('time').print_stats(250)
            file.flush()
            file.close()
        except: pass
        raise error[0], error[1], error[2]
    return result

def publish_module(module_name,
                   stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr,
                   environ=os.environ, debug=0, request=None, response=None):
    """ publish a Python module, with or without profiling enabled """
    if _pfile: # profiling is enabled
        return publish_module_profiled(module_name, stdin, stdout, stderr,
                                       environ, debug, request, response)
    else:
        return publish_module_standard(module_name, stdin, stdout, stderr,
                                       environ, debug, request, response)

