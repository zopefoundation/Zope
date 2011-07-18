##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
"""
ZServer HTTPResponse

The HTTPResponse class takes care of server headers, response munging
and logging duties.

"""
import asyncore
from cStringIO import StringIO
import re
import tempfile
import thread
import time

from zope.event import notify

from ZPublisher.HTTPResponse import HTTPResponse # XXX WTF?
from ZPublisher.Iterators import IStreamIterator # XXX WTF?
from ZPublisher.pubevents import PubBeforeStreaming # XXX WTF?

from ZServer.medusa.http_date import build_http_date
from ZServer.PubCore.ZEvent import Wakeup
from ZServer.medusa import http_server

from ZServer.Producers import ShutdownProducer
from ZServer.Producers import LoggingProducer
from ZServer.Producers import CallbackProducer
from ZServer.Producers import file_part_producer
from ZServer.Producers import file_close_producer
from ZServer.Producers import iterator_producer
from ZServer.DebugLogger import log


class ZServerHTTPResponse(HTTPResponse):
    "Used to push data into a channel's producer fifo"

    # Set this value to 1 if streaming output in
    # HTTP/1.1 should use chunked encoding
    http_chunk = 1
    http_chunk_size = 1024

    # defaults
    _http_version = '1.0'
    _http_connection = 'close'
    _server_version = 'Zope/2.0 ZServer/2.0'

    # using streaming response
    _streaming = 0
    # using chunking transfer-encoding
    _chunking = 0
    _bodyproducer = None

    def __str__(self):
        if self._wrote:
            if self._chunking:
                return '0\r\n\r\n'
            else:
                return ''

        headers = self.headers
        body = self.body

        # set 204 (no content) status if 200 and response is empty
        # and not streaming
        if ('content-type' not in headers and 
            'content-length' not in headers and 
            not self._streaming and self.status == 200):
            self.setStatus('nocontent')

        if self.status in (100, 101, 102, 204, 304):
            # These responses should not have any body or Content-Length.
            # See RFC 2616 4.4 "Message Length".
            body = ''
            if 'content-length' in headers:
                del headers['content-length']
            if 'content-type' in headers:
                del headers['content-type']
        elif not headers.has_key('content-length') and not self._streaming:
            self.setHeader('content-length', len(body))

        chunks = []
        append = chunks.append


        # status header must come first.
        append("HTTP/%s %d %s" % (self._http_version or '1.0',
                                  self.status, self.errmsg))

        # add zserver headers
        append('Server: %s' % self._server_version)
        append('Date: %s' % build_http_date(time.time()))

        if self._http_version == '1.0':
            if self._http_connection == 'keep-alive':
                self.setHeader('Connection','Keep-Alive')
            else:
                self.setHeader('Connection','close')

        # Close the connection if we have been asked to.
        # Use chunking if streaming output.
        if self._http_version == '1.1':
            if self._http_connection == 'close':
                self.setHeader('Connection','close')
            elif (not self.headers.has_key('content-length') and 
                  self.http_chunk and self._streaming):
                self.setHeader('Transfer-Encoding','chunked')
                self._chunking = 1
                    
        headers = headers.items()
        headers.extend(self.accumulated_headers)

        for key, val in headers:
            if key.lower() == key:
                # only change non-literal header names
                key = "%s%s" % (key[:1].upper(), key[1:])
                start = 0
                l = key.find('-',start)
                while l >= start:
                    key = "%s-%s%s" % (key[:l],
                                       key[l+1:l+2].upper(),
                                       key[l+2:])
                    start = l + 1
                    l = key.find('-', start)
                val = val.replace('\n\t', '\r\n\t')
            append("%s: %s" % (key, val))
        if self.cookies:
            chunks.extend(['%s: %s' % x for x in self._cookie_list()])
            
        append('')
        append(body)
        return "\r\n".join(chunks)

    _tempfile = None
    _templock = None
    _tempstart = 0

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


        if type(data) is not str:
            raise TypeError('Value must be a string')

        stdout = self.stdout

        if not self._wrote:
            notify(PubBeforeStreaming(self))

            l = self.headers.get('content-length', None)
            if l is not None:
                try:
                    if type(l) is str: l = int(l)
                    if l > 128000:
                        self._tempfile = tempfile.TemporaryFile()
                        self._templock = thread.allocate_lock()
                except: pass

            self._streaming = 1
            stdout.write(str(self))
            self._wrote = 1

        if not data: return

        if self._chunking:
            data = '%x\r\n%s\r\n' % (len(data),data)

        l = len(data)

        t = self._tempfile
        if t is None or l<200:
            stdout.write(data)
        else:
            b = self._tempstart
            e = b + l
            self._templock.acquire()
            try:
                t.seek(b)
                t.write(data)
            finally:
                self._templock.release()
            self._tempstart = e
            stdout.write(file_part_producer(t,self._templock,b,e), l)

    _retried_response = None

    def _finish(self):
        if self._retried_response:
            try:
                self._retried_response._finish()
            finally:
                self._retried_response = None
            return
        stdout = self.stdout

        t = self._tempfile
        if t is not None:
            stdout.write(file_close_producer(t), 0)
            self._tempfile = None

        stdout.finish(self)
        stdout.close()

        self.stdout = None # need to break cycle?
        self._request = None

    def retry(self):
        """Return a request object to be used in a retry attempt
        """
        # This implementation is a bit lame, because it assumes that
        # only stdout stderr were passed to the constructor. OTOH, I
        # think that that's all that is ever passed.

        response = self.__class__(stdout=self.stdout, stderr=self.stderr)
        response.headers = self.headers
        response._http_version = self._http_version
        response._http_connection = self._http_connection
        response._server_version = self._server_version
        self._retried_response = response
        return response

    def outputBody(self):
        """Output the response body"""
        self.stdout.write(str(self))
        if self._bodyproducer:
            self.stdout.write(self._bodyproducer, 0)
        # we assign None to self._bodyproducer below to ensure that even
        # if self is part of a cycle which causes a leak that we
        # don't leak the bodyproducer (which often holds a reference to
        # an open file descriptor, and leaking file descriptors can have
        # particularly bad ramifications for a long-running process)
        self._bodyproducer = None

    def setBody(self, body, title='', is_error=0, **kw):
        """ Accept either a stream iterator or a string as the body """
        if IStreamIterator.providedBy(body):
            assert(self.headers.has_key('content-length'))
            # wrap the iterator up in a producer that medusa can understand
            self._bodyproducer = iterator_producer(body)
            HTTPResponse.setBody(self, '', title, is_error, **kw)
            return self
        else:
            HTTPResponse.setBody(self, body, title, is_error, **kw)

