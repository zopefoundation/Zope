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
ZServer HTTPResponse

The HTTPResponse class takes care of server headers, response munging
and logging duties.

"""
import time, re,  sys, tempfile
from cStringIO import StringIO
import thread
from ZPublisher.HTTPResponse import HTTPResponse
from medusa.http_date import build_http_date
from PubCore.ZEvent import Wakeup
from medusa.producers import hooked_producer
from medusa import http_server
import asyncore
from Producers import ShutdownProducer, LoggingProducer, CallbackProducer, \
    file_part_producer, file_close_producer
from types import LongType
import DebugLogger


class ZServerHTTPResponse(HTTPResponse):
    "Used to push data into a channel's producer fifo"

    # Set this value to 1 if streaming output in
    # HTTP/1.1 should use chunked encoding
    http_chunk=1
    http_chunk_size=1024
    
    # defaults
    _http_version='1.0'
    _http_connection='close'
    _server_version='Zope/2.0 ZServer/2.0'

    # using streaming response
    _streaming=0
    # using chunking transfer-encoding
    _chunking=0

    def __str__(self,
                html_search=re.compile('<html>',re.I).search,
                ):
        if self._wrote:
            if self._chunking:
                return '0\r\n\r\n'
            else:
                return ''

        headers=self.headers
        body=self.body

        # set 204 (no content) status if 200 and response is empty
        # and not streaming
        if not headers.has_key('content-type') and \
                not headers.has_key('content-length') and \
                not self._streaming and \
                self.status == 200:
            self.setStatus('nocontent')

        # add content length if not streaming
        if not headers.has_key('content-length') and \
                not self._streaming:
            self.setHeader('content-length',len(body))

        
        content_length= headers.get('content-length', None)
        if content_length>0 : 
            self.setHeader('content-length', content_length)

        headersl=[]
        append=headersl.append
     
        status=headers.get('status', '200 OK')
     
        # status header must come first.
        append("HTTP/%s %s" % (self._http_version or '1.0' , status))
        if headers.has_key('status'):
            del headers['status']

        if not headers.has_key("Etag"):
            self.setHeader('Etag','')
        
        # add zserver headers
        append('Server: %s' % self._server_version) 
        append('Date: %s' % build_http_date(time.time()))

        if self._http_version=='1.0':
            if self._http_connection=='keep-alive' and \
                    self.headers.has_key('content-length'):
                self.setHeader('Connection','Keep-Alive')
            else:
                self.setHeader('Connection','close')
                
        # Close the connection if we have been asked to.
        # Use chunking if streaming output.
        if self._http_version=='1.1':
            if self._http_connection=='close':
                self.setHeader('Connection','close')
            elif not self.headers.has_key('content-length'):
                if self.http_chunk and self._streaming:
                    self.setHeader('Transfer-Encoding','chunked')
                    self._chunking=1
                else:
                    self.setHeader('Connection','close')                
        
        for key, val in headers.items():
            if key.lower()==key:
                # only change non-literal header names
                key="%s%s" % (key[:1].upper(), key[1:])
                start=0
                l=key.find('-',start)
                while l >= start:
                    key="%s-%s%s" % (key[:l],key[l+1:l+2].upper(),key[l+2:])
                    start=l+1
                    l=key.find('-',start)
            append("%s: %s" % (key, val))
        if self.cookies:
            headersl=headersl+self._cookie_list()
        headersl[len(headersl):]=[self.accumulated_headers, body]
        return "\r\n".join(headersl)

    _tempfile=None
    _templock=None
    _tempstart=0
    
    def write(self,data):
        """\
        Return data as a stream

        HTML data may be returned using a stream-oriented interface.
        This allows the browser to display partial results while
        computation of a response to proceed.

        The published object should first set any output headers or
        cookies on the response object.

        Note that published objects must not generate any errors
        after beginning stream-oriented output. 

        """
        stdout=self.stdout
        
        if not self._wrote:
            l=self.headers.get('content-length', None)
            if l is not None:
                try:
                    if type(l) is type(''): l=int(l)
                    if l > 128000:
                        self._tempfile=tempfile.TemporaryFile()
                        self._templock=thread.allocate_lock()
                except: pass

            self._streaming=1
            stdout.write(str(self))
            self._wrote=1

        if not data: return

        if self._chunking:
            data = '%x\r\n%s\r\n' % (len(data),data)

        t=self._tempfile
        if t is None:
            stdout.write(data)
        else:
            l=len(data)
            b=self._tempstart
            e=b+l
            self._templock.acquire()
            try:
                t.seek(b)
                t.write(data)
            finally:
                self._templock.release()
            self._tempstart=e
            stdout.write(file_part_producer(t,self._templock,b,e), l)
    
    _retried_response = None

    def _finish(self):
        if self._retried_response:
            try:
                self._retried_response._finish()
            finally:
                self._retried_response = None
            return
        stdout=self.stdout

        t=self._tempfile
        if t is not None:
            stdout.write(file_close_producer(t), 0)
            self._tempfile=None
        
        stdout.finish(self)
        stdout.close()
        
        self.stdout=None # need to break cycle?
        self._request=None

    def retry(self):
        """Return a request object to be used in a retry attempt
        """
        # This implementation is a bit lame, because it assumes that
        # only stdout stderr were passed to the constructor. OTOH, I
        # think that that's all that is ever passed.

        response=self.__class__(stdout=self.stdout, stderr=self.stderr)
        response._http_version=self._http_version
        response._http_connection=self._http_connection
        response._server_version=self._server_version
        self._retried_response = response
        return response


class ChannelPipe:
    """Experimental pipe from ZPublisher to a ZServer Channel.
    Should only be used by one thread at a time. Note also that
    the channel will be being handled by another thread, thus
    restrict access to channel to the push method only."""

    def __init__(self, request):
        self._channel=request.channel
        self._request=request
        self._shutdown=0
        self._close=0
        self._bytes=0
    
    def write(self, text, l=None):
        if self._channel.closed:
            return
        if l is None: l=len(text)
        self._bytes=self._bytes + l
        self._channel.push(text,0)
        Wakeup()
        
    def close(self):
        DebugLogger.log('A', id(self._request), 
                '%s %s' % (self._request.reply_code, self._bytes))
        if not self._channel.closed:
            self._channel.push(LoggingProducer(self._request, self._bytes), 0)
            self._channel.push(CallbackProducer(self._channel.done), 0)
            self._channel.push(CallbackProducer(
                lambda t=('E', id(self._request)): apply(DebugLogger.log, t)), 0)
            if self._shutdown:
                try: r=self._shutdown[0]
                except: r=0
                sys.ZServerExitCode=r
                self._channel.push(ShutdownProducer(), 0)
                Wakeup()
            else:
                if self._close: self._channel.push(None, 0)
            Wakeup()
        else:
            # channel closed too soon

            self._request.log(self._bytes)
            DebugLogger.log('E', id(self._request))

            if self._shutdown:
                try: r=self._shutdown[0]
                except: r=0
                sys.ZServerExitCode=r
                Wakeup(lambda: asyncore.close_all())
            else:
                Wakeup()

        self._channel=None #need to break cycles?
        self._request=None

    def flush(self): pass # yeah, whatever
    
    def finish(self, response):
        if response.headers.get('bobo-exception-type', '') == \
                'exceptions.SystemExit':

            r=response.headers.get('bobo-exception-value','0')
            try: r=int(r)
            except: r = r and 1 or 0
            self._shutdown=r,
        if response.headers.get('connection','') == 'close' or \
                response.headers.get('Connection','') == 'close':
            self._close=1
        self._request.reply_code=response.status
        
        
def make_response(request, headers):
    "Simple http response factory"
    # should this be integrated into the HTTPResponse constructor?
    
    response=ZServerHTTPResponse(stdout=ChannelPipe(request), stderr=StringIO())
    response._http_version=request.version
    response._http_connection=(
            http_server.get_header(http_server.CONNECTION, request.header)).lower()
    response._server_version=request.channel.server.SERVER_IDENT
    return response
    

