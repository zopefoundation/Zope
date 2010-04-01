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
Response class for the FTP Server.
"""

from ZServer.HTTPResponse import ZServerHTTPResponse
from PubCore.ZEvent import Wakeup
from cStringIO import StringIO
import marshal


class FTPResponse(ZServerHTTPResponse):
    """
    Response to an FTP command
    """

    def __str__(self):
        return ''

    def outputBody(self):
        pass

    def setCookie(self, name, value, **kw):
        self.cookies[name]=value

    def appendCookie(self, name, value):
        self.cookies[name]=self.cookies[name] + value

    def expireCookie(self, name, **kw):
        if self.cookies.has_key(name):
            del self.cookies[name]

    def _cookie_list(self):
        return []

    def _marshalledBody(self):
        return marshal.loads(self.body)

    def setMessage(self, message):
        self._message = message

    def getMessage(self):
        return getattr(self, '_message', '')

class CallbackPipe:
    """
    Sends response object to a callback. Doesn't write anything.
    The callback takes place in Medusa's thread, not the request thread.
    """
    def __init__(self, callback, args):
        self._callback=callback
        self._args=args
        self._producers=[]

    def close(self):
        pass

    def write(self, text, l=None):
        if text:
            self._producers.append(text)

    def finish(self, response):
        self._response=response
        Wakeup(self.apply) # move callback to medusas thread

    def apply(self):
        result=apply(self._callback, self._args+(self._response,))

        # break cycles
        self._callback=None
        self._response=None
        self._args=None

        return result

def make_response(channel, callback, *args):
    # XXX should this be the FTPResponse constructor instead?
    r=FTPResponse(stdout=CallbackPipe(callback, args), stderr=StringIO())
    r.setHeader('content-type','text/plain')
    r.cookies=channel.cookies
    return r
