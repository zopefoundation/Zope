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
import time, regex, string
from cStringIO import StringIO

from ZPublisher.HTTPResponse import HTTPResponse, end_of_header_search
from medusa.http_date import build_http_date
from PubCore.ZEvent import Wakeup
from medusa.producers import hooked_producer
from medusa import http_server
from Producers import ShutdownProducer, LoggingProducer, CallbackProducer

__version__='1.0b1'
__zope_version__='1.11a1' # XXX retrieve this somehow
                          # XXX there should be a method somewhere for this

class ZServerHTTPResponse(HTTPResponse):
    "Used to push data into a channel's producer fifo"

    http_chunk=0
    http_chunk_size=1024
    
    def __str__(self,
                html_search=regex.compile('<html>',regex.casefold).search,
                ):        
        if self._wrote: return ''       # Streaming output was used.

        headers=self.headers
        body=self.body
        if body:
            isHTML=self.isHTML(body)
            if not headers.has_key('content-type'):
                if isHTML:
                    c='text/html'
                else:
                    c='text/plain'
                self.setHeader('content-type',c)
            else:
                isHTML = headers['content-type']=='text/html'
            if isHTML and end_of_header_search(self.body) < 0:
                lhtml=html_search(body)
                if lhtml >= 0:
                    lhtml=lhtml+6
                    body='%s<head></head>\n%s' % (body[:lhtml],body[lhtml:])
                else:
                    body='<html><head></head>\n' + body
                self.setBody(body)
                body=self.body

        if not headers.has_key('content-type') and self.status == 200:
            self.setStatus('nocontent')

        if not headers.has_key('content-length'):
            self.setHeader('content-length',len(body))

        headersl=[]
        append=headersl.append
     
        status=headers.get('status', '200 OK')
     
        # status header must come first.
        append("HTTP/%s: %s" % (self._http_version, status))
        if headers.has_key('status'):
            del headers['status']
        
        # add zserver headers
        append('Server: Zope/%s ZServer/%s' % (__zope_version__, __version__)) 
        append('Date: %s' % build_http_date(time.time()))
        append('X-Powered-By: Zope (www.zope.org), Python (www.python.org)')
        chunk=0
        if self._http_version=='1.0':
            if self._http_connection=='keep alive':
                if self.headers.has_key('content-length'):
                    self.setHeader('Connection','close')
                else:
                    self.setHeader('Connection','Keep-Alive')
            else:
                self.setHeader('Connection','close')
        elif self._http_version=='1.1':           
            if self._http_connection=='close':
                self.setHeader('Connection','close')
            elif not self.headers.has_key('content-length'):
                if self.headers.has_key('transfer-encoding'):
                    if self.headers['transfer-encoding'] != 'chunked':
                        self.setHeader('Connection','close')
                    else:
                        chunk=1
                elif self.http_chunk:
                    self.setHeader('Transfer-Encoding','chunked')
                    chunk=1
                else:
                    self.setHeader('Connection','close')
        
        if chunk:
            chunked_body=''
            while body:
                chunk=body[:self.http_chunk_size]
                body=body[self.http_chunk_size:]
                chunked_body='%s%x\r\n%s\r\n' % (chunked_body, len(chunk), chunk)    
            chunked_body='%s0\r\n\r\n' % chunked_body
            body=chunked_body
        
        for key, val in headers.items():
            if string.lower(key)==key:
                # only change non-literal header names
                key="%s%s" % (string.upper(key[:1]), key[1:])
                start=0
                l=string.find(key,'-',start)
                while l >= start:
                    key="%s-%s%s" % (key[:l],string.upper(key[l+1:l+2]),key[l+2:])
                    start=l+1
                    l=string.find(key,'-',start)
            append("%s: %s" % (key, val))
        if self.cookies:
            headersl=headersl+self._cookie_list()
        headersl[len(headersl):]=[self.accumulated_headers, body]
        return string.join(headersl,'\r\n')

    # XXX add server headers, etc to write()
    
    def _finish(self):
        self.stdout.finish(self)
        self.stdout.close()
        
        self.stdout=None # need to break cycle?
        self._request=None


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
    
    def write(self, text):
        self._bytes=self._bytes + len(text)
        self._channel.push(text,0)
        Wakeup()
        
    def close(self):
        self._channel.push(LoggingProducer(self._request, self._bytes), 0)
        self._channel.push(CallbackProducer(self._channel.done))
        if self._shutdown:
            self._channel.push(ShutdownProducer(), 0)
        elif self._close:
            self._channel.push(None, 0)
        Wakeup()
        
        self._channel=None #need to break cycles?
        self._request=None
    
    def finish(self, request):
        if request.headers.get('bobo-exception-type', '') == \
                'exceptions.SystemExit':
            self._shutdown=1
        if request.headers.get('connection','')=='close':
            self._close=1
        self._request.reply_code=request.status
        
        
def make_response(request, headers):
    "Simple http response factory"
	# should this be integrated into the HTTPResponse constructor?
	
    response=ZServerHTTPResponse(stdout=ChannelPipe(request), stderr=StringIO())
    response._http_version=request.version
    response._http_connection=string.lower(
            http_server.get_header(http_server.CONNECTION, request.header))
    return response
    