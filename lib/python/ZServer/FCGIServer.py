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
ZServer/Medusa FastCGI server, by Robin Dunn.

Accepts connections from a FastCGI enabled webserver, receives request
info using the FastCGi protocol, and then hands the request off to
ZPublisher for processing.  The response is then handed back to the
webserver to send down to the browser.

See http://www.fastcgi.com/fcgi-devkit-2.1/doc/fcgi-spec.html for the
protocol specificaition.
"""

__version__ = "1.0"

#----------------------------------------------------------------------

from medusa import asynchat, asyncore, logger
from medusa.counter import counter
from medusa.http_server import compute_timezone_for_log

from ZServer import CONNECTION_LIMIT

from PubCore import handle
from PubCore.ZEvent import Wakeup
from ZPublisher.HTTPResponse import HTTPResponse
from ZPublisher.HTTPRequest import HTTPRequest
from Producers import ShutdownProducer, LoggingProducer, file_part_producer, file_close_producer

from cStringIO import StringIO
from tempfile import TemporaryFile
import socket, string, os, sys, time
from types import StringType

tz_for_log = compute_timezone_for_log()

#----------------------------------------------------------------------
# Set various FastCGI constants

# Maximum number of requests that can be handled.  Apache mod_fastcgi
# never asks for these values, so we actually will handle as many
# connections/requests as they attempt upto the limits of ZServer.
# These values are suitable defaults for any web server that does ask.
FCGI_MAX_CONNS = 10
FCGI_MAX_REQS  = 50

# Supported version of the FastCGI protocol
FCGI_VERSION_1 = 1

# Boolean: can this application multiplex connections?
FCGI_MPXS_CONNS=0

# Record types
FCGI_BEGIN_REQUEST     = 1
FCGI_ABORT_REQUEST     = 2
FCGI_END_REQUEST       = 3
FCGI_PARAMS            = 4
FCGI_STDIN             = 5
FCGI_STDOUT            = 6
FCGI_STDERR            = 7
FCGI_DATA              = 8
FCGI_GET_VALUES        = 9
FCGI_GET_VALUES_RESULT = 10
FCGI_UNKNOWN_TYPE      = 11
FCGI_MAXTYPE           = FCGI_UNKNOWN_TYPE

# Types of management records
FCGI_ManagementTypes = [ FCGI_GET_VALUES ]

FCGI_NULL_REQUEST_ID=0

# Masks for flags component of FCGI_BEGIN_REQUEST
FCGI_KEEP_CONN = 1

# Values for role component of FCGI_BEGIN_REQUEST
FCGI_RESPONDER  = 1
FCGI_AUTHORIZER = 2
FCGI_FILTER     = 3

# Values for protocolStatus component of FCGI_END_REQUEST
FCGI_REQUEST_COMPLETE = 0               # Request completed nicely
FCGI_CANT_MPX_CONN    = 1               # This app can't multiplex
FCGI_OVERLOADED       = 2               # New request rejected; too busy
FCGI_UNKNOWN_ROLE     = 3               # Role value not known


#----------------------------------------------------------------------

class FCGIRecord:
    """
    This class represents the various record structures used in the
    FastCGI protocol.  It knows how to read and build itself bits
    at a time as they are read from the FCGIChannel.  There are really
    several different record types but in this case subclassing for
    each type is probably overkill.

    See the FastCGI spec for structure and other details for all these
    record types.
    """
    def __init__(self, header=None):
        if header:
            # extract the record header values.
            vals = map(ord, header)
            self.version = vals[0]
            self.recType = vals[1]
            self.reqId = (vals[2] << 8) + vals[3]
            self.contentLength = (vals[4] << 8) + vals[5]
            self.paddingLength = vals[6]
        else:
            self.version = FCGI_VERSION_1
            self.recType = FCGI_UNKNOWN_TYPE
            self.reqId   = FCGI_NULL_REQUEST_ID
        self.content = ""


    def needContent(self):
        return (self.contentLength and not self.content)

    def needPadding(self):
        return self.paddingLength != 0

    def needMore(self):
        if self.needContent():
            return self.contentLength
        else:
            return self.paddingLength

    def gotPadding(self):
        self.paddingLength = 0


    def parseContent(self, data):
        c = self.content = data
        if self.recType == FCGI_BEGIN_REQUEST:
            self.role  = (ord(c[0]) << 8) + ord(c[1])
            self.flags = ord(c[2])

        elif self.recType == FCGI_UNKNOWN_TYPE:
            self.unknownType = ord(c[0])

        elif self.recType == FCGI_GET_VALUES or self.recType == FCGI_PARAMS:
            self.values = {}
            pos = 0
            while pos < len(c):
                name, value, pos = self.readPair(c, pos)
                self.values[name] = value

        elif self.recType == FCGI_END_REQUEST:
            b = map(ord, c[0:4])
            self.appStatus = (b[0] << 24) + (b[1] << 16) + (b[2] << 8) + b[3]
            self.protocolStatus = ord(c[4])



    def readPair(self, st, pos):
        """
        Read the next name-value pair from st at pos.
        """
        nameLen = ord(st[pos])
        pos = pos + 1
        if nameLen & 0x80:  # is the high bit set? if so, size is 4 bytes, not 1.
            b = map(ord, st[pos:pos+3])
            pos = pos + 3
            nameLen = ((nameLen & 0x7F) << 24) + (b[0] << 16) + (b[1] << 8) + b[2]

        valueLen = ord(st[pos])
        pos = pos + 1
        if valueLen & 0x80:  # same thing here...
            b = map(ord, st[pos:pos+3])
            pos = pos + 3
            valueLen = ((valueLen & 0x7F) << 24) + (b[0] << 16) + (b[1] << 8) + b[2]

        # pull out the name and value and return with the updated position
        return ( st[pos : pos+nameLen],
                 st[pos + nameLen : pos + nameLen + valueLen],
                 pos + nameLen + valueLen )


    def writePair(name, value):
        """
        Opposite of readPair
        """
        l = len(name)
        if l < 0x80:
            st = chr(l)
        else:
            st = chr(0x80 | (l >> 24) & 0xFF) + chr((l >> 16) & 0xFF) + \
                 chr((l >> 8) & 0xFF) + chr(l & 0xFF)

        l = len(value)
        if l < 0x80:
            st = st + chr(l)
        else:
            st = st + chr(0x80 | (l >> 24) & 0xFF) + chr((l >> 16) & 0xFF) + \
                 chr((l >> 8) & 0xFF) + chr(l & 0xFF)

        return st + name + value



    def getRecordAsString(self):
        """
        Format the record to be sent back to the web server.
        """
        content = self.content
        if self.recType == FCGI_BEGIN_REQUEST:
            content = chr(self.role>>8) + chr(self.role & 0xFF) + \
                      chr(self.flags) + 5*'\000'

        elif self.recType == FCGI_UNKNOWN_TYPE:
            content = chr(self.unknownType) + 7*'\000'

        elif self.recType == FCGI_GET_VALUES or self.recType == FCGI_PARAMS:
            content = ""
            for i in self.values.keys():
                content = content + self.writePair(i, self.values[i])

        elif self.recType == FCGI_END_REQUEST:
            v = self.appStatus
            content = chr((v >> 24) & 0xFF) + chr((v >> 16) & 0xFF) + \
                      chr((v >> 8) & 0xFF) + chr(v & 0xFF)
            content = content + chr(self.protocolStatus) + 3*'\000'

        cLen = len(content)
        eLen = (cLen + 7) & (0xFFFF - 7)    # align to an 8-byte boundary
        padLen = eLen - cLen

        hdr = [ self.version,
                self.recType,
                self.reqId >> 8,
                self.reqId & 0xFF,
                cLen >> 8,
                cLen & 0xFF,
                padLen,
                0]
        hdr = string.join(map(chr, hdr), '')
        return hdr + content + padLen * '\000'


#----------------------------------------------------------------------

class FCGIChannel(asynchat.async_chat):
    """
    Process a FastCGI connection.  This class implements most of the
    Application Server side of the protocol defined in
    http://www.fastcgi.com/fcgi-devkit-2.1/doc/fcgi-spec.html (which is
    the FastCGI Specification 1.0 from Open Market, Inc.) in a manner
    that is compatible with the asyncore medusa engine of ZServer.

    The main ommission from the spec is support for multiplexing
    multiple requests on a single connection, but since none of the
    web servers support it (that I know of,) and since ZServer can
    easily multiplex multiple connections in the same process, it's no
    great loss.
    """
    closed=0
    using_temp_stdin=None
    
    def __init__(self, server, sock, addr):
        self.server = server
        self.addr = addr
        asynchat.async_chat.__init__(self, sock)
        self.setInitialState()
        self.remainingRecs = 1  # We have to read at least one
        self.env = {}
        self.stdin = StringIO()
        self.filterData = StringIO()  # not currently used, but maybe someday
        self.requestId = 0


    def setInitialState(self):
        self.data = StringIO()
        self.curRec = None
        self.set_terminator(8) # FastCGI record header size.


    def readable(self):
        return self.remainingRecs != 0


    def collect_incoming_data(self, data):
        self.data.write(data)


    def found_terminator(self):
        # Are we starting a new record?  If so, data is the header.
        if not self.curRec:
            self.curRec = FCGIRecord(self.data.getvalue())
            if self.curRec.needMore():
                self.set_terminator(self.curRec.needMore())
                self.data = StringIO()
                return

        rec = self.curRec

        # If waiting for record content, give it to the record.
        if rec.needContent():
            rec.parseContent(self.data.getvalue())
            if rec.needMore():
                self.set_terminator(rec.needMore())
                self.data = StringIO()
                return

        if rec.needPadding():
            rec.gotPadding()


        # If we get this far without returning, we've got the whole
        # record.  Figure out what to do with it.

        if rec.recType in FCGI_ManagementTypes:
            # Apache mod_fastcgi doesn't send these, but others may
            self.handleManagementTypes(rec)

        elif rec.reqId == 0:
            # It's a management record of unknown type.
            # Complain about it...
            r2 = FCGIRecord()
            r2.recType = FCGI_UNKNOWN_TYPE
            r2.unknownType = rec.recType
            self.push(r2.getRecordAsString(), 0)


        # Since we don't actually have to do anything to ignore the
        # following conditions, they have been commented out and have
        # been left in the code for documentation purposes.

        # Ignore requests that aren't active
        # elif rec.reqId != self.requestId and rec.recType != FCGI_BEGIN_REQUEST:
        #     pass
        #
        # If we're already doing a request, ignore further BEGIN_REQUESTs
        # elif rec.recType == FCGI_BEGIN_REQUEST and self.requestId != 0:
        #     pass


        # Begin a new request
        elif rec.recType == FCGI_BEGIN_REQUEST and self.requestId == 0:
            self.requestId = rec.reqId
            if rec.role == FCGI_AUTHORIZER:   self.remainingRecs = 1
            elif rec.role == FCGI_RESPONDER:  self.remainingRecs = 2
            elif rec.role == FCGI_FILTER:     self.remainingRecs = 3


        # Read some name-value pairs (the CGI environment)
        elif rec.recType == FCGI_PARAMS:
            if rec.contentLength == 0:  # end of the stream
                self.remainingRecs = self.remainingRecs - 1
            else:
                self.env.update(rec.values)

        # read some stdin data
        elif rec.recType == FCGI_STDIN:
            if rec.contentLength == 0:  # end of the stream
                self.remainingRecs = self.remainingRecs - 1
            else:
                # see if stdin is getting too big, and 
                # replace it with a tempfile if necessary
                if len(rec.content) + self.stdin.tell() > 1048576 and \
                        not self.using_temp_stdin:
                    t=TemporaryFile()
                    t.write(self.stdin.getvalue())
                    self.stdin=t
                    self.using_temp_stdin=1
                self.stdin.write(rec.content)

        # read some filter data
        elif rec.recType == FCGI_DATA:
            if rec.contentLength == 0:  # end of the stream
                self.remainingRecs = self.remainingRecs - 1
            else:
                self.filterData.write(rec.content)


        # We've processed the record.  Now what do we do?
        if self.remainingRecs:
            # prepare to get the next record
            self.setInitialState()

        else:
            # We've got them all.  Let ZPublisher do its thang.

            # But first, fixup the auth header if using newest mod_fastcgi.
            if self.env.has_key('Authorization'):
                self.env['HTTP_AUTHORIZATION'] = self.env['Authorization']

            self.stdin.seek(0)
            self.send_response()



    def send_response(self):
        """
        Create output pipes, request, and response objects.  Give them
        to ZPublisher for processing.
        """
        response = FCGIResponse(stdout = FCGIPipe(self, FCGI_STDOUT),
                                stderr = StringIO())
        response.setChannel(self)
        request  = HTTPRequest(self.stdin, self.env, response)
        handle(self.server.module, request, response)


    def log_request(self, bytes):
        # XXX need to add reply code logging
        if self.env.has_key('PATH_INFO'):
            path='%s%s' % (self.server.module, self.env['PATH_INFO'])
        else:
            path='%s/' % self.server.module
        if self.env.has_key('REQUEST_METHOD'):
            method=self.env['REQUEST_METHOD']
        else:
            method="GET"
        if self.addr:
            self.server.logger.log (
                self.addr[0],
                '%d - - [%s] "%s %s" %d' % (
                    self.addr[1],
                    time.strftime (
                    '%d/%b/%Y:%H:%M:%S ',
                    time.gmtime(time.time())
                    ) + tz_for_log,
                    method, path, bytes
                    )
                )
        else:
            self.server.logger.log (
                '127.0.0.1',
                '- - [%s] "%s %s" %d' % (
                    time.strftime (
                    '%d/%b/%Y:%H:%M:%S ',
                    time.gmtime(time.time())
                    ) + tz_for_log,
                    method, path, bytes
                    )
                )



    def handleManagementTypes(self, rec):
        """
        The web server has asked us what features we support...
        """
        if rec.recType == FCGI_GET_VALUES:
            rec.recType = FCGI_GET_VALUES_RESULT
            vars={'FCGI_MAX_CONNS' : FCGI_MAX_CONNS,
                  'FCGI_MAX_REQS'  : FCGI_MAX_REQS,
                  'FCGI_MPXS_CONNS': FCGI_MPXS_CONNS}
            rec.values = vars
            self.push(rec.getRecordAsString(), 0)


    def sendDataRecord(self, data, recType):
        rec = FCGIRecord()
        rec.recType = recType
        rec.reqId   = self.requestId
        # Can't send more than 64K minus header size.  8K seems about right.
        if type(data)==type(''):
            # send some string data
            while data:
                chunk = data[:8192]
                data = data[8192:]
                rec.content = chunk
                self.push(rec.getRecordAsString(), 0)
        else:
            # send a producer
            p, cLen=data
            eLen = (cLen + 7) & (0xFFFF - 7)    # align to an 8-byte boundary
            padLen = eLen - cLen

            hdr = [ rec.version,
                    rec.recType,
                    rec.reqId >> 8,
                    rec.reqId & 0xFF,
                    cLen >> 8,
                    cLen & 0xFF,
                    padLen,
                    0]
            hdr = string.join(map(chr, hdr), '')
            self.push(hdr, 0)
            self.push(p, 0)
            self.push(padLen * '\000', 0)            

    def sendStreamTerminator(self, recType):
        rec = FCGIRecord()
        rec.recType = recType
        rec.reqId   = self.requestId
        rec.content = ""
        self.push(rec.getRecordAsString(), 0)

    def sendEndRecord(self, appStatus=0):
        rec = FCGIRecord()
        rec.recType        = FCGI_END_REQUEST
        rec.reqId          = self.requestId
        rec.protocolStatus = FCGI_REQUEST_COMPLETE
        rec.appStatus      = appStatus
        self.push(rec.getRecordAsString(), 0)
        self.requestId     = 0

    def push(self, producer, send=1):
        # this is thread-safe when send is false
        # note, that strings are not wrapped in 
        # producers by default
        if self.closed:
            return
        self.producer_fifo.push(producer)
        if send: self.initiate_send()

    push_with_producer=push

    def close(self):
        self.closed=1
        while self.producer_fifo:
            p=self.producer_fifo.first()
            if p is not None and type(p) != StringType:
                p.more() # free up resources held by producer
            self.producer_fifo.pop()
        asyncore.dispatcher.close(self)

#----------------------------------------------------------------------

class FCGIServer(asyncore.dispatcher):
    """
    Listens for and accepts FastCGI requests and hands them off to a
    FCGIChannel for handling.

    FCGIServer can be configured to listen on either a specific port
    (for inet sockets) or socket_file (for unix domain sockets.)

    For inet sockets, the ip argument specifies the address from which
    the server will accept connections, '' indicates all addresses. If
    you only want to accept connections from the localhost, set ip to
    '127.0.0.1'.
    """

    channel_class=FCGIChannel

    def __init__(self,
                 module='Main',
                 ip='127.0.0.1',
                 port=None,
                 socket_file=None,
                 resolver=None,
                 logger_object=None):

        self.ip = ip
        asyncore.dispatcher.__init__(self)
        if not logger_object:
            logger_object = logger.file_logger(sys.stdout)
        if resolver:
            self.logger = logger.resolving_logger(resolver, logger_object)
        else:
            self.logger = logger.unresolving_logger(logger_object)

        # get configuration
        self.module = module
        self.port = port
        self.socket_file = socket_file

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
        self.listen(256)
        self.log_info('FastCGI Server (V%s) started at %s\n'
                      '\tIP          : %s\n'
                      '\tPort        : %s\n'
                      '\tSocket path : %s\n'
                      % (__version__, time.ctime(time.time()), self.ip,
                         self.port, self.socket_file))



    def handle_accept(self):
        try:
            conn, addr = self.accept()
        except socket.error:
            self.log_info('Server accept() threw an exception', 'warning')
            return
        self.channel_class(self, conn, addr)


    def readable(self):
        return len(asyncore.socket_map) < CONNECTION_LIMIT


    def writable (self):
        return 0


    def listen(self, num):
        # override asyncore limits for nt's listen queue size
        self.accepting = 1
        return self.socket.listen(num)

#----------------------------------------------------------------------

class FCGIResponse(HTTPResponse):
  
    _tempfile=None
    _tempstart=0
    
    def setChannel(self, channel):
        self.channel = channel

    def write(self, data):
        stdout=self.stdout
        
        if not self._wrote:
            l=self.headers.get('content-length', None)
            if l is not None:
                try:
                    if type(l) is type(''): l=string.atoi(l)
                    if l > 128000:
                        self._tempfile=TemporaryFile()
                except: pass
                    
            stdout.write(str(self))
            self._wrote=1

        if not data: return

        t=self._tempfile
        if t is None:
            stdout.write(data)
        else:
            while data:
                # write file producers
                # each producer holds 32K data
                chunk=data[:32768]
                data=data[32768:]
                l=len(chunk)
                b=self._tempstart
                e=b+l
                t.seek(b)
                t.write(chunk)
                self._tempstart=e
                stdout.write((file_part_producer(t,b,e), l))

    def _finish(self):
        t=self._tempfile
        if t is not None:
            self.stdout.write((file_close_producer(t), 0))
        self._tempfile=None

        self.channel.sendStreamTerminator(FCGI_STDOUT)
        self.channel.sendEndRecord()
        self.stdout.close()
        self.stderr.close()

        # The following was adapted from PCGIPipe.finish and PCGIPipe.close
        # I don't really understand it enough to know if I got it right...
        shutdown = 0
        if self.headers.get('bobo-exception-type','') == \
                'exceptions.SystemExit':
            r = self.headers.get('bobo-exception-value','0')
            try: r=string.atoi(r)
            except: r = r and 1 or 0
            shutdown = r,

        if not self.channel.closed:
            self.channel.push_with_producer(LoggingProducer(self.channel,
                                                            self.stdout.length,
                                                            'log_request'), 0)
        if shutdown:
            sys.ZServerExitCode = shutdown[0]
            self.channel.push(ShutdownProducer(), 0)
            Wakeup(lambda: asyncore.close_all())
        else:
            self.channel.push(None,0)
            Wakeup()
        self.channel=None



#----------------------------------------------------------------------

class FCGIPipe:
    """
    This class acts like a file and is used to catch stdout/stderr
    from ZPublisher and create FCGI records out of the data stream to
    send back to the web server.
    """
    def __init__(self, channel, recType):
        self.channel = channel
        self.recType = recType
        self.length  = 0


    def write(self, data):
        if type(data)==type(''):
            datalen = len(data)
        else:
            p, datalen = data
        if data:
            self.channel.sendDataRecord(data, self.recType)
            self.length = self.length + datalen

    def close(self):
        self.channel = None


#----------------------------------------------------------------------



