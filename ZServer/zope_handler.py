"""
Zope Medusa Handler based on bobo_handler.py

Uses a new threaded architecture.

Requires:

  * Python 1.5 or greater, with threads
  * Medusa 990107 or greater
  * ZPublisher
  
"""


import sys
import regex
import string
import os
import types
from cStringIO import StringIO
import thread

from PubCore import handle

from medusa import counter
from medusa import default_handler
from medusa import producers

split_path = default_handler.split_path
unquote    = default_handler.unquote
get_header = default_handler.get_header

CONTENT_LENGTH = regex.compile('Content-Length: \([0-9]+\)',regex.casefold)


# maps request headers to environment variables
#
header2env={'content-length'    : 'CONTENT_LENGTH',
            'content-type'      : 'CONTENT_TYPE'
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
        if not uri_base:    
            uri_base="/%s" % module
        elif uri_base[-1]=="/": # kill possible trailing /
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
        if request.command in ["post","put"]:
            request.collector=input_collector(self,request)
            request.channel.set_terminator(None)
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
            # cgi_publisher_module doesn't want the leading '?'
            query = query[1:]
        env = {}
        env['REQUEST_METHOD'] = string.upper(request.command)
        env['SERVER_PORT'] = str(request.channel.server.port)
        env['SERVER_NAME'] = request.channel.server.server_name
        env['SERVER_SOFTWARE'] = request['Server']
        env['SCRIPT_NAME'] = self.uri_base
        if query:
            env['QUERY_STRING'] = query
        try:
            path_info=string.split(path,self.uri_base[1:],1)[1]
        except:
            path_info=''
        env['PATH_INFO'] = path_info
        env['GATEWAY_INTERFACE']='CGI/1.1'
        env['REMOTE_ADDR']=request.channel.addr[0]
        #env['REMOTE_HOST']=request.channel.addr[0] #what should this be?
        
        for header in request.header:
            [key,value]=string.split(header,": ",1)
            key=string.lower(key)
            if header2env.has_key(key) and value:
                env[header2env[key]]=value
            else:
                key='HTTP_'+string.upper(string.join(string.split(key,"-"),"_"))
                if value and not env.has_key(key):
                    env[key]=value
        return env

    def continue_request(self,sin,request):
        "continue handling request now that we have the stdin"
        request.data=[]
        outpipe=handle(self.module_name,
            self.get_environment(request),sin,(self.more,(request,)))
        
    def more(self,request,pipe):
        """packages up the current output from the output pipe.
        called repeatedly when there is something in the output pipe"""
        
        # XXX does not stream, probably inefficient.
        
        done=None
        while not done:
            data=pipe.read()
            if data is None:
                done=1
            elif data=="":
                done=1
                self.finish(request)
            else:
                request.data.append(data)
    
    def finish(self,request):
        "finishes up the response"

        # XXX does not stream, probably inefficient to boot
        
        data=string.join(request.data,'')
        if string.find(data,"\n\n"):
            [headers,html]=string.split(data,"\n\n",1)
            headers=string.split(headers,"\n")
            for line in headers:
                [header, header_value]=string.split(line,": ",1)
                if header=="Status":
                    [code,message]=string.split(header_value," ",1)
                    request.reply_code=string.atoi(code)
                else:
                    request[header]=header_value
        request.push(html)
        request.done()

    def status (self):
        return producers.simple_producer("""
            <li>Zope Handler
            <ul>
            <li><b>Published Module:</b> % s
            <li><b>Hits:</b> %d
            </ul>""" %(self.module_name,int(self.hits))
            )


class input_collector:
    "gathers input for put and post requests"
    
    # XXX update to use tempfiles for large content 

    def __init__ (self, handler, request):
        self.handler    = handler
        self.request    = request
        self.data = StringIO()
        # make sure there's a content-length header
        self.cl = get_header (CONTENT_LENGTH, request.header)
        if not self.cl:
            request.error(411)
            return
        else:
            self.cl = string.atoi(self.cl)

    def collect_incoming_data (self, data):
        self.data.write(data)
        if self.data.tell() >= self.cl:
            self.data.seek(0)
            h=self.handler
            r=self.request
            # set the terminator back to the default
            self.request.channel.set_terminator ('\r\n\r\n')
            del self.handler
            del self.request
            h.continue_request(self.data,r)
