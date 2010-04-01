##############################################################################
#
# Copyright (c) 2005 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################

""" Zope clock server.  Generate a faux HTTP request on a regular basis
by coopting the asyncore API. """

import posixpath
import os
import socket
import time
import StringIO
import asyncore

from ZServer.medusa.http_server import http_request
from ZServer.medusa.default_handler import unquote
from ZServer.PubCore import handle
from ZServer.HTTPResponse import make_response
from ZPublisher.HTTPRequest import HTTPRequest

def timeslice(period, when=None, t=time.time):
    if when is None:
        when =  t()
    return when - (when % period)

class LogHelper:
    def __init__(self, logger):
        self.logger = logger

    def log(self, ip, msg, **kw):
        self.logger.log(ip + ' ' + msg)

class DummyChannel:
    # we need this minimal do-almost-nothing channel class to appease medusa
    addr = ['127.0.0.1']
    closed = 1

    def __init__(self, server):
        self.server = server
        
    def push_with_producer(self):
        pass

    def close_when_done(self):
        pass
    
class ClockServer(asyncore.dispatcher):
    # prototype request environment
    _ENV = dict(REQUEST_METHOD = 'GET',
                SERVER_PORT = 'Clock',
                SERVER_NAME = 'Zope Clock Server',
                SERVER_SOFTWARE = 'Zope',
                SERVER_PROTOCOL = 'HTTP/1.0',
                SCRIPT_NAME = '',
                GATEWAY_INTERFACE='CGI/1.1',
                REMOTE_ADDR = '0')

    # required by ZServer
    SERVER_IDENT = 'Zope Clock' 

    def __init__ (self, method, period=60, user=None, password=None,
                  host=None, logger=None, handler=None):
        self.period = period
        self.method = method

        self.last_slice = timeslice(period)

        h = self.headers = []
        h.append('User-Agent: Zope Clock Server Client')
        h.append('Accept: text/html,text/plain')
        if not host:
            host = socket.gethostname()
        h.append('Host: %s' % host)
        auth = False
        if user and password:
            encoded = ('%s:%s' % (user, password)).encode('base64')
            h.append('Authorization: Basic %s' % encoded)
            auth = True

        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.logger = LogHelper(logger)
        self.log_info('Clock server for "%s" started (user: %s, period: %s)'
                      % (method, auth and user or 'Anonymous', self.period))
        if handler is None:
            # for unit testing
            handler = handle
        self.zhandler = handler

    def get_requests_and_response(self):
        out = StringIO.StringIO()
        s_req = '%s %s HTTP/%s' % ('GET', self.method, '1.0')
        req = http_request(DummyChannel(self), s_req, 'GET', self.method,
                           '1.0', self.headers)
        env = self.get_env(req)
        resp = make_response(req, env)
        zreq = HTTPRequest(out, env, resp)
        return req, zreq, resp

    def get_env(self, req):
        env = self._ENV.copy()
        (path, params, query, fragment) = req.split_uri()
        if params:
            path = path + params # undo medusa bug
        while path and path[0] == '/':
            path = path[1:]
        if '%' in path:
            path = unquote(path)
        if query:
            # ZPublisher doesn't want the leading '?'
            query = query[1:]
        env['PATH_INFO']= '/' + path
        env['PATH_TRANSLATED']= posixpath.normpath(
            posixpath.join(os.getcwd(), env['PATH_INFO']))
        if query:
            env['QUERY_STRING'] = query
        env['channel.creation_time']=time.time()
        for header in req.header:
            key,value = header.split(":",1)
            key = key.upper()
            value = value.strip()
            key = 'HTTP_%s' % ("_".join(key.split( "-")))
            if value:
                env[key]=value
        return env

    def readable(self):
        # generate a request at most once every self.period seconds
        slice = timeslice(self.period)
        if slice != self.last_slice:
            # no need for threadsafety here, as we're only ever in one thread
            self.last_slice = slice
            req, zreq, resp = self.get_requests_and_response()
            self.zhandler('Zope2', zreq, resp)
        return False

    def handle_read(self):
        return True

    def handle_write (self):
        self.log_info('unexpected write event', 'warning')
        return True

    def writable(self):
        return False

    def handle_error (self):      # don't close the socket on error
        (file,fun,line), t, v, tbinfo = asyncore.compact_traceback()
        self.log_info('Problem in Clock (%s:%s %s)' % (t, v, tbinfo),
                      'error')



