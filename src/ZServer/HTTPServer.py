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

"""
Medusa HTTP server for Zope

changes from Medusa's http_server

    Request Threads -- Requests are processed by threads from a thread
    pool.

    Output Handling -- Output is pushed directly into the producer
    fifo by the request-handling thread. The HTTP server does not do
    any post-processing such as chunking.

    Pipelineable -- This is needed for protocols such as HTTP/1.1 in
    which mutiple requests come in on the same channel, before
    responses are sent back. When requests are pipelined, the client
    doesn't wait for the response before sending another request. The
    server must ensure that responses are sent back in the same order
    as requests are received.

"""
import sys
import re
import os
import posixpath
import thread
import time
import socket
from cStringIO import StringIO

from PubCore import handle
from HTTPResponse import make_response
from ZPublisher.HTTPRequest import HTTPRequest
from App.config import getConfiguration

import asyncore
import asynchat

from medusa.http_server import http_server, get_header
from medusa.http_server import fifo, http_channel, VERSION_STRING
from medusa import counter, producers
from medusa.test import  max_sockets
from medusa.default_handler import unquote
from asyncore import compact_traceback, dispatcher

from ZServer import ZOPE_VERSION, ZSERVER_VERSION
from ZServer import requestCloseOnExec
import DebugLogger
from medusa import logger


CONTENT_LENGTH  = re.compile('Content-Length: ([0-9]+)',re.I)
CONNECTION      = re.compile('Connection: (.*)', re.I)
USER_AGENT      = re.compile('User-Agent: (.*)', re.I)

is_proxying_match = re.compile(r'[^ ]* [^ \\]*:').match


# maps request some headers to environment variables.
# (those that don't start with 'HTTP_')
header2env={'content-length'    : 'CONTENT_LENGTH',
            'content-type'      : 'CONTENT_TYPE',
            'connection'        : 'CONNECTION_TYPE',
            }


class zhttp_collector:
    def __init__(self, handler, request, size):
        from ZServer import LARGE_FILE_THRESHOLD
        self.handler = handler
        self.request = request
        if size > LARGE_FILE_THRESHOLD:
            # write large upload data to a file
            from tempfile import TemporaryFile
            self.data = TemporaryFile('w+b')
        else:
            self.data = StringIO()
        request.channel.set_terminator(size)
        request.collector=self

    # put and post collection methods
    #
    def collect_incoming_data (self, data):
        self.data.write(data)

    def found_terminator(self):
        # reset collector
        self.request.channel.set_terminator('\r\n\r\n')
        self.request.collector=None
        # finish request
        self.data.seek(0)
        r=self.request
        d=self.data
        del self.request
        del self.data
        self.handler.continue_request(d,r)

