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

"""First cut at a Medusa PCGI server.

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

from medusa import asynchat, asyncore, logger
from medusa.counter import counter
from medusa.producers import NotReady, hooked_producer

from PubCore import handle

from cStringIO import StringIO
from tempfile import TemporaryFile
import socket
import string
import os

class PCGIChannel(asynchat.async_chat):    
    """Processes a PCGI request by collecting the env and stdin and
    then passing them to ZPublisher. The result is wrapped in a
    producer and sent back."""
    
    def __init__(self,server,sock,addr):
        self.server = server
        self.addr = addr
        asynchat.async_chat.__init__ (self, sock)
        self.data=StringIO()
        self.set_terminator(10)
        self.size=None
        self.env={}
        self.done=None
        
    def found_terminator(self):
        if self.size is None:
            # read the next size header
            # and prepare to read env or stdin
            self.data.seek(0)
            self.size=string.atoi(self.data.read())
            self.set_terminator(self.size)
            if self.size==0:
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
                self.env['PATH_INFO'] = string.join(path[len(script):],'/')
            
            self.data=StringIO()
            # now read the next size header
            self.set_terminator(10)
        else:
            # we're done, we've got both env and stdin
            self.set_terminator('\r\n')
            self.data.seek(0)
            self.send_response()
        
    def send_response(self):
        # create an output pipe by passing request to ZPublisher,
        # and requesting a callback of self.log with the module
        # name and PATH_INFO as an argument.
        self.done=1        
        outpipe=handle(self.server.module, self.env, self.data)
        self.push_with_producer(
            hooked_producer(PCGIProducer(outpipe), self.log_request)
            )
        self.close_when_done()        
        
    def collect_incoming_data(self, data):
        self.data.write(data)

    def readable(self):
        if not self.done:
            return 1
     
    def log_request(self, bytes):
        if self.env.has_key('PATH_INFO'):
            path='%s/%s' % (self.server.module, self.env['PATH_INFO'])
        else:
            path='%s/' % self.server.module
        self.server.logger.log (
            self.addr[0],
            '%d - - [time goes here] "%s" %d' % (
                self.addr[1], path, bytes
                )
            )

    def writable(self):
        return len(self.ac_out_buffer) or self.producer_fifo.ready() \
            or (not self.connected)


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
        if pcgi_file is None:
            self.module=module    
            self.port=port
            self.pid_file=pid_file
            self.socket_file=socket_file
        else:
            self.read_info(pcgi_file)
        
        # write pid file
        try:
           f = open(self.pid_file, 'wb')
           f.write(str(os.getpid()))
           f.close()
        except IOError:
            self.log("Error, cannot write PID file.")
        
        # setup sockets
        if self.port:
            self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
            self.set_reuse_addr()
            self.bind((self.ip, self.port))
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
        self.listen(5)

    def read_info(self,info_file):
        "read configuration information from a PCGI info file"
        lines=open(info_file).readlines()
        directives={}
        for line in lines:
            if not len(line) or line[0]=='#':
                continue
            k,v=string.split(line,'=',1)
            directives[string.strip(k)]=string.strip(v)
        self.pid_file=directives['PCGI_PID_FILE']
        self.socket_file=directives.get('PCGI_SOCKET_FILE',None)
        self.port=directives.get('PCGI_PORT',None)
        if directives.has_key('PCGI_MODULE'):
            self.module=directives['PCGI_MODULE']
        else:
            path=directives['PCGI_MODULE_PATH']
            path,module=os.path.split(path)
            module,ext=os.path.splitext(module)
            self.module=module
        
    def handle_accept (self):
        self.count.increment()
        try:
            conn, addr = self.accept()
        except socket.error:
            sys.stderr.write('warning: server accept() threw an exception\n')
            return
        self.channel_class(self, conn, addr)
    
    def writable (self):
        return 0
    
        
class PCGIProducer:
    """Producer wrapper over output pipe
    
    output format is in PCGI format: 10 digits indicating len of
    STDOUT followed by STDOUT.
    
    Note: no STDERR is returned.
    Note: streaming is not supported, since PCGI requires the length
    of the STDOUT be known before it is sent.
    """
    
    def __init__(self,pipe):
        self.pipe=pipe
        self.buffer=StringIO()
        self.buffer.write('0'*10) #this will hold length header
        self.chunk_size=512
        self.done=None
    
    def ready(self):
        if self.done:
            return 1
        data=self.pipe.read()
        if data is not None:
            self.buffer.write(data)
        if data=='':
            self.buffer.write('0'*10) #write stderr header
            self.buffer.seek(0)
            size=len(self.buffer.getvalue())-20
            self.buffer.write('%010d' % size)
            self.buffer.seek(0)
            self.done=1
            return 1    
        
    def more(self):
        if not self.done:
            raise NotReady
        else:
            return self.buffer.read(self.chunk_size)

