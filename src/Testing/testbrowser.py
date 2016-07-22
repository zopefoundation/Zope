##############################################################################
#
# Copyright (c) 2006 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Support for using zope.testbrowser from Zope2.

Mostly just copy and paste from zope.testbrowser.testing.
"""

import cStringIO
import httplib
import urllib2

import mechanize
from zExceptions import status_reasons
from zope.testbrowser import browser

from Testing.ZopeTestCase.zopedoctest import functional


class PublisherConnection(object):

    def __init__(self, host, timeout=None):
        self.caller = functional.http
        self.host = host

    def set_debuglevel(self, level):
        pass

    def _quote(self, url):
        # the publisher expects to be able to split on whitespace, so we have
        # to make sure there is none in the URL
        return url.replace(' ', '%20')

    def request(self, method, url, body=None, headers=None):
        """Send a request to the publisher.

        The response will be stored in ``self.response``.
        """
        if body is None:
            body = ''

        if url == '':
            url = '/'

        url = self._quote(url)
        # Extract the handle_error option header
        handle_errors_key = 'X-Zope-Handle-Errors'
        handle_errors_header = headers.get(handle_errors_key, True)
        if handle_errors_key in headers:
            del headers[handle_errors_key]
        # Translate string to boolean.
        handle_errors = {'False': False}.get(handle_errors_header, True)

        # Construct the headers.
        header_chunks = []
        if headers is not None:
            for header in headers.items():
                header_chunks.append('%s: %s' % header)
            headers = '\n'.join(header_chunks) + '\n'
        else:
            headers = ''

        # Construct the full HTTP request string, since that is what the
        # ``HTTPCaller`` wants.
        request_string = (method + ' ' + url + ' HTTP/1.1\n' +
                          headers + '\n' + body)
        self.response = self.caller(request_string, handle_errors)

    def getresponse(self):
        """Return a ``urllib2`` compatible response.

        The goal of ths method is to convert the Zope Publisher's reseponse to
        a ``urllib2`` compatible response, which is also understood by
        mechanize.
        """
        real_response = self.response._response
        status = real_response.getStatus()
        reason = status_reasons[real_response.status]
        headers = []
        # Convert header keys to camel case. This is basically a copy
        # paste from ZPublisher.HTTPResponse
        for key, val in real_response.headers.items():
            if key.lower() == key:
                # only change non-literal header names
                key = "%s%s" % (key[:1].upper(), key[1:])
                start = 0
                l = key.find('-', start)
                while l >= start:
                    key = "%s-%s%s" % (
                        key[:l], key[l + 1:l + 2].upper(), key[l + 2:])
                    start = l + 1
                    l = key.find('-', start)
            headers.append((key, val))
        # get the cookies, breaking them into tuples for sorting
        cookies = real_response._cookie_list()
        headers.extend(cookies)
        headers.sort()
        headers.insert(0, ('Status', "%s %s" % (status, reason)))
        headers = '\r\n'.join('%s: %s' % h for h in headers)
        content = real_response.body
        return PublisherResponse(content, headers, status, reason)


class PublisherResponse(object):
    """``mechanize`` compatible response object."""

    def __init__(self, content, headers, status, reason):
        self.content = content
        self.status = status
        self.reason = reason
        self.msg = httplib.HTTPMessage(cStringIO.StringIO(headers), 0)
        self.content_as_file = cStringIO.StringIO(self.content)

    def read(self, amt=None):
        return self.content_as_file.read(amt)

    def close(self):
        """To overcome changes in mechanize and socket in python2.5"""
        pass


class PublisherHTTPHandler(urllib2.HTTPHandler):
    """Special HTTP handler to use the Zope Publisher."""

    http_request = urllib2.AbstractHTTPHandler.do_request_

    def http_open(self, req):
        """Open an HTTP connection having a ``urllib2`` request."""
        # Here we connect to the publisher.
        return self.do_open(PublisherConnection, req)


class PublisherMechanizeBrowser(mechanize.Browser):
    """Special ``mechanize`` browser using the Zope Publisher HTTP handler."""

    default_schemes = ['http']
    default_others = ['_http_error', '_http_request_upgrade',
                      '_http_default_error']
    default_features = ['_redirect', '_cookies', '_referer', '_refresh',
                        '_equiv', '_basicauth', '_digestauth']

    def __init__(self, *args, **kws):
        self.handler_classes = mechanize.Browser.handler_classes.copy()
        self.handler_classes["http"] = PublisherHTTPHandler
        self.default_others = [cls for cls in self.default_others
                               if cls in mechanize.Browser.handler_classes]
        mechanize.Browser.__init__(self, *args, **kws)


class Browser(browser.Browser):
    """A Zope ``testbrowser` Browser that uses the Zope Publisher."""

    def __init__(self, url=None):
        mech_browser = PublisherMechanizeBrowser()
        # override the http handler class
        mech_browser.handler_classes["http"] = PublisherHTTPHandler
        super(Browser, self).__init__(url=url, mech_browser=mech_browser)
