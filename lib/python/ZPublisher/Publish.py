##############################################################################
#
# Copyright (c) 2001 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
__doc__="""Python Object Publisher -- Publish Python objects on web servers

$Id: Publish.py,v 1.161 2003/03/21 21:15:02 fdrake Exp $"""
__version__='$Revision: 1.161 $'[11:-2]

import sys, os
from Response import Response
from Request import Request
from maybe_lock import allocate_lock
from mapply import mapply

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
        cancel=''
        if request_get('SUBMIT','').strip().lower()=='cancel':
            cancel=request_get('CANCEL_ACTION','')
            if cancel: raise 'Redirect', cancel

        after_list[0]=bobo_after
        if debug_mode: response.debug_mode=debug_mode
        if realm and not request.get('REMOTE_USER',None):
            response.realm=realm

        if bobo_before is not None:
            bobo_before()

        # Get a nice clean path list:
        path=request_get('PATH_INFO').strip()

        request['PARENTS']=parents=[object]

        if transactions_manager: transactions_manager.begin()

        object=request.traverse(path, validated_hook=validated_hook)

        if transactions_manager:
            transactions_manager.recordMetaData(object, request)

        result=mapply(object, request.args, request,
                      call_object,1,
                      missing_name,
                      dont_publish_class,
                      request, bind=1)

        if result is not response: response.setBody(result)

        if transactions_manager: transactions_manager.commit()

        return response
    except:
        if transactions_manager: transactions_manager.abort()

        # DM: provide nicer error message for FTP
        sm = None
        if response is not None:
            sm = getattr(response, "setMessage", None)

        if sm is not None:
            from ZServer.medusa.asyncore import compact_traceback
            cl,val= sys.exc_info()[:2]
            sm('%s: %s %s' % (getattr(cl,'__name__',cl), val, debug_mode and compact_traceback()[-1] or ''))
         

        if err_hook is not None:
            if parents: parents=parents[0]
            try:
                return err_hook(parents, request,
                                sys.exc_info()[0],
                                sys.exc_info()[1],
                                sys.exc_info()[2],
                                )
            except Retry:
                # We need to try again....
                if not request.supports_retry():
                    return err_hook(parents, request,
                                    sys.exc_info()[0],
                                    sys.exc_info()[1],
                                    sys.exc_info()[2],
                                    )
                newrequest=request.retry()
                request.close()  # Free resources held by the request.
                try:
                    return publish(newrequest, module_name, after_list, debug)
                finally:
                    newrequest.close()

        else: raise


def publish_module(module_name,
                   stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr,
                   environ=os.environ, debug=0, request=None, response=None):
    must_die=0
    status=200
    after_list=[None]
    try:
        try:
            if response is None:
                response=Response(stdout=stdout, stderr=stderr)
            else:
                stdout=response.stdout

            if request is None:
                request=Request(stdin, environ, response)

            response = publish(request, module_name, after_list, debug=debug)
        except SystemExit, v:
            must_die=sys.exc_info()
            request.response.exception(must_die)
        except ImportError, v:
            if type(v) is type(()) and len(v)==3: must_die=v
            elif hasattr(sys, 'exc_info'): must_die=sys.exc_info()
            else: must_die = SystemExit, v, sys.exc_info()[2]
            request.response.exception(1, v)
        except:
            request.response.exception()
            status=response.getStatus()

        if response:
            outputBody=getattr(response, 'outputBody', None)
            if outputBody is not None:
                outputBody()
            else:
                response=str(response)
                if response: stdout.write(response)

        # The module defined a post-access function, call it
        if after_list[0] is not None: after_list[0]()

    finally:
        if request is not None: request.close()

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
    try:
        try:
            module=__import__(module_name, globals(), globals(), ('__doc__',))

            # Let the app specify a realm
            if hasattr(module,'__bobo_realm__'):
                realm=module.__bobo_realm__
            elif os.environ.has_key('Z_REALM'):
                realm=os.environ['Z_REALM']
            elif os.environ.has_key('BOBO_REALM'):
                realm=os.environ['BOBO_REALM']
            else:
                realm=module_name

            # Check for debug mode
            debug_mode=None
            if hasattr(module,'__bobo_debug_mode__'):
                debug_mode=not not module.__bobo_debug_mode__
            else:

                z1 = os.environ.get('Z_DEBUG_MODE','')
                z2 = os.environ.get('BOBO_DEBUG_MODE','')

                if z1.lower() in ('yes','y') or z1.isdigit():
                    debug_mode = 1
                elif z2.lower() in ('yes','y') or z2.isdigit():
                    debug_mode = 1


            if hasattr(module,'__bobo_before__'):
                bobo_before=module.__bobo_before__
            else: bobo_before=None

            if hasattr(module,'__bobo_after__'): bobo_after=module.__bobo_after__
            else: bobo_after=None

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
                try: get_transaction()
                except: pass
                else:
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
    def begin(self): get_transaction().begin()
    def commit(self): get_transaction().commit()
    def abort(self): get_transaction().abort()
    def recordMetaData(self, object, request):
        # Is this code needed?
        request_get = request.get
        T=get_transaction()
        T.note(request_get('PATH_INFO'))
        auth_user=request_get('AUTHENTICATED_USER',None)
        if auth_user is not None:
            T.setUser(auth_user, request_get('AUTHENTICATION_PATH'))


# ZPublisher profiler support
# ---------------------------

if os.environ.get('PROFILE_PUBLISHER', None):

    import profile, pstats

    _pfile=os.environ['PROFILE_PUBLISHER']
    _plock=allocate_lock()
    _pfunc=publish_module
    _pstat=None

    def pm(module_name, stdin, stdout, stderr,
           environ, debug, request, response):
        try:
            r=_pfunc(module_name, stdin=stdin, stdout=stdout,
                     stderr=stderr, environ=environ, debug=debug,
                     request=request, response=response)
        except: r=None
        sys._pr_=r

    def publish_module(module_name, stdin=sys.stdin, stdout=sys.stdout,
                       stderr=sys.stderr, environ=os.environ, debug=0,
                       request=None, response=None):
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
