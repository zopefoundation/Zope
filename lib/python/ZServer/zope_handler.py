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
CONNECTION = regex.compile ('Connection: \(.*\)', regex.casefold)

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
            cl=get_header(CONTENT_LENGTH, request.header)
            self.data = StringIO() # XXX maybe use tempfile, if cl is large
            self.request = request
            request.channel.set_terminator(string.atoi(cl))
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

        outgoing_producer = crazy_producer(request,outpipe)

        # apply a few final transformations to the output
        request.channel.push_with_producer (
            # globbing gives us large packets
            producers.globbing_producer (
                # hooking lets us log the number of bytes sent
                producers.hooked_producer (
                    outgoing_producer,
                    request.log
                    )
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
        

class pipe_producer:
    def __init__(self,pipe):
        self.pipe=pipe
        
    def more(self):
        #if not self.ready():
        #    import traceback
        #    traceback.print_stack()
        data=self.pipe.read()
        if data is None: return ''
        return data

    def ready(self):
       return self.pipe.ready()


class crazy_producer:
    """This weird producer patches together
    medusa's idea of http headers with ZPublisher's
    """
    def __init__(self,request,pipe):
        self.request=request
        self.pipe=pipe
        self.done=None
        self.buffer=''
        
    def more(self):
        if self.buffer:
            b=self.buffer
            self.buffer=''
            return b
        data=self.pipe.read()
        if data is None: return ''
        return data
           
    def ready(self):
        if self.done:
            return self.pipe.ready()
        elif self.pipe.ready():
            self.buffer=self.buffer+self.pipe.read()
            if string.find(self.buffer,"\n\n"):
                [headers,html]=string.split(self.buffer,"\n\n",1)
                headers=string.split(headers,"\n")
                for line in headers:
                    [header, header_value]=string.split(line,": ",1)
                    if header=="Status":
                        [code,message]=string.split(header_value," ",1)
                        self.request.reply_code=string.atoi(code)
                else:
                    self.request[header]=header_value
                self.buffer=self.request.build_reply_header()+html
                del self.request
                self.done=1

