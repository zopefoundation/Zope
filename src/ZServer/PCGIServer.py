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
Medusa PCGI server.

This server functions as the PCGI publisher--it accepts the request
from the PCGI wrapper CGI program, services the request, and sends
back the response.

It should work with both inet and unix domain sockets.

Why would you want to use it? Using PCGI to connect to ZServer from
another webserver is similar to using the web server as a proxy,
with the difference, that the web server gets to control the
environment and headers completely.

Note that ZServer can operate multiple PCGI servers.
"""

from medusa import logger
import asynchat, asyncore
from medusa.counter import counter
from medusa.http_server import compute_timezone_for_log
from asyncore import compact_traceback

import ZServer
from ZServer import requestCloseOnExec

from PubCore import handle
from PubCore.ZEvent import Wakeup
from ZPublisher.HTTPResponse import HTTPResponse
from ZPublisher.HTTPRequest import HTTPRequest
from Producers import ShutdownProducer, LoggingProducer, CallbackProducer
import DebugLogger

from cStringIO import StringIO
from tempfile import TemporaryFile
import socket, string, os, sys, time

tz_for_log=compute_timezone_for_log()

class ParseError(Exception):
    pass

class PCGIChannel(asynchat.async_chat):
    """Processes a PCGI request by collecting the env and stdin and
    then passing them to ZPublisher. The result is wrapped in a
    producer and sent back."""

    closed=0

    def __init__(self,server,sock,addr):
        self.server = server
        self.addr = addr
        asynchat.async_chat.__init__ (self, sock)
        requestCloseOnExec(sock)
        self.env={}
        self.data=StringIO()
        self.set_terminator(10)
        self.size=None
        self.done=None

    def found_terminator(self):
        if self.size is None:
            # read the next size header
            # and prepare to read env or stdin
            self.data.seek(0)
            self.size=string.atoi(self.data.read())
            self.set_terminator(self.size)
            if self.size==0:

                DebugLogger.log('I', id(self), 0)

                self.set_terminator('\r\n')
                self.data=StringIO()
                self.send_response()
            elif self.size > 1048576:
                self.data=TemporaryFile('w+b')
            else:
                self.data=StringIO()
        elif not self.env:
            # read env
            self.size=None
            self.data.seek(0)
            buff=self.data.read()
            for line in string.split(buff,'\000'):
                try:
                    k,v = string.split(line,'=',1)
                    self.env[k] = v
                except:
                    pass
            # Hack around broken IIS PATH_INFO
            # maybe, this should go in ZPublisher...
            if self.env.has_key('SERVER_SOFTWARE') and \
                    string.find(self.env['SERVER_SOFTWARE'],
                    'Microsoft-IIS') != -1:
                script = filter(None,string.split(
                        string.strip(self.env['SCRIPT_NAME']),'/'))
                path = filter(None,string.split(
                        string.strip(self.env['PATH_INFO']),'/'))
                self.env['PATH_INFO'] = '/' + string.join(path[len(script):],'/')
            self.data=StringIO()

            DebugLogger.log('B', id(self),
                '%s %s' % (self.env['REQUEST_METHOD'],
                           self.env.get('PATH_INFO' ,'/')))

            # now read the next size header
            self.set_terminator(10)
        else:

            DebugLogger.log('I', id(self), self.terminator)

            # we're done, we've got both env and stdin
            self.set_terminator('\r\n')
            self.data.seek(0)
            self.send_response()

    def send_response(self):
        # create an output pipe by passing request to ZPublisher,
        # and requesting a callback of self.log with the module
        # name and PATH_INFO as an argument.
        self.done=1
        response=PCGIResponse(stdout=PCGIPipe(self), stderr=StringIO())
        request=HTTPRequest(self.data, self.env, response)
        handle(self.server.module, request, response)

    def collect_incoming_data(self, data):
        self.data.write(data)

    def readable(self):
        if not self.done:
            return 1

    def log_request(self, bytes):
        if self.env.has_key('HTTP_USER_AGENT'):
            user_agent=self.env['HTTP_USER_AGENT']
        else:
            user_agent=''
        if self.env.has_key('HTTP_REFERER'):
            referer=self.env['HTTP_REFERER']
        else:
            referer=''

        if self.env.has_key('PATH_INFO'):
            path=self.env['PATH_INFO']
        else:
            path='%s/' % self.server.module
        if self.env.has_key('REQUEST_METHOD'):
            method=self.env['REQUEST_METHOD']
        else:
            method="GET"
        addr=self.addr
        if addr and isinstance(addr, tuple):
            self.server.logger.log (
                addr[0],
                '%d - - [%s] "%s %s" %d %d "%s" "%s"' % (
                    addr[1],
                    time.strftime (
                    '%d/%b/%Y:%H:%M:%S ',
                    time.localtime(time.time())
                    ) + tz_for_log,
                    method, path, self.reply_code, bytes,
                    referer, user_agent
                    )
                )
        else:
            self.server.logger.log (
                '127.0.0.1',
                ' - - [%s] "%s %s" %d %d "%s" "%s"' % (
                    time.strftime (
                    '%d/%b/%Y:%H:%M:%S ',
                    time.gmtime(time.time())
                    ) + tz_for_log,
                    method, path, self.reply_code, bytes,
                    referer, user_agent
                    )
                )

    def push(self, producer, send=1):
        # this is thread-safe when send is false
        # note, that strings are not wrapped in
        # producers by default
        self.producer_fifo.push(producer)
        if send: self.initiate_send()

    def __repr__(self):
        return "<PCGIChannel at %x>" % id(self)

    def close(self):
        self.closed=1
        while self.producer_fifo:
            p=self.producer_fifo.first()
            if p is not None and not isinstance(p, basestring):
                p.more() # free up resources held by producer
            self.producer_fifo.pop()
        asyncore.dispatcher.close(self)


class PCGIServer(asyncore.dispatcher):
    """Accepts PCGI requests and hands them off to the PCGIChannel for
    handling.

    PCGIServer can be configured with either a PCGI info file or by
    directly specifying the module, pid_file, and either port (for
    inet sockets) or socket_file (for unix domain sockets.)

    For inet sockets, the ip argument specifies the address from which
    the server will accept connections, '' indicates all addresses. If
    you only want to accept connections from the localhost, set ip to
    '127.0.0.1'."""

    channel_class=PCGIChannel

    def __init__ (self,
            module='Main',
            ip='127.0.0.1',
            port=None,
            socket_file=None,
            pid_file=None,
            pcgi_file=None,
            resolver=None,
            logger_object=None):

        self.ip = ip
        asyncore.dispatcher.__init__(self)
        self.count=counter()
        if not logger_object:
            logger_object = logger.file_logger (sys.stdout)
        if resolver:
            self.logger = logger.resolving_logger (resolver, logger_object)
        else:
            self.logger = logger.unresolving_logger (logger_object)

        # get configuration
        self.module=module
        self.port=port
        self.pid_file=pid_file
        self.socket_file=socket_file
        if pcgi_file is not None:
            self.read_info(pcgi_file)

        # write pid file
        try:
            f = open(self.pid_file, 'w')
            f.write(str(os.getpid()))
            f.close()
        except IOError:
            self.log_info("Cannot write PID file.", 'error')

        # setup sockets
        if self.port:
            self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
            self.set_reuse_addr()
            self.bind((self.ip, self.port))
            self.log_info(
                'PCGI Server started at %s\n'
                '\tInet socket port: %s' % (time.ctime(time.time()), self.port)
                )
        else:
            try:
                os.unlink(self.socket_file)
            except os.error:
                pass
            self.create_socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self.set_reuse_addr()
            self.bind(self.socket_file)
            try:
                os.chmod(self.socket_file,0777)
            except os.error:
                pass
            self.log_info(
                'PCGI Server started at %s\n'
                '\tUnix socket: %s' % (time.ctime(time.time()), self.socket_file)
                )
        self.listen(256)

    def create_socket(self, family, type):
        asyncore.dispatcher.create_socket(self, family, type)
        requestCloseOnExec(self.socket)

    def read_info(self,info_file):
        "read configuration information from a PCGI info file"
        lines=open(info_file).readlines()
        directives={}
        try:
            for line in lines:
                line=string.strip(line)
                if not len(line) or line[0]=='#':
                    continue
                k,v=string.split(line,'=',1)
                directives[string.strip(k)]=string.strip(v)
        except:
            raise ParseError, 'Error parsing PCGI info file'

        self.pid_file=directives.get('PCGI_PID_FILE',None)
        self.socket_file=directives.get('PCGI_SOCKET_FILE',None)
        if directives.has_key('PCGI_PORT'):
            self.port=string.atoi(directives['PCGI_PORT'])
        if directives.has_key('PCGI_MODULE'):
            self.module=directives['PCGI_MODULE']
        elif directives.has_key('PCGI_MODULE_PATH'):
            path=directives['PCGI_MODULE_PATH']
            path,module=os.path.split(path)
            module,ext=os.path.splitext(module)
            self.module=module

    def handle_accept (self):
        self.count.increment()
        try:
            conn, addr = self.accept()
        except socket.error:
            self.log_info('Server accept() threw an exception', 'warning')
            return
        self.channel_class(self, conn, addr)

    def readable(self):
        from ZServer import CONNECTION_LIMIT
        return len(asyncore.socket_map) < CONNECTION_LIMIT

    def writable (self):
        return 0

    def listen(self, num):
        # override asyncore limits for nt's listen queue size
        self.accepting = 1
        return self.socket.listen (num)


class PCGIResponse(HTTPResponse):

    def write(self, data):
        if type(data) != type(''):
            raise TypeError('Value must be a string')

        if not self._wrote:
            self.stdout.write(str(self))
            self._wrote=1
        self.stdout.write(data)

    def _finish(self):
        self.stdout.finish(self)
        self.stdout.close()

        self.stdout=None
        self._request=None


class PCGIPipe:
    """
    Formats a HTTP response in PCGI format

        10 digits indicating len of STDOUT
        STDOUT
        10 digits indicating len of STDERR
        STDERR

    Note that this implementation never sends STDERR
    """
    def __init__(self, channel):
        self._channel=channel
        self._data=StringIO()
        self._shutdown=0

    def write(self,text):
        self._data.write(text)

    def close(self):
        if not self._channel.closed:
            data=self._data.getvalue()
            l=len(data)
            DebugLogger.log('A', id(self._channel),
                '%s %s' % (self._channel.reply_code, l))
            self._channel.push('%010d%s%010d' % (l, data, 0), 0)
            self._channel.push(LoggingProducer(self._channel, l, 'log_request'), 0)
            self._channel.push(CallbackProducer(
                lambda t=('E', id(self._channel)): apply(DebugLogger.log,t)), 0)

            if self._shutdown:
                try: r=self._shutdown[0]
                except: r=0
                ZServer.exit_code=r
                self._channel.push(ShutdownProducer(), 0)
                Wakeup(lambda: asyncore.close_all())
            else:
                self._channel.push(None, 0)
                Wakeup()
        self._data=None
        self._channel=None

    def finish(self, response):
        if response._shutdownRequested():
            self._shutdown = 1
        self._channel.reply_code=response.status
