##############################################################################
# 
# Zope Public License (ZPL) Version 1.0
# -------------------------------------
# 
# Copyright (c) Digital Creations.  All rights reserved.
# 
# This license has been certified as Open Source(tm).
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
# 
# 1. Redistributions in source code must retain the above copyright
#    notice, this list of conditions, and the following disclaimer.
# 
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions, and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
# 
# 3. Digital Creations requests that attribution be given to Zope
#    in any manner possible. Zope includes a "Powered by Zope"
#    button that is installed by default. While it is not a license
#    violation to remove this button, it is requested that the
#    attribution remain. A significant investment has been put
#    into Zope, and this effort will continue if the Zope community
#    continues to grow. This is one way to assure that growth.
# 
# 4. All advertising materials and documentation mentioning
#    features derived from or use of this software must display
#    the following acknowledgement:
# 
#      "This product includes software developed by Digital Creations
#      for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
#    In the event that the product being advertised includes an
#    intact Zope distribution (with copyright and license included)
#    then this clause is waived.
# 
# 5. Names associated with Zope or Digital Creations must not be used to
#    endorse or promote products derived from this software without
#    prior written permission from Digital Creations.
# 
# 6. Modified redistributions of any form whatsoever must retain
#    the following acknowledgment:
# 
#      "This product includes software developed by Digital Creations
#      for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
#    Intact (re-)distributions of any official Zope release do not
#    require an external acknowledgement.
# 
# 7. Modifications are encouraged but must be packaged separately as
#    patches to official Zope releases.  Distributions that do not
#    clearly separate the patches from the original work must be clearly
#    labeled as unofficial distributions.  Modifications which do not
#    carry the name Zope may be packaged in any form, as long as they
#    conform to all of the clauses above.
# 
# 
# Disclaimer
# 
#   THIS SOFTWARE IS PROVIDED BY DIGITAL CREATIONS ``AS IS'' AND ANY
#   EXPRESSED OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
#   IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
#   PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL DIGITAL CREATIONS OR ITS
#   CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
#   SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
#   LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF
#   USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#   ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
#   OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT
#   OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
#   SUCH DAMAGE.
# 
# 
# This software consists of contributions made by Digital Creations and
# many individuals on behalf of Digital Creations.  Specific
# attributions are listed in the accompanying credits file.
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
import regex
import string
import os
import types
import thread
from cStringIO import StringIO

from PubCore import handle
from HTTPResponse import make_response
from ZPublisher.HTTPRequest import HTTPRequest

from medusa.http_server import http_server, http_channel
from medusa import counter, producers, asyncore
from medusa.default_handler import split_path, unquote, get_header

CONTENT_LENGTH = regex.compile('Content-Length: \([0-9]+\)',regex.casefold)
CONNECTION = regex.compile ('Connection: \(.*\)', regex.casefold)

ZSERVER_VERSION='1.1b1'
try:
    import Main
    ZOPE_VERSION=Main.app.Control_Panel.version_txt()
    del Main
except:
    ZOPE_VERSION='experimental'
    
# maps request some headers to environment variables.
# (those that don't start with 'HTTP_')
header2env={'content-length'    : 'CONTENT_LENGTH',
            'content-type'      : 'CONTENT_TYPE',
            'connection'        : 'CONNECTION_TYPE',
            }


