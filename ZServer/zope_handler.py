##############################################################################
# 
# Zope Public License (ZPL) Version 0.9.6
# ---------------------------------------
# 
# Copyright (c) Digital Creations.  All rights reserved.
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
# 3. Any use, including use of the Zope software to operate a website,
#    must either comply with the terms described below under
#    "Attribution" or alternatively secure a separate license from
#    Digital Creations.  Digital Creations will not unreasonably
#    deny such a separate license in the event that the request
#    explains in detail a valid reason for withholding attribution.
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
# Attribution
# 
#   Individuals or organizations using this software as a web
#   site ("the web site") must provide attribution by placing
#   the accompanying "button" on the website's main entry
#   point.  By default, the button links to a "credits page"
#   on the Digital Creations' web site. The "credits page" may
#   be copied to "the web site" in order to add other credits,
#   or keep users "on site". In that case, the "button" link
#   may be updated to point to the "on site" "credits page".
#   In cases where this placement of attribution is not
#   feasible, a separate arrangment must be concluded with
#   Digital Creations.  Those using the software for purposes
#   other than web sites must provide a corresponding
#   attribution in locations that include a copyright using a
#   manner best suited to the application environment.  Where
#   attribution is not possible, or is considered to be
#   onerous for some other reason, a request should be made to
#   Digital Creations to waive this requirement in writing.
#   As stated above, for valid requests, Digital Creations
#   will not unreasonably deny such requests.
# 
# This software consists of contributions made by Digital Creations and
# many individuals on behalf of Digital Creations.  Specific
# attributions are listed in the accompanying credits file.
# 
##############################################################################

"""
Zope Medusa Handler

Uses a new threaded architecture.
Works with http_server.py
  
"""


import sys
import regex
import string
import os
import types
from cStringIO import StringIO
import thread

from PubCore import handle

from medusa import counter, producers, asyncore
from medusa.default_handler import split_path, unquote, get_header
from medusa.producers import NotReady

CONTENT_LENGTH = regex.compile('Content-Length: \([0-9]+\)',regex.casefold)
CONNECTION = regex.compile ('Connection: \(.*\)', regex.casefold)

# maps request some headers to environment variables.
# (those that don't start with 'HTTP_')
header2env={'content-length'    : 'CONTENT_LENGTH',
            'content-type'      : 'CONTENT_TYPE',
            'connection'        : 'CONNECTION_TYPE',
            }


class zope_handler:
    "publishes a module with ZPublisher"
    
    # XXX add code to allow env overriding 
    
    def __init__ (self, module, uri_base=None):
        """Creates a zope_handler
        
        module -- string, the name of the module to publish
        uri_base -- string, the base uri of the published module
                    defaults to '/<module name>' if not given. 
        """
        
        self.module_name=module
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

    def match (self, request):
        uri = request.uri
        if self.uri_regex.match(uri) == len(uri):
            return 1
        else:
            return 0

    def handle_request(self,request):
        self.hits.increment()
        size=get_header(CONTENT_LENGTH, request.header)
        if size:
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
        env['REQUEST_METHOD'] = string.upper(request.command)
        env['SERVER_PORT'] = str(request.channel.server.port)
        env['SERVER_NAME'] = request.channel.server.server_name
        env['SERVER_SOFTWARE'] = request['Server']
        env['SERVER_PROTOCOL']='HTTP/1.0' # should this be 1.1?
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
        return env

    def continue_request(self,sin,request):
        "continue handling request now that we have the stdin"
        
        outpipe=handle(self.module_name,self.get_environment(request),sin)
        
        # now comes the hairy stuff. adapted from http_server
        #
        connection = string.lower(get_header(CONNECTION,request.header))

        close_it = 0
        wrap_in_chunking = 0

        if request.version == '1.0':
            if connection == 'keep-alive':
                if not request.has_key ('Content-Length'):
                    close_it = 1
                else:
                    request['Connection'] = 'Keep-Alive'
            else:
                close_it = 1
        elif request.version == '1.1':
            if connection == 'close':
                close_it = 1
            elif not request.has_key ('Content-Length'):
                if request.has_key ('Transfer-Encoding'):
                    if not request['Transfer-Encoding'] == 'chunked':
                        close_it = 1
                elif request.use_chunked:
                    request['Transfer-Encoding'] = 'chunked'
                    wrap_in_chunking = 1
                else:
                    close_it = 1
        
        if close_it:
            request['Connection'] = 'close'

        outgoing_producer = header_scanning_producer(request,outpipe)

        # apply a few final transformations to the output
        request.channel.push_with_producer (
            # hooking lets us log the number of bytes sent
            producers.hooked_producer (
                outgoing_producer,
                request.log
                )
            )

        request.channel.current_request = None

        if close_it:
            request.channel.close_when_done()


    def status (self):
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
        

class header_scanning_producer:
    """This weird producer patches together
    medusa's idea of http headers with ZPublisher's
    """
    def __init__(self,request,pipe):
        self.request=request
        self.pipe=pipe
        self.done=None
        self.buffer=''
        self.exit=None
        
    def more(self):
        if self.buffer:
            b=self.buffer
            self.buffer=''
            return b
        data=self.pipe.read()
        if data is None:
            raise NotReady()
        if data=='' and self.exit:
            asyncore.close_all()
        return data
           
    def ready(self):
        if self.done:
            return self.pipe.ready()
        elif self.pipe.ready():
            self.buffer=self.buffer+self.pipe.read()
            if string.find(self.buffer,"\n\n") != -1:
                [headers,html]=string.split(self.buffer,"\n\n",1)
                headers=string.split(headers,"\n")
                for line in headers:
                    [header, header_value]=string.split(line,": ",1)
                    if header=="Status":
                        [code,message]=string.split(header_value," ",1)
                        self.request.reply_code=string.atoi(code)
                    elif header=="Bobo-Exception-Type" and \
                            header_value=="exceptions.SystemExit":
                        self.exit=1
                    else:
                        self.request[header]=header_value
                self.buffer=self.request.build_reply_header()+html
                del self.request
                self.done=1