class zhttp_handler:
    "A medusa style handler for zhttp_server"

    _force_connection_close = 0

    def __init__ (self, module, uri_base=None, env=None):
        """Creates a zope_handler

        module -- string, the name of the module to publish
        uri_base -- string, the base uri of the published module
                    defaults to '/<module name>' if not given.
        env -- dictionary, environment variables to be overridden.
                    Replaces standard variables with supplied ones.
        """

        self.module_name=module
        self.env_override=env or {}
        self.hits = counter.counter()
        # if uri_base is unspecified, assume it
        # starts with the published module name
        #
        if uri_base is None:
            uri_base='/%s' % module
        elif uri_base == '':
            uri_base='/'
        else:
            if uri_base[0] != '/':
                uri_base='/'+uri_base
            if uri_base[-1] == '/':
                uri_base=uri_base[:-1]
        self.uri_base=uri_base
        uri_regex='%s.*' % self.uri_base
        self.uri_regex = re.compile(uri_regex)

    def match(self, request):
        uri = request.uri
        if self.uri_regex.match(uri):
            return 1
        else:
            return 0

    def handle_request(self,request):
        self.hits.increment()

        DebugLogger.log('B', id(request), '%s %s' % (request.command.upper(), request.uri))

        size=get_header(CONTENT_LENGTH, request.header)
        if size and size != '0':
            size=int(size)
            zhttp_collector(self, request, size)
        else:
            sin=StringIO()
            self.continue_request(sin,request)

    def get_environment(self, request,
                        # These are strictly performance hackery...
                        h2ehas=header2env.has_key,
                        h2eget=header2env.get,
                        workdir=os.getcwd(),
                        ospath=os.path,
                        ):

        (path, params, query, fragment) = request.split_uri()

        if params: path = path + params # undo medusa bug!

        while path and path[0] == '/':
            path = path[1:]
        if '%' in path:
            path = unquote(path)
        if query:
            # ZPublisher doesn't want the leading '?'
            query = query[1:]

        server=request.channel.server
        env = {}
        env['REQUEST_METHOD']=request.command.upper()
        env['SERVER_PORT']=str(server.port)
        env['SERVER_NAME']=server.request_server_name
        env['SERVER_SOFTWARE']=server.SERVER_IDENT
        env['SERVER_PROTOCOL']="HTTP/"+request.version
        env['channel.creation_time']=request.channel.creation_time
        if self.uri_base=='/':
            env['SCRIPT_NAME']=''
            env['PATH_INFO']='/' + path
        else:
            env['SCRIPT_NAME'] = self.uri_base
            try:
                path_info=path.split(self.uri_base[1:],1)[1]
            except:
                path_info=''
            env['PATH_INFO']=path_info
        env['PATH_TRANSLATED']=ospath.normpath(ospath.join(
                workdir, env['PATH_INFO']))
        if query:
            env['QUERY_STRING'] = query
        env['GATEWAY_INTERFACE']='CGI/1.1'
        env['REMOTE_ADDR']=request.channel.addr[0]


        # This is a really bad hack to support WebDAV
        # clients accessing documents through GET
        # on the HTTP port. We check if your WebDAV magic
        # machinery is enabled and if the client is recognized
        # as WebDAV client. If yes, we fake the environment
        # to pretend the ZPublisher to have a WebDAV request.
        # This sucks like hell but it works pretty fine ;-)

        if env['REQUEST_METHOD']=='GET' and self._wdav_client_reg:
            self._munge_webdav_source_port(request, env)


        # If we're using a resolving logger, try to get the
        # remote host from the resolver's cache.
        if hasattr(server.logger, 'resolver'):
            dns_cache=server.logger.resolver.cache
            if dns_cache.has_key(env['REMOTE_ADDR']):
                remote_host=dns_cache[env['REMOTE_ADDR']][2]
                if remote_host is not None:
                    env['REMOTE_HOST']=remote_host

        env_has=env.has_key
        for header in request.header:
            key,value=header.split(":",1)
            key=key.lower()
            value=value.strip()
            if h2ehas(key) and value:
                env[h2eget(key)]=value
            else:
                key='HTTP_%s' % ("_".join(key.split( "-"))).upper()
                if value and not env_has(key):
                    env[key]=value
        env.update(self.env_override)
        return env

    _wdav_client_reg = None

    def _munge_webdav_source_port(self, request, env):
        agent = get_header(USER_AGENT, request.header)
        if self._wdav_client_reg(agent):
            env['WEBDAV_SOURCE_PORT'] = 1
            path_info = env['PATH_INFO']
            path_info = posixpath.join(path_info, 'manage_DAVget')
            path_info = posixpath.normpath(path_info)
            env['PATH_INFO'] = path_info

    def set_webdav_source_clients(self, regex):
        self._wdav_client_reg = re.compile(regex).search

    def continue_request(self, sin, request):
        "continue handling request now that we have the stdin"

        s=get_header(CONTENT_LENGTH, request.header)
        if s:
            s=int(s)
        else:
            s=0
        DebugLogger.log('I', id(request), s)

        env=self.get_environment(request)
        zresponse=make_response(request,env)
        if self._force_connection_close:
            zresponse._http_connection = 'close'
        zrequest=HTTPRequest(sin, env, zresponse)
        request.channel.current_request=None
        request.channel.queue.append((self.module_name, zrequest, zresponse))
        request.channel.work()

    def status(self):
        return producers.simple_producer("""
            <li>Zope Handler
            <ul>
            <li><b>Published Module:</b> %s
            <li><b>Hits:</b> %s
            </ul>""" %(self.module_name, self.hits)
            )

from HTTPResponse import ChannelPipe

class zwsgi_handler(zhttp_handler):
    
    def continue_request(self, sin, request):
        "continue handling request now that we have the stdin"

        s=get_header(CONTENT_LENGTH, request.header)
        if s:
            s=int(s)
        else:
            s=0
        DebugLogger.log('I', id(request), s)

        env=self.get_environment(request)
        version = request.version
        if version=='1.0' and is_proxying_match(request.request):
            # a request that was made as if this zope was an http 1.0 proxy.
            # that means we have to use some slightly different http
            # headers to manage persistent connections.
            connection_re = proxying_connection_re
        else:
            # a normal http request
            connection_re = CONNECTION
        
        env['http_connection'] = get_header(connection_re,
                                            request.header).lower()
        env['server_version']=request.channel.server.SERVER_IDENT

        env['wsgi.output'] = ChannelPipe(request)
        env['wsgi.input'] = sin
        env['wsgi.errors']       = sys.stderr
        env['wsgi.version']      = (1,0)
        env['wsgi.multithread']  = True
        env['wsgi.multiprocess'] = True
        env['wsgi.run_once']     = True
        env['wsgi.url_scheme']   = env['SERVER_PROTOCOL'].split('/')[0]

        request.channel.current_request=None
        request.channel.queue.append(('Zope2WSGI', env, 
                                      env['wsgi.output'].start_response))
        request.channel.work()


