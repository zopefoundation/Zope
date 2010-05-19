# -*- coding: iso-8859-15 -*-

import unittest

class HTTPResponseTests(unittest.TestCase):

    def _getTargetClass(self):

        from ZPublisher.HTTPResponse import HTTPResponse
        return HTTPResponse

    def _makeOne(self, *args, **kw):

        return self._getTargetClass()(*args, **kw)

    def test_setStatus_with_exceptions(self):

        from zExceptions import Unauthorized
        from zExceptions import Forbidden
        from zExceptions import NotFound
        from zExceptions import BadRequest
        from zExceptions import InternalError

        for exc_type, code in ((Unauthorized, 401),
                               (Forbidden, 403),
                               (NotFound, 404),
                               (BadRequest, 400),
                               (InternalError, 500)):
            response = self._makeOne()
            response.setStatus(exc_type)
            self.assertEqual(response.status, code)

    def test_setCookie_no_attrs(self):
        response = self._makeOne()
        response.setCookie('foo', 'bar')
        cookie = response.cookies.get('foo', None)
        self.assertEqual(len(cookie), 2)
        self.assertEqual(cookie.get('value'), 'bar')
        self.assertEqual(cookie.get('quoted'), True)

        cookies = response._cookie_list()
        self.assertEqual(len(cookies), 1)
        self.assertEqual(cookies[0], 'Set-Cookie: foo="bar"')

    def test_setCookie_w_expires(self):
        EXPIRES = 'Wed, 31-Dec-97 23:59:59 GMT'
        response = self._makeOne()
        response.setCookie('foo', 'bar', expires=EXPIRES)
        cookie = response.cookies.get('foo', None)
        self.failUnless(cookie)
        self.assertEqual(cookie.get('value'), 'bar')
        self.assertEqual(cookie.get('expires'), EXPIRES)
        self.assertEqual(cookie.get('quoted'), True)

        cookies = response._cookie_list()
        self.assertEqual(len(cookies), 1)
        self.assertEqual(cookies[0],
                         'Set-Cookie: foo="bar"; Expires=%s' % EXPIRES)

    def test_setCookie_w_domain(self):
        response = self._makeOne()
        response.setCookie('foo', 'bar', domain='example.com')
        cookie = response.cookies.get('foo', None)
        self.assertEqual(len(cookie), 3)
        self.assertEqual(cookie.get('value'), 'bar')
        self.assertEqual(cookie.get('domain'), 'example.com')
        self.assertEqual(cookie.get('quoted'), True)

        cookies = response._cookie_list()
        self.assertEqual(len(cookies), 1)
        self.assertEqual(cookies[0],
                         'Set-Cookie: foo="bar"; Domain=example.com')

    def test_setCookie_w_path(self):
        response = self._makeOne()
        response.setCookie('foo', 'bar', path='/')
        cookie = response.cookies.get('foo', None)
        self.assertEqual(len(cookie), 3)
        self.assertEqual(cookie.get('value'), 'bar')
        self.assertEqual(cookie.get('path'), '/')
        self.assertEqual(cookie.get('quoted'), True)

        cookies = response._cookie_list()
        self.assertEqual(len(cookies), 1)
        self.assertEqual(cookies[0], 'Set-Cookie: foo="bar"; Path=/')

    def test_setCookie_w_comment(self):
        response = self._makeOne()
        response.setCookie('foo', 'bar', comment='COMMENT')
        cookie = response.cookies.get('foo', None)
        self.assertEqual(len(cookie), 3)
        self.assertEqual(cookie.get('value'), 'bar')
        self.assertEqual(cookie.get('comment'), 'COMMENT')
        self.assertEqual(cookie.get('quoted'), True)

        cookies = response._cookie_list()
        self.assertEqual(len(cookies), 1)
        self.assertEqual(cookies[0], 'Set-Cookie: foo="bar"; Comment=COMMENT')

    def test_setCookie_w_secure_true_value(self):
        response = self._makeOne()
        response.setCookie('foo', 'bar', secure='SECURE')
        cookie = response.cookies.get('foo', None)
        self.assertEqual(len(cookie), 3)
        self.assertEqual(cookie.get('value'), 'bar')
        self.assertEqual(cookie.get('secure'), 'SECURE')
        self.assertEqual(cookie.get('quoted'), True)

        cookies = response._cookie_list()
        self.assertEqual(len(cookies), 1)
        self.assertEqual(cookies[0], 'Set-Cookie: foo="bar"; Secure')

    def test_setCookie_w_secure_false_value(self):
        response = self._makeOne()
        response.setCookie('foo', 'bar', secure='')
        cookie = response.cookies.get('foo', None)
        self.assertEqual(len(cookie), 3)
        self.assertEqual(cookie.get('value'), 'bar')
        self.assertEqual(cookie.get('secure'), '')
        self.assertEqual(cookie.get('quoted'), True)

        cookies = response._cookie_list()
        self.assertEqual(len(cookies), 1)
        self.assertEqual(cookies[0], 'Set-Cookie: foo="bar"')

    def test_expireCookie(self):
        response = self._makeOne()
        response.expireCookie('foo', path='/')
        cookie = response.cookies.get('foo', None)
        self.failUnless(cookie)
        self.assertEqual(cookie.get('expires'), 'Wed, 31-Dec-97 23:59:59 GMT')
        self.assertEqual(cookie.get('max_age'), 0)
        self.assertEqual(cookie.get('path'), '/')

    def test_setCookie_w_httponly_true_value(self):
        response = self._makeOne()
        response.setCookie('foo', 'bar', http_only=True)
        cookie = response.cookies.get('foo', None)
        self.assertEqual(len(cookie), 3)
        self.assertEqual(cookie.get('value'), 'bar')
        self.assertEqual(cookie.get('http_only'), True)
        self.assertEqual(cookie.get('quoted'), True)

        cookie_list = response._cookie_list()
        self.assertEqual(len(cookie_list), 1)
        self.assertEqual(cookie_list[0], 'Set-Cookie: foo="bar"; HTTPOnly')

    def test_setCookie_w_httponly_false_value(self):
        response = self._makeOne()
        response.setCookie('foo', 'bar', http_only=False)
        cookie = response.cookies.get('foo', None)
        self.assertEqual(len(cookie), 3)
        self.assertEqual(cookie.get('value'), 'bar')
        self.assertEqual(cookie.get('http_only'), False)
        self.assertEqual(cookie.get('quoted'), True)

        cookie_list = response._cookie_list()
        self.assertEqual(len(cookie_list), 1)
        self.assertEqual(cookie_list[0], 'Set-Cookie: foo="bar"')

    def test_setCookie_unquoted(self):
        response = self._makeOne()
        response.setCookie('foo', 'bar', quoted=False)
        cookie = response.cookies.get('foo', None)
        self.assertEqual(len(cookie), 2)
        self.assertEqual(cookie.get('value'), 'bar')
        self.assertEqual(cookie.get('quoted'), False)

        cookie_list = response._cookie_list()
        self.assertEqual(len(cookie_list), 1)
        self.assertEqual(cookie_list[0], 'Set-Cookie: foo=bar')

    def test_expireCookie1160(self):
        # Verify that the cookie is expired even if an expires kw arg is passed
        # http://zope.org/Collectors/Zope/1160
        response = self._makeOne()
        response.expireCookie('foo', path='/',
                              expires='Mon, 22-Mar-2004 17:59 GMT', max_age=99)
        cookie = response.cookies.get('foo', None)
        self.failUnless(cookie)
        self.assertEqual(cookie.get('expires'), 'Wed, 31-Dec-97 23:59:59 GMT')
        self.assertEqual(cookie.get('max_age'), 0)
        self.assertEqual(cookie.get('path'), '/')

    def test_appendCookie(self):
        response = self._makeOne()
        response.setCookie('foo', 'bar', path='/')
        response.appendCookie('foo', 'baz')
        cookie = response.cookies.get('foo', None)
        self.failUnless(cookie)
        self.assertEqual(cookie.get('value'), 'bar:baz')
        self.assertEqual(cookie.get('path'), '/')

    def test_appendHeader(self):
        response = self._makeOne()
        response.setHeader('foo', 'bar')
        response.appendHeader('foo', 'foo')
        self.assertEqual(response.headers.get('foo'), 'bar,\r\n\tfoo')
        response.setHeader('xxx', 'bar')
        response.appendHeader('XXX', 'foo')
        self.assertEqual(response.headers.get('xxx'), 'bar,\r\n\tfoo')

    def test_setHeader(self):
        response = self._makeOne()
        response.setHeader('foo', 'bar')
        self.assertEqual(response.getHeader('foo'), 'bar')
        self.assertEqual(response.headers.get('foo'), 'bar')
        response.setHeader('SPAM', 'eggs')
        self.assertEqual(response.getHeader('spam'), 'eggs')
        self.assertEqual(response.getHeader('SPAM'), 'eggs')

    def test_setHeader_literal(self):
        response = self._makeOne()
        response.setHeader('foo', 'bar', literal=True)
        self.assertEqual(response.getHeader('foo'), 'bar')
        response.setHeader('SPAM', 'eggs', literal=True)
        self.assertEqual(response.getHeader('SPAM', literal=True), 'eggs')
        self.assertEqual(response.getHeader('spam'), None)

    def test_setStatus_ResourceLockedError(self):
        response = self._makeOne()
        from webdav.Lockable import ResourceLockedError
        response.setStatus(ResourceLockedError)
        self.assertEqual(response.status, 423)

    def test_charset_no_header(self):
        response = self._makeOne(body='foo')
        self.assertEqual(response.headers.get('content-type'),
                         'text/plain; charset=iso-8859-15')

    def test_charset_text_header(self):
        response = self._makeOne(body='foo',
                    headers={'content-type': 'text/plain'})
        self.assertEqual(response.headers.get('content-type'),
                         'text/plain; charset=iso-8859-15')

    def test_charset_application_header_no_header(self):
        response = self._makeOne(body='foo',
                    headers={'content-type': 'application/foo'})
        self.assertEqual(response.headers.get('content-type'),
                         'application/foo')

    def test_charset_application_header_with_header(self):
        response = self._makeOne(body='foo',
                    headers={'content-type': 'application/foo; charset: something'})
        self.assertEqual(response.headers.get('content-type'),
                         'application/foo; charset: something')
    
    def test_charset_application_header_unicode(self):
        response = self._makeOne(body=unicode('ärger', 'iso-8859-15'),
                    headers={'content-type': 'application/foo'})
        self.assertEqual(response.headers.get('content-type'),
                         'application/foo; charset=iso-8859-15')
        self.assertEqual(response.body, 'ärger')

    def test_charset_application_header_unicode_1(self):
        response = self._makeOne(body=unicode('ärger', 'iso-8859-15'),
                    headers={'content-type': 'application/foo; charset=utf-8'})
        self.assertEqual(response.headers.get('content-type'),
                         'application/foo; charset=utf-8')
        self.assertEqual(response.body, unicode('ärger',
                         'iso-8859-15').encode('utf-8'))

    def test_XMLEncodingRecoding(self):
        xml = u'<?xml version="1.0" encoding="iso-8859-15" ?>\n<foo><bar/></foo>'
        response = self._makeOne(body=xml, headers={'content-type': 'text/xml; charset=utf-8'})
        self.assertEqual(xml.replace('iso-8859-15', 'utf-8')==response.body, True)
        response = self._makeOne(body=xml, headers={'content-type': 'text/xml; charset=iso-8859-15'})
        self.assertEqual(xml==response.body, True)

    def test_addHeader_drops_CRLF(self):
        # RFC2616 disallows CRLF in a header value.
        response = self._makeOne()
        response.addHeader('Location',
                           'http://www.ietf.org/rfc/\r\nrfc2616.txt')
        self.assertEqual(response.accumulated_headers,
                         'Location: http://www.ietf.org/rfc/rfc2616.txt\r\n')

    def test_appendHeader_drops_CRLF(self):
        # RFC2616 disallows CRLF in a header value.
        response = self._makeOne()
        response.appendHeader('Location',
                               'http://www.ietf.org/rfc/\r\nrfc2616.txt')
        self.assertEqual(response.headers['location'],
                         'http://www.ietf.org/rfc/rfc2616.txt')

    def test_setHeader_drops_CRLF(self):
        # RFC2616 disallows CRLF in a header value.
        response = self._makeOne()
        response.setHeader('Location',
                           'http://www.ietf.org/rfc/\r\nrfc2616.txt')
        self.assertEqual(response.headers['location'],
                         'http://www.ietf.org/rfc/rfc2616.txt')

    def test_setHeader_drops_CRLF_when_accumulating(self):
        # RFC2616 disallows CRLF in a header value.
        response = self._makeOne()
        response.setHeader('Set-Cookie', 'allowed="OK"')
        response.setHeader('Set-Cookie',
                       'violation="http://www.ietf.org/rfc/\r\nrfc2616.txt"')
        self.assertEqual(response.accumulated_headers,
                'Set-Cookie: allowed="OK"\r\n' +
                'Set-Cookie: '
                'violation="http://www.ietf.org/rfc/rfc2616.txt"\r\n')

    def test_setBody_compression_vary(self):
        # Vary header should be added here
        response = self._makeOne()
        response.enableHTTPCompression(REQUEST={'HTTP_ACCEPT_ENCODING': 'gzip'})
        response.setBody('foo'*100) # body must get smaller on compression
        self.assertEqual('Accept-Encoding' in response.getHeader('Vary'), True)
        # But here it would be unnecessary
        response = self._makeOne()
        response.enableHTTPCompression(REQUEST={'HTTP_ACCEPT_ENCODING': 'gzip'})
        response.setHeader('Vary', 'Accept-Encoding,Accept-Language')
        before = response.getHeader('Vary')
        response.setBody('foo'*100)
        self.assertEqual(before, response.getHeader('Vary'))


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(HTTPResponseTests, 'test'))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
