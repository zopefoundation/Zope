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
__doc__="""Python Object Publisher -- Publish Python objects on web servers

$Id: Publish.py 67721 2006-04-28 14:57:35Z regebro $"""

import sys, os, re, time
import transaction
from Response import Response
from Request import Request
from maybe_lock import allocate_lock
from mapply import mapply
from zExceptions import Redirect
from cStringIO import StringIO
from ZServer.medusa.http_date import build_http_date

class WSGIResponse(Response):
    """A response object for WSGI

    This Response object knows nothing about ZServer, but tries to be
    compatible with the ZServerHTTPResponse. 
    
    Most significantly, streaming is not (yet) supported."""

    _streaming = 0
    
    def __str__(self,
                html_search=re.compile('<html>',re.I).search,
                ):
        if self._wrote:
            if self._chunking:
                return '0\r\n\r\n'
            else:
                return ''

        headers=self.headers
        body=self.body

        # set 204 (no content) status if 200 and response is empty
        # and not streaming
        if not headers.has_key('content-type') and \
                not headers.has_key('content-length') and \
                not self._streaming and \
                self.status == 200:
            self.setStatus('nocontent')

        # add content length if not streaming
        if not headers.has_key('content-length') and \
                not self._streaming:
            self.setHeader('content-length',len(body))


        content_length= headers.get('content-length', None)
        if content_length>0 :
            self.setHeader('content-length', content_length)

        headersl=[]
        append=headersl.append

        status=headers.get('status', '200 OK')

        # status header must come first.
        append("HTTP/%s %s" % (self._http_version or '1.0' , status))
        if headers.has_key('status'):
            del headers['status']

        # add zserver headers
        append('Server: %s' % self._server_version)
        append('Date: %s' % build_http_date(time.time()))

        if self._http_version=='1.0':
            if self._http_connection=='keep-alive' and \
                    self.headers.has_key('content-length'):
                self.setHeader('Connection','Keep-Alive')
            else:
                self.setHeader('Connection','close')

        # Close the connection if we have been asked to.
        # Use chunking if streaming output.
        if self._http_version=='1.1':
            if self._http_connection=='close':
                self.setHeader('Connection','close')
            elif not self.headers.has_key('content-length'):
                if self.http_chunk and self._streaming:
                    self.setHeader('Transfer-Encoding','chunked')
                    self._chunking=1
                else:
                    self.setHeader('Connection','close')

        for key, val in headers.items():
            if key.lower()==key:
                # only change non-literal header names
                key="%s%s" % (key[:1].upper(), key[1:])
                start=0
                l=key.find('-',start)
                while l >= start:
                    key="%s-%s%s" % (key[:l],key[l+1:l+2].upper(),key[l+2:])
                    start=l+1
                    l=key.find('-',start)
            append("%s: %s" % (key, val))
        if self.cookies:
            headersl=headersl+self._cookie_list()
        headersl[len(headersl):]=[self.accumulated_headers, body]
        return "\r\n".join(headersl)

    
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

def publish_module_standard(environ, start_response):

    must_die=0
    status=200
    after_list=[None]
    stdout = StringIO()
    stderr = StringIO()
    response = WSGIResponse(stdout=stdout, stderr=stderr)
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
        status = response.getHeader('status')
        # ZServerHTTPResponse calculates all headers and things when you
        # call it's __str__, so we need to get it, and then munge out
        # the headers from it. It's a bit backwards, and we might optimize
        # this by not using ZServerHTTPResponse at all, and making the 
        # HTTPResponses more WSGI friendly. But this works.
        result = str(response)
        headers, body = result.split('\r\n\r\n',1)
        headers = [tuple(n.split(': ',1)) for n in headers.split('\r\n')[1:]]
        start_response(status, headers)
        # If somebody used response.write, that data will be in the
        # stdout StringIO, so we put that before the body.
        # XXX This still needs verification that it really works.
        result=(stdout.getvalue(), body)
    request.close()
    stdout.close()

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
        
    # Return the result body iterable.
    return result


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
    
def pm(environ, start_response):
    try:
        r=_pfunc(environ, start_response)
    except: r=None
    sys._pr_=r

def publish_module_profiled(environ, start_response):
    import profile, pstats
    global _pstat
    _plock.acquire()
    try:
        if request is not None:
            path_info=request.get('PATH_INFO')
        else: path_info=environ.get('PATH_INFO')
        if path_info[-14:]=='manage_profile':
            return _pfunc(environ, start_response)
        pobj=profile.Profile()
        pobj.runcall(pm, menviron, start_response)
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

def publish_module(environ, start_response):
    """ publish a Python module, with or without profiling enabled """
    if _pfile: # profiling is enabled
        return publish_module_profiled(environ, start_response)
    else:
        return publish_module_standard(environ, start_response)