class zhttp_channel(http_channel):
    "http channel"

    closed = 0
    no_more_requests = 0
    zombie_timeout=100*60 # 100 minutes

    def __init__(self, server, conn, addr):
        http_channel.__init__(self, server, conn, addr)
        if isinstance(self.producer_fifo, (fifo, asynchat.fifo)):
            self.producer_fifo_push = self.producer_fifo.push
            self.producer_fifo_first = self.producer_fifo.first
            self.producer_fifo_pop = self.producer_fifo.pop
        else:
            self.producer_fifo_push = self.producer_fifo.append
            def first():
                return self.producer_fifo[0]
            self.producer_fifo_first = first
            def pop():
                del self.producer_fifo[0]
            self.producer_fifo_pop = pop
        requestCloseOnExec(conn)
        self.queue = []
        self.working=0
        self.max_header_len = getConfiguration().http_header_max_length

    def push(self, producer, send=1):
        # this is thread-safe when send is false
        # note, that strings are not wrapped in
        # producers by default
        if self.closed:
            return
        self.producer_fifo_push(producer)
        if send: self.initiate_send()

    push_with_producer=push

    def clean_shutdown_control(self,phase,time_in_this_phase):
        if phase==3:
            # This is the shutdown phase where we are trying to finish processing
            # outstanding requests, and not accept any more
            self.no_more_requests = 1
            if self.working or self.writable():
                # We are busy working on an old request. Try to stall shutdown
                return 1
            else:
                # We are no longer busy. Close ourself and allow shutdown to proceed
                self.close()
                return 0

    def work(self):
        "try to handle a request"
        if not self.working:
            if self.queue and not self.no_more_requests:
                self.working=1
                try: module_name, request, response=self.queue.pop(0)
                except: return
                handle(module_name, request, response)

    def close(self):
        self.closed=1
        while self.queue:
            self.queue.pop()
        if self.current_request is not None:
            self.current_request.collector = None # break circ refs
            self.current_request.channel = None # break circ refs
            self.current_request=None
        while self.producer_fifo:
            p=self.producer_fifo_first()
            if p is not None and not isinstance(p, basestring):
                p.more() # free up resources held by producer
            self.producer_fifo_pop()
        dispatcher.close(self)

    def done(self):
        "Called when a publishing request is finished"
        self.working=0
        self.work()

    def kill_zombies(self):
        now = int (time.time())
        for channel in asyncore.socket_map.values():
            if channel.__class__ == self.__class__:
                if (now - channel.creation_time) > channel.zombie_timeout:
                    channel.close()

    def collect_incoming_data (self, data):
        # Override medusa http_channel implementation to prevent DOS attacks
        # that send never-ending HTTP headers.
        if self.current_request:
                # we are receiving data (probably POST data) for a request
            self.current_request.collect_incoming_data (data)
        else:
                # we are receiving header (request) data
            self.in_buffer = self.in_buffer + data
            inbuf_len = len(self.in_buffer) 
            if inbuf_len > self.max_header_len:
                # Don't bother with a proper response header,
                # we are probably under attack and that would just consume 
                # precious resources.
                # Instead, just bail out and leave the nasty client hanging.
                # Hanging's too good for them!
                # Unfortunate side effect: the attack gets logged to the
                # event log, but not the access log.
                raise ValueError('HTTP headers invalid (too long) (got: %d bytes, allowed %d bytes' % (inbuf_len, self.max_header_len))

class zhttp_server(http_server):
    "http server"

    SERVER_IDENT = 'Zope/%s ZServer/%s' % (ZOPE_VERSION, ZSERVER_VERSION)
    server_protocol = 'HTTP'
    channel_class = zhttp_channel
    shutup=0

    def __init__ (self, ip, port, resolver=None, logger_object=None,
                  fast_listen=True):
        self.shutup=1
        self.fast_listen = fast_listen
        http_server.__init__(self, ip, port, resolver, logger_object)
        self.request_server_name = self.server_name
        if self.request_server_name == '0.0.0.0':
            # Workaround to set a more descriptive server name
            # for use in the Request SERVER_NAME variable
            try:
                self.request_server_name = socket.getfqdn()
            except socket.error:
                pass
        self.shutup=0
        self.log_info('%s server started at %s\n'
                      '\tHostname: %s\n\tPort: %d' % (
            self.server_protocol,
            time.ctime(time.time()),
            self.server_name,
            self.server_port
            ))

    def clean_shutdown_control(self,phase,time_in_this_phase):
        if phase==2:
            self.log_info('closing %s to new connections' % self.server_protocol)
            self.close()

    def log_info(self, message, type='info'):
        if self.shutup: return
        dispatcher.log_info(self, message, type)

    def create_socket(self, family, type):
        dispatcher.create_socket(self, family, type)
        requestCloseOnExec(self.socket)

    def readable(self):
        from ZServer import CONNECTION_LIMIT
        return self.accepting and \
               len(asyncore.socket_map) < CONNECTION_LIMIT

    def listen(self, num):
        # override asyncore limits for nt's listen queue size

        if self.fast_listen:
            self.accepting = 1
            return self.socket.listen (num)
        else:
            return 0


class zwebdav_server(zhttp_server):
    server_protocol = 'WebDAV'