class ChannelPipe:
    """Experimental pipe from ZPublisher to a ZServer Channel.
    Should only be used by one thread at a time. Note also that
    the channel will be being handled by another thread, thus
    restrict access to channel to the push method only."""

    def __init__(self, request):
        self._channel = request.channel
        self._request = request
        self._shutdown = 0
        self._close = 0
        self._bytes = 0

    def write(self, text, l=None):
        if self._channel.closed:
            return
        if l is None: l = len(text)
        self._bytes = self._bytes + l
        self._channel.push(text,0)
        Wakeup()

    def close(self):
        log('A', id(self._request),
                '%s %s' % (self._request.reply_code, self._bytes))
        if not self._channel.closed:
            self._channel.push(LoggingProducer(self._request, self._bytes), 0)
            self._channel.push(CallbackProducer(self._channel.done), 0)
            self._channel.push(CallbackProducer(
                lambda t=('E', id(self._request)): apply(log, t)), 0)
            if self._shutdown:
                self._channel.push(ShutdownProducer(), 0)
                Wakeup()
            else:
                if self._close: self._channel.push(None, 0)
            Wakeup()
        else:
            # channel closed too soon

            self._request.log(self._bytes)
            log('E', id(self._request))

            if self._shutdown:
                Wakeup(lambda: asyncore.close_all())
            else:
                Wakeup()

        self._channel = None #need to break cycles?
        self._request = None

    def flush(self): pass # yeah, whatever

    def finish(self, response):
        if response._shutdownRequested():
            self._shutdown = 1
        if response.headers.get('connection','') == 'close' or \
                response.headers.get('Connection','') == 'close':
            self._close = 1
        self._request.reply_code = response.status

    def start_response(self, status, headers, exc_info=None):
        # Used for WSGI
        self._request.reply_code = int(status.split(' ')[0])
        status = 'HTTP/%s %s\r\n' % (self._request.version, status)
        self.write(status)
        headers = '\r\n'.join([': '.join(x) for x in headers])
        self.write(headers)
        self.write('\r\n\r\n')
        return self.write
        

is_proxying_match = re.compile(r'[^ ]* [^ \\]*:').match
proxying_connection_re = re.compile ('Proxy-Connection: (.*)', re.IGNORECASE)

def make_response(request, headers):
    "Simple http response factory"
    # should this be integrated into the HTTPResponse constructor?

    response = ZServerHTTPResponse(stdout=ChannelPipe(request),
                                   stderr=StringIO())
    response._http_version = request.version
    if request.version == '1.0' and is_proxying_match(request.request):
        # a request that was made as if this zope was an http 1.0 proxy.
        # that means we have to use some slightly different http
        # headers to manage persistent connections.
        connection_re = proxying_connection_re
    else:
        # a normal http request
        connection_re = http_server.CONNECTION
    response._http_connection = http_server.get_header(connection_re,
                                                       request.header).lower()
    response._server_version = request.channel.server.SERVER_IDENT
    return response