class zhttp_handler:
    "A medusa style handler for zhttp_server"
    
    # XXX add code to allow env overriding 
    
    
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
        self.uri_regex = regex.compile(uri_regex)

    def match(self, request):
        uri = request.uri
        if self.uri_regex.match(uri) == len(uri):
            return 1
        else:
            return 0

    def handle_request(self,request):
        self.hits.increment()
        size=get_header(CONTENT_LENGTH, request.header)
        if size and size != '0':
            size=string.atoi(size)
            if size > 1048576:
                # write large upload data to a file
                from tempfile import TemporaryFile
                self.data = TemporaryFile('w+b')
            else:
                self.data = StringIO()
            self.request = request
            request.channel.set_terminator(size)
            request.collector=self
        else:
            sin=StringIO()
            self.continue_request(sin,request)

    def get_environment(self,request):
    
        # XXX add env overriding
        
        [path, params, query, fragment] = split_path(request.uri)
        while path and path[0] == '/':
            path = path[1:]
        if '%' in path:
            path = unquote(path)
        if query:
            # ZPublisher doesn't want the leading '?'
            query = query[1:]
        env = {}
        env['REQUEST_METHOD']=string.upper(request.command)
        env['SERVER_PORT']=str(request.channel.server.port)
        env['SERVER_NAME']=request.channel.server.server_name
        env['SERVER_SOFTWARE']=request.channel.server.SERVER_IDENT
        env['SERVER_PROTOCOL']=request.version
        if self.uri_base=='/':
            env['SCRIPT_NAME']=''
            env['PATH_INFO']=path
        else:
            env['SCRIPT_NAME'] = self.uri_base
            try:
                path_info=string.split(path,self.uri_base[1:],1)[1]
            except:
                path_info=''
            env['PATH_INFO']=path_info
        env['PATH_TRANSLATED']=os.path.normpath(os.path.join(
                os.getcwd(),env['PATH_INFO']))
        if query:
            env['QUERY_STRING'] = query
        env['GATEWAY_INTERFACE']='CGI/1.1'
        env['REMOTE_ADDR']=request.channel.addr[0]
        # If we're using a resolving logger, try to get the
        # remote host from the resolver's cache. 
        try:
            dns_cache=request.channel.server.logger.resolver.cache
            if dns_cache.has_key(env['REMOTE_ADDR']):
                env['REMOTE_HOST']=dns_cache[env['REMOTE_ADDR']][2]
        except AttributeError:
            pass
        
        for header in request.header:
            [key,value]=string.split(header,": ",1)
            key=string.lower(key)
            if header2env.has_key(key) and value:
                env[header2env[key]]=value
            else:
                key='HTTP_' + string.upper(
                    string.join(string.split(key, "-"), "_"))
                if value and not env.has_key(key):
                    env[key]=value        
        for key, value in self.env_override.items():
            env[key]=value
        return env

    def continue_request(self, sin, request):
        "continue handling request now that we have the stdin"
        env=self.get_environment(request)
        zresponse=make_response(request,env)
        zrequest=HTTPRequest(sin, env, zresponse)
        request.channel.current_request=None
        request.channel.queue.append(self.module_name, zrequest, zresponse)
        request.channel.work()

    def status(self):
        return producers.simple_producer("""
            <li>Zope Handler
            <ul>
            <li><b>Published Module:</b> % s
            <li><b>Hits:</b> %d
            </ul>""" %(self.module_name,int(self.hits))
            )

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
        self.continue_request(d,r)


class zhttp_channel(http_channel):
    "http channel"
    
    def __init__(self, server, conn, addr):
        http_channel.__init__(self, server, conn, addr)
        self.queue=[]
        self.working=0
    
    def push(self, producer, send=1):
        # this is thread-safe when send is false
        # note, that strings are not wrapped in 
        # producers by default
        self.producer_fifo.push(producer)
        if send: self.initiate_send()
        
    push_with_producer=push

    def work(self):
        "try to handle a request"
        if not self.working:
            if self.queue:
                self.working=1
                module_name, request, response=self.queue[0]
                self.queue=self.queue[1:]
                handle(module_name, request, response)
        
    def done(self):
        "Called when a pushing request is finished"
        self.working=0
        self.work()


class zhttp_server(http_server):    
    "http server"
    
    SERVER_IDENT='Zope/%s ZServer/%s' % (ZOPE_VERSION,ZSERVER_VERSION)
    
    channel_class = zhttp_channel
