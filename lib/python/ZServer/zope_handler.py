"""
Zope Medusa Handler

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
from medusa import producers
from medusa.default_handler import split_path, unquote, get_header

HEADER_LINE = regex.compile ('\([A-Za-z0-9-]+\): \(.*\)')
CONTENT_LENGTH = regex.compile('Content-Length: \([0-9]+\)',regex.casefold)
CONNECTION = regex.compile ('Connection: \(.*\)', regex.casefold)

# maps request some headers to environment variables.
# (those that don't start with 'HTTP_')
# 
header2env={'content-length'    : 'CONTENT_LENGTH',
            'content-type'      : 'CONTENT_TYPE',
            'connection'        : 'CONNECTION_TYPE',
            }


class zope_handler:
    "Publishes a module with ZPublisher"
    
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
            size=get_header(CONTENT_LENGTH, request.header)
            if size > 1048576:
                # write large upload data to a file
                from tempfile import TemporaryFile
                self.data = TemporaryFile('w+b')
            else:
                self.data = StringIO()
            self.request = request
            request.channel.set_terminator(string.atoi(size))
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

        # XXX 'REMOTE_HOST' is missing. Should it be
        #     retrieved from the resolver somehow?

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
        producer=header_scanning_producer(request)
        pusher=file_pusher(producer)
        outpipe=handle(self.module_name,
            self.get_environment(request), sin, (pusher.push, ()))
    
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
    def collect_incoming_data(self, data):
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
        

# The pusher is used to push data out of the pipe into the 
# header_scanning_producer

class file_pusher:
    "pushs data from one file into another file"

    def __init__(self,out):
        self.out=out

    def push(self,file):
        "push data from file to out. if file is exhausted, close out."
        data=file.read()
        if data != '':
            self.out.write(data)
        else:
            self.out.close()


# The header_scanning_producer accepts data from
# the output pipe (via the file pusher). Then it
# munges the data and pushes it into the channel.

class header_scanning_producer:
    """This producer accepts data with the write method.
    It scans the data, munges HTTP headers and pushes
    it into a channel. When done it logs information."""

    close_it=1
    exit=None

    def __init__ (self, request):
        self.buffer = ''
        self.request = request
        self.channel = request.channel
        self.got_header = 0
        self.bytes_out = counter.counter()

    def write (self, data):
        if self.got_header:
            self.push(data)
        else:
            self.buffer = self.buffer + data         
            i=string.find(self.buffer,'\n\n')
            if i != -1:
                self.got_header = 1
                headers=string.split(self.buffer[:i],'\n')
                self.push(self.build_header(headers))
                self.push(self.buffer[i+2:])
                self.buffer = ''

    def build_header (self, lines):
        status = '200 OK'
        headers=[]
        header_dict={}
        for line in lines:
            [header, header_value]=string.split(line,": ",1)
            header_dict[header]=header_value
            if header=="Status":
                status=header_value
            elif line:
                headers.append(line)

  
        self.request.reply_code=string.atoi(status[:3]) # for logging
        
        headers.insert (0, 'HTTP/1.0 %s' % status)
        headers.append ('Server: ' + self.request['Server'])
        headers.append ('Date: ' + self.request['Date'])
        
        # XXX add stuff to determine chunking and 
        #     'Transfer-Encoding'
            
        # XXX is this keep alive logic right?
        connection = string.lower(get_header
                    (CONNECTION, self.request.header))
        if connection == 'keep-alive' and \
                    header_dict.has_key ('Content-Length'):
            self.close_it=None
            headers.append('Connection: Keep-Alive')
        else:
            headers.append ('Connection: close')
            self.close_it=1
        
        if header_dict.has_key('Bobo-Exception-Type') and \
            header_dict['Bobo-Exception-Type']=='exceptions.SystemExit':
                self.exit=1
                
        return string.join (headers, '\r\n')+'\r\n\r\n'

    def push(self, data):
        self.bytes_out.increment(len(data))
        self.channel.push(data)

    def close (self):
        self.request.log(int(self.bytes_out.as_long()))
        self.request.channel.current_request = None
        if self.exit:
            self.channel.producer_fifo.push(exit_producer())
        elif self.close_it:
            self.channel.close_when_done()
        
        # is this necessary?
        del self.request
        del self.channel


class exit_producer:
    
    # XXX this is not currently sufficient. 
    #     needs to be enhanced to actually work.
    
    def more(self):
        raise SystemExit

