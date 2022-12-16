import traceback
import unittest
from io import BytesIO

from zExceptions import BadRequest
from zExceptions import Forbidden
from zExceptions import InternalError
from zExceptions import NotFound
from zExceptions import ResourceLockedError
from zExceptions import Unauthorized

from ..HTTPResponse import encode_params
from ..HTTPResponse import encode_words
from ..HTTPResponse import header_encoding_registry
from ..HTTPResponse import make_content_disposition


class HTTPResponseTests(unittest.TestCase):

    def _getTargetClass(self):
        from ZPublisher.HTTPResponse import HTTPResponse
        return HTTPResponse

    def _makeOne(self, *args, **kw):
        return self._getTargetClass()(*args, **kw)

    def test_ctor_defaults(self):
        response = self._makeOne()
        self.assertEqual(response.accumulated_headers, [])
        self.assertEqual(response.status, 200)
        self.assertEqual(response.errmsg, 'OK')
        self.assertEqual(response.base, '')
        self.assertEqual(response.body, b'')
        self.assertEqual(response.charset, 'utf-8')
        self.assertEqual(response.cookies, {})
        self.assertEqual(response.headers, {})
        self.assertIsInstance(response.stdout, BytesIO)
        self.assertIsInstance(response.stderr, BytesIO)

    def test_ctor_w_body(self):
        response = self._makeOne(body=b'ABC')
        self.assertEqual(response.body, b'ABC')

    def test_ctor_w_headers(self):
        response = self._makeOne(headers={'foo': 'bar'})
        self.assertEqual(response.headers, {'foo': 'bar'})

    def test_ctor_w_status_code(self):
        response = self._makeOne(status=401)
        self.assertEqual(response.status, 401)
        self.assertEqual(response.errmsg, 'Unauthorized')
        self.assertEqual(response.headers, {})

    def test_ctor_w_status_errmsg(self):
        response = self._makeOne(status='Unauthorized')
        self.assertEqual(response.status, 401)
        self.assertEqual(response.errmsg, 'Unauthorized')
        self.assertEqual(response.headers, {})

    def test_ctor_w_status_exception(self):
        response = self._makeOne(status=Unauthorized)
        self.assertEqual(response.status, 401)
        self.assertEqual(response.errmsg, 'Unauthorized')
        self.assertEqual(response.headers, {})

    def test_ctor_charset_no_content_type_header(self):
        response = self._makeOne(body=b'foo')
        self.assertEqual(response.headers.get('content-type'),
                         'text/plain; charset=utf-8')

    def test_ctor_charset_text_header_no_charset_defaults_latin1(self):
        response = self._makeOne(body=b'foo',
                                 headers={'content-type': 'text/plain'})
        self.assertEqual(response.headers.get('content-type'),
                         'text/plain; charset=utf-8')

    def test_ctor_charset_application_header_no_header(self):
        response = self._makeOne(body=b'foo',
                                 headers={'content-type': 'application/foo'})
        self.assertEqual(response.headers.get('content-type'),
                         'application/foo')

    def test_ctor_charset_application_header_with_header(self):
        response = self._makeOne(
            body=b'foo',
            headers={'content-type': 'application/foo; charset: something'})
        self.assertEqual(response.headers.get('content-type'),
                         'application/foo; charset: something')

    def test_ctor_charset_unicode_body_application_header(self):
        BODY = '\xe4rger'
        response = self._makeOne(body=BODY,
                                 headers={'content-type': 'application/foo'})
        self.assertEqual(response.headers.get('content-type'),
                         'application/foo')
        self.assertEqual(response.body, BODY.encode('utf-8'))

    def test_ctor_charset_unicode_body_application_header_diff_encoding(self):
        BODY = '\xe4rger'
        response = self._makeOne(body=BODY,
                                 headers={'content-type':
                                          'application/foo; charset=utf-8'})
        self.assertEqual(response.headers.get('content-type'),
                         'application/foo; charset=utf-8')
        # Body is re-encoded to match the header
        self.assertEqual(response.body, BODY.encode('utf-8'))

    def test_ctor_body_recodes_to_match_content_type_charset(self):
        xml = ('<?xml version="1.0" encoding="iso-8859-15" ?>\n'
               '<foo><bar/></foo>')
        response = self._makeOne(
            body=xml, headers={
                'content-type': 'text/xml; charset=utf-8'})
        self.assertEqual(response.body,
                         xml.replace('iso-8859-15', 'utf-8').encode('utf-8'))

    def test_ctor_body_already_matches_charset_unchanged(self):
        xml = ('<?xml version="1.0" encoding="iso-8859-15" ?>\n'
               '<foo><bar/></foo>')
        response = self._makeOne(
            body=xml, headers={
                'content-type': 'text/xml; charset=iso-8859-15'})
        self.assertEqual(response.body, xml.encode('iso-8859-15'))

    def test_retry(self):
        STDOUT, STDERR = object(), object()
        response = self._makeOne(stdout=STDOUT, stderr=STDERR)
        cloned = response.retry()
        self.assertIsInstance(cloned, self._getTargetClass())
        self.assertTrue(cloned.stdout is STDOUT)
        self.assertTrue(cloned.stderr is STDERR)

    def test_setStatus_code(self):
        response = self._makeOne()
        response.setStatus(400)
        self.assertEqual(response.status, 400)
        self.assertEqual(response.errmsg, 'Bad Request')

    def test_setStatus_errmsg(self):
        response = self._makeOne()
        response.setStatus('Bad Request')
        self.assertEqual(response.status, 400)
        self.assertEqual(response.errmsg, 'Bad Request')

    def test_setStatus_BadRequest(self):
        response = self._makeOne()
        response.setStatus(BadRequest)
        self.assertEqual(response.status, 400)
        self.assertEqual(response.errmsg, 'Bad Request')

    def test_setStatus_Unauthorized_exception(self):
        response = self._makeOne()
        response.setStatus(Unauthorized)
        self.assertEqual(response.status, 401)
        self.assertEqual(response.errmsg, 'Unauthorized')

    def test_setStatus_Forbidden_exception(self):
        response = self._makeOne()
        response.setStatus(Forbidden)
        self.assertEqual(response.status, 403)
        self.assertEqual(response.errmsg, 'Forbidden')

    def test_setStatus_NotFound_exception(self):
        response = self._makeOne()
        response.setStatus(NotFound)
        self.assertEqual(response.status, 404)
        self.assertEqual(response.errmsg, 'Not Found')

    def test_setStatus_ResourceLockedError_exception(self):
        response = self._makeOne()
        response.setStatus(ResourceLockedError)
        self.assertEqual(response.status, 423)
        self.assertEqual(response.errmsg, 'Locked')

    def test_setStatus_InternalError_exception(self):
        response = self._makeOne()
        response.setStatus(InternalError)
        self.assertEqual(response.status, 500)
        self.assertEqual(response.errmsg, 'Internal Server Error')

    def test_setCookie_no_existing(self):
        response = self._makeOne()
        response.setCookie('foo', 'bar')
        cookie = response.cookies.get('foo', None)
        self.assertEqual(len(cookie), 1)
        self.assertEqual(cookie.get('value'), 'bar')

    def test_setCookie_w_existing(self):
        response = self._makeOne()
        response.setCookie('foo', 'bar')
        response.setCookie('foo', 'baz')
        cookie = response.cookies.get('foo', None)
        self.assertEqual(len(cookie), 1)
        self.assertEqual(cookie.get('value'), 'baz')

    def test_setCookie_no_attrs(self):
        response = self._makeOne()
        response.setCookie('foo', 'bar')
        cookie = response.cookies.get('foo', None)
        self.assertEqual(len(cookie), 1)
        self.assertEqual(cookie.get('value'), 'bar')
        cookies = response._cookie_list()
        self.assertEqual(len(cookies), 1)
        self.assertEqual(cookies[0], ('Set-Cookie', 'foo=bar'))

    def test_setCookie_w_expires(self):
        EXPIRES = 'Wed, 31 Dec 1997 23:59:59 GMT'
        response = self._makeOne()
        response.setCookie('foo', 'bar', expires=EXPIRES)
        cookie = response.cookies.get('foo', None)
        self.assertTrue(cookie)
        self.assertEqual(cookie.get('value'), 'bar')
        self.assertEqual(cookie.get('Expires'), EXPIRES)

        cookies = response._cookie_list()
        self.assertEqual(len(cookies), 1)
        self.assertEqual(cookies[0],
                         ('Set-Cookie', 'foo=bar; Expires=%s' % EXPIRES))

    def test_setCookie_w_domain(self):
        response = self._makeOne()
        response.setCookie('foo', 'bar', domain='example.com')
        cookie = response.cookies.get('foo', None)
        self.assertEqual(len(cookie), 2)
        self.assertEqual(cookie.get('value'), 'bar')
        self.assertEqual(cookie.get('Domain'), 'example.com')

        cookies = response._cookie_list()
        self.assertEqual(len(cookies), 1)
        self.assertEqual(cookies[0],
                         ('Set-Cookie', 'foo=bar; Domain=example.com'))

    def test_setCookie_w_path(self):
        response = self._makeOne()
        response.setCookie('foo', 'bar', path='/')
        cookie = response.cookies.get('foo', None)
        self.assertEqual(len(cookie), 2)
        self.assertEqual(cookie.get('value'), 'bar')
        self.assertEqual(cookie.get('Path'), '/')

        cookies = response._cookie_list()
        self.assertEqual(len(cookies), 1)
        self.assertEqual(cookies[0], ('Set-Cookie', 'foo=bar; Path=/'))

    def test_setCookie_w_comment(self):
        response = self._makeOne()
        response.setCookie('foo', 'bar', comment='COMMENT')
        cookie = response.cookies.get('foo', None)
        self.assertEqual(len(cookie), 2)
        self.assertEqual(cookie.get('value'), 'bar')
        self.assertEqual(cookie.get('Comment'), 'COMMENT')

        cookies = response._cookie_list()
        self.assertEqual(len(cookies), 1)
        self.assertEqual(cookies[0],
                         ('Set-Cookie', 'foo=bar; Comment=COMMENT'))

    def test_setCookie_w_secure_true_value(self):
        response = self._makeOne()
        response.setCookie('foo', 'bar', secure='SECURE')
        cookie = response.cookies.get('foo', None)
        self.assertEqual(len(cookie), 2)
        self.assertEqual(cookie.get('value'), 'bar')
        self.assertIs(cookie.get('Secure'), True)

        cookies = response._cookie_list()
        self.assertEqual(len(cookies), 1)
        self.assertEqual(cookies[0], ('Set-Cookie', 'foo=bar; Secure'))

    def test_setCookie_w_secure_false_value(self):
        response = self._makeOne()
        response.setCookie('foo', 'bar', secure='')
        cookie = response.cookies.get('foo', None)
        self.assertEqual(len(cookie), 2)
        self.assertEqual(cookie.get('value'), 'bar')
        self.assertIsNone(cookie.get('Secure'))

        cookies = response._cookie_list()
        self.assertEqual(len(cookies), 1)
        self.assertEqual(cookies[0], ('Set-Cookie', 'foo=bar'))

    def test_setCookie_w_httponly_true_value(self):
        response = self._makeOne()
        response.setCookie('foo', 'bar', http_only=True)
        cookie = response.cookies.get('foo', None)
        self.assertEqual(len(cookie), 2)
        self.assertEqual(cookie.get('value'), 'bar')
        self.assertEqual(cookie.get('HttpOnly'), True)

        cookie_list = response._cookie_list()
        self.assertEqual(len(cookie_list), 1)
        self.assertEqual(cookie_list[0], ('Set-Cookie', 'foo=bar; HttpOnly'))

    def test_setCookie_w_httponly_false_value(self):
        response = self._makeOne()
        response.setCookie('foo', 'bar', http_only=False)
        cookie = response.cookies.get('foo', None)
        self.assertEqual(len(cookie), 2)
        self.assertEqual(cookie.get('value'), 'bar')
        self.assertIsNone(cookie.get('HttpOnly'))

        cookie_list = response._cookie_list()
        self.assertEqual(len(cookie_list), 1)
        self.assertEqual(cookie_list[0], ('Set-Cookie', 'foo=bar'))

    def test_setCookie_w_same_site(self):
        response = self._makeOne()
        response.setCookie('foo', 'bar', same_site='Strict')
        cookie = response.cookies.get('foo', None)
        self.assertEqual(len(cookie), 2)
        self.assertEqual(cookie.get('value'), 'bar')
        self.assertEqual(cookie.get('SameSite'), 'Strict')
        cookies = response._cookie_list()
        self.assertEqual(len(cookies), 1)
        self.assertEqual(cookies[0],
                         ('Set-Cookie', 'foo=bar; SameSite=Strict'))

    def test_setCookie_unquoted(self):
        response = self._makeOne()
        response.setCookie('foo', 'bar', quoted=False)
        cookie = response.cookies.get('foo', None)
        self.assertEqual(len(cookie), 1)
        self.assertEqual(cookie.get('value'), 'bar')

        cookie_list = response._cookie_list()
        self.assertEqual(len(cookie_list), 1)
        self.assertEqual(cookie_list[0], ('Set-Cookie', 'foo=bar'))

    def test_setCookie_handle_byte_values(self):
        response = self._makeOne()
        response.setCookie('foo', b'bar')
        cookie = response.cookies.get('foo', None)
        self.assertEqual(len(cookie), 1)
        self.assertEqual(cookie.get('value'), b'bar')

        cookie_list = response._cookie_list()
        self.assertEqual(len(cookie_list), 1)
        self.assertEqual(cookie_list[0], ('Set-Cookie', 'foo=bar'))

    def test_setCookie_handle_unicode_values(self):
        response = self._makeOne()
        response.setCookie('foo', 'bar')
        cookie = response.cookies.get('foo', None)
        self.assertEqual(len(cookie), 1)
        self.assertEqual(cookie.get('value'), 'bar')

        cookie_list = response._cookie_list()
        self.assertEqual(len(cookie_list), 1)
        self.assertEqual(cookie_list[0], ('Set-Cookie', 'foo=bar'))

    def test_appendCookie_w_existing(self):
        response = self._makeOne()
        response.setCookie('foo', 'bar', path='/')
        response.appendCookie('foo', 'baz')
        cookie = response.cookies.get('foo', None)
        self.assertTrue(cookie)
        self.assertEqual(cookie.get('value'), 'bar:baz')
        self.assertEqual(cookie.get('Path'), '/')

    def test_appendCookie_no_existing(self):
        response = self._makeOne()
        response.appendCookie('foo', 'baz')
        cookie = response.cookies.get('foo', None)
        self.assertTrue(cookie)
        self.assertEqual(cookie.get('value'), 'baz')

    def test_expireCookie(self):
        response = self._makeOne()
        response.expireCookie('foo', path='/')
        cookie = response.cookies.get('foo', None)
        self.assertTrue(cookie)
        self.assertEqual(cookie.get('Expires'),
                         'Wed, 31 Dec 1997 23:59:59 GMT')
        self.assertEqual(cookie.get('Max-Age'), '0')
        self.assertEqual(cookie.get('Path'), '/')

    def test_expireCookie1160(self):
        # Verify that the cookie is expired even if an expires kw arg is passed
        response = self._makeOne()
        response.expireCookie('foo', path='/',
                              expires='Mon, 22 Mar 2004 17:59 GMT', max_age=99)
        cookie = response.cookies.get('foo', None)
        self.assertTrue(cookie)
        self.assertEqual(cookie.get('Expires'),
                         'Wed, 31 Dec 1997 23:59:59 GMT')
        self.assertEqual(cookie.get('Max-Age'), '0')
        self.assertEqual(cookie.get('Path'), '/')

    def test_getHeader_nonesuch(self):
        response = self._makeOne()
        self.assertEqual(response.getHeader('nonesuch'), None)

    def test_getHeader_existing(self):
        response = self._makeOne(headers={'foo': 'bar'})
        self.assertEqual(response.getHeader('foo'), 'bar')

    def test_getHeader_existing_not_literal(self):
        response = self._makeOne(headers={'foo': 'bar'})
        response.setHeader('spam', 'Eggs')
        self.assertEqual(response.getHeader('Foo'), 'bar')
        self.assertEqual(response.getHeader('Spam'), 'Eggs')

    def test_getHeader_existing_w_literal(self):
        response = self._makeOne()
        response.setHeader('Foo', 'Bar', literal=True)
        self.assertEqual(response.getHeader('Foo', literal=True), 'Bar')

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

    def test_setHeader_drops_CRLF(self):
        # RFC2616 disallows CRLF in a header value.
        response = self._makeOne()
        response.setHeader('Location',
                           'http://www.ietf.org/rfc/\r\nrfc2616.txt')
        self.assertEqual(response.headers['location'],
                         'http://www.ietf.org/rfc/rfc2616.txt')

    def test_setHeader_drops_LF(self):
        # Some browsers accept \n in place of \n\r to separate headers,
        # so we scrub it too.
        response = self._makeOne()
        response.setHeader('Location',
                           'http://www.ietf.org/rfc/\nrfc2616.txt')
        self.assertEqual(response.headers['location'],
                         'http://www.ietf.org/rfc/rfc2616.txt')

    def test_appendHeader_no_existing(self):
        response = self._makeOne()
        response.appendHeader('foo', 'foo')
        self.assertEqual(response.headers.get('foo'), 'foo')

    def test_appendHeader_no_existing_case_insensative(self):
        response = self._makeOne()
        response.appendHeader('Foo', 'foo')
        self.assertEqual(response.headers.get('foo'), 'foo')

    def test_appendHeader_w_existing(self):
        response = self._makeOne()
        response.setHeader('foo', 'bar')
        response.appendHeader('foo', 'foo')
        self.assertEqual(response.headers.get('foo'), 'bar, foo')

    def test_appendHeader_w_existing_case_insenstative(self):
        response = self._makeOne()
        response.setHeader('xxx', 'bar')
        response.appendHeader('XXX', 'foo')
        self.assertEqual(response.headers.get('xxx'), 'bar, foo')

    def test_appendHeader_drops_CRLF(self):
        # RFC2616 disallows CRLF in a header value.
        response = self._makeOne()
        response.appendHeader('Location',
                              'http://www.ietf.org/rfc/\r\nrfc2616.txt')
        self.assertEqual(response.headers['location'],
                         'http://www.ietf.org/rfc/rfc2616.txt')

    def test_addHeader_is_case_sensitive(self):
        response = self._makeOne()
        response.addHeader('Location', 'http://www.ietf.org/rfc/rfc2616.txt')
        self.assertEqual(response.accumulated_headers,
                         [('Location', 'http://www.ietf.org/rfc/rfc2616.txt')])

    def test_addHeader_drops_CRLF(self):
        # RFC2616 disallows CRLF in a header value.
        response = self._makeOne()
        response.addHeader('Location',
                           'http://www.ietf.org/rfc/\r\nrfc2616.txt')
        self.assertEqual(response.accumulated_headers,
                         [('Location', 'http://www.ietf.org/rfc/rfc2616.txt')])

    def test_setBase_None(self):
        response = self._makeOne()
        response.base = 'BEFORE'
        response.setBase(None)
        self.assertEqual(response.base, '')

    def test_setBase_no_trailing_path(self):
        response = self._makeOne()
        response.setBase('foo')
        self.assertEqual(response.base, 'foo/')

    def test_setBase_w_trailing_path(self):
        response = self._makeOne()
        response.setBase('foo/')
        self.assertEqual(response.base, 'foo/')

    def test_insertBase_not_HTML_no_change(self):
        response = self._makeOne()
        response.setHeader('Content-Type', 'application/pdf')
        response.setHeader('Content-Length', 8)
        response.body = b'BLAHBLAH'
        response.insertBase()
        self.assertEqual(response.body, b'BLAHBLAH')
        self.assertEqual(response.getHeader('Content-Length'), '8')

    def test_insertBase_HTML_no_base_w_head_not_munged(self):
        HTML = b'<html><head></head><body></body></html>'
        response = self._makeOne()
        response.setHeader('Content-Type', 'text/html')
        response.setHeader('Content-Length', len(HTML))
        response.body = HTML
        response.insertBase()
        self.assertEqual(response.body, HTML)
        self.assertEqual(response.getHeader('Content-Length'), str(len(HTML)))

    def test_insertBase_HTML_w_base_no_head_not_munged(self):
        HTML = b'<html><body></body></html>'
        response = self._makeOne()
        response.setHeader('Content-Type', 'text/html')
        response.setHeader('Content-Length', len(HTML))
        response.body = HTML
        response.insertBase()
        self.assertEqual(response.body, HTML)
        self.assertEqual(response.getHeader('Content-Length'), str(len(HTML)))

    def test_insertBase_HTML_w_base_w_head_munged(self):
        HTML = b'<html><head></head><body>\xc3\xa4scii</body></html>'
        MUNGED = (b'<html><head>\n'
                  b'<base href="http://example.com/base/" />\n'
                  b'</head><body>\xc3\xa4scii</body></html>')
        response = self._makeOne()
        response.setHeader('Content-Type', 'text/html')
        response.setHeader('Content-Length', len(HTML))
        response.body = HTML
        response.setBase('http://example.com/base/')
        response.insertBase()
        self.assertEqual(response.body, MUNGED)
        self.assertEqual(int(response.getHeader('Content-Length')),
                         len(MUNGED))

    def test_setBody_w_locking(self):
        response = self._makeOne()
        response.setBody(b'BEFORE', lock=True)
        result = response.setBody(b'AFTER')
        self.assertFalse(result)
        self.assertEqual(response.body, b'BEFORE')

    def test_setBody_empty_unchanged(self):
        response = self._makeOne()
        response.body = b'BEFORE'
        result = response.setBody(b'')
        self.assertTrue(result)
        self.assertEqual(response.body, b'BEFORE')
        self.assertEqual(response.getHeader('Content-Type'), None)
        self.assertEqual(response.getHeader('Content-Length'), None)

    def test_setBody_with_is_error_converted_to_Site_Error(self):
        response = self._makeOne()
        response.body = b'BEFORE'
        result = response.setBody(b'BODY', 'TITLE', is_error=True)
        self.assertTrue(result)
        self.assertFalse(b'BEFORE' in response.body)
        self.assertTrue(b'<h2>Site Error</h2>' in response.body)
        self.assertTrue(b'TITLE' in response.body)
        self.assertTrue(b'BODY' in response.body)
        self.assertEqual(response.getHeader('Content-Type'),
                         'text/html; charset=utf-8')

    def test_setBody_string_not_HTML(self):
        response = self._makeOne()
        result = response.setBody(b'BODY')
        self.assertTrue(result)
        self.assertEqual(response.body, b'BODY')
        self.assertEqual(response.getHeader('Content-Type'),
                         'text/plain; charset=utf-8')
        self.assertEqual(response.getHeader('Content-Length'), '4')

    def test_setBody_string_HTML_uses_text_plain(self):
        HTML = '<html><head></head><body></body></html>'
        response = self._makeOne()
        result = response.setBody(HTML)
        self.assertTrue(result)
        self.assertEqual(response.body, HTML.encode('utf-8'))
        # content type is set as text/plain, even though body
        # could be guessed as html
        self.assertEqual(response.getHeader('Content-Type'),
                         'text/plain; charset=utf-8')
        self.assertEqual(response.getHeader('Content-Length'), str(len(HTML)))

    def test_setBody_object_with_asHTML(self):
        HTML = '<html><head></head><body></body></html>'

        class Dummy:
            def asHTML(self):
                return HTML
        response = self._makeOne()
        result = response.setBody(Dummy())
        self.assertTrue(result)
        self.assertEqual(response.body, HTML.encode('utf-8'))
        self.assertEqual(response.getHeader('Content-Type'),
                         'text/html; charset=utf-8')
        self.assertEqual(response.getHeader('Content-Length'), str(len(HTML)))

    def test_setBody_object_with_unicode(self):
        HTML = ('<html><head></head><body>'
                '<h1>Tr\u0039s Bien</h1></body></html>')
        ENCODED = HTML.encode('utf-8')
        response = self._makeOne()
        result = response.setBody(HTML)
        self.assertTrue(result)
        self.assertEqual(response.body, ENCODED)
        self.assertEqual(response.getHeader('Content-Type'),
                         'text/plain; charset=utf-8')
        self.assertEqual(response.getHeader('Content-Length'),
                         str(len(ENCODED)))

    def test_setBody_list(self):
        """Test that setBody casts lists of ints into their str representation,
        regardless of if the values are in byte range."""
        resp = self._makeOne()
        for body in ([1, 2, 3], [1, 2, 500]):
            resp.setBody(body)
            self.assertEqual(resp.body, str(body).encode('ascii'))

    def test_setBody_io(self):
        """
        Test that BytesIO.getbuffer() can be used to write a binary response.
        """
        from io import BytesIO
        resp = self._makeOne()
        value = b'\x00\x01'
        bio = BytesIO(value)
        resp.setBody(bio.getbuffer())
        self.assertEqual(resp.body, value)

    def test_setBody_by_content_type(self):
        """
        Check that a list as response is treated differently depending on the
        content type.
        """
        resp = self._makeOne()
        body = [1, 2, 3]

        resp.setBody(body)
        self.assertEqual(resp.body, str(body).encode('ascii'))

        resp.setHeader('Content-Type', 'application/x-octet-stream')
        resp.setBody(body)
        self.assertEqual(resp.body, bytes(body))

        resp.setHeader('Content-Type', 'text/plain')
        resp.setBody(body)
        self.assertEqual(resp.body, str(body).encode('ascii'))

    def test_setBody_w_bogus_pseudo_HTML(self):
        # The 2001 checkin message which added the path-under-test says:
        # (r19315): "merged content type on error fixes from 2.3
        # If the str of the object returs a Python "pointer" looking mess,
        # don't let it get treated as HTML.
        BOGUS = b'<Bogus 0xa39d53d>'
        response = self._makeOne()
        self.assertRaises(NotFound, response.setBody, BOGUS)

    def test_setBody_tuple(self):
        response = self._makeOne()
        response.setBody(('a',))
        self.assertEqual(b"('a',)", response.body)
        response.setBody(('a', 'b'))
        self.assertEqual(b"('a', 'b')", response.body)
        response.setBody(('a', 'b', 'c'))
        self.assertEqual(b"('a', 'b', 'c')", response.body)

    def test_setBody_calls_insertBase(self):
        response = self._makeOne()
        lamb = {}

        def _insertBase():
            lamb['flavor'] = 'CURRY'
        response.insertBase = _insertBase
        response.setBody(b'Garlic Naan')
        self.assertEqual(lamb['flavor'], 'CURRY')

    def test_setBody_compression_uncompressible_mimetype(self):
        BEFORE = b'foo' * 100  # body must get smaller on compression
        response = self._makeOne()
        response.setHeader('Content-Type', 'image/jpeg')
        response.enableHTTPCompression({'HTTP_ACCEPT_ENCODING': 'gzip'})
        response.setBody(BEFORE)
        self.assertFalse(response.getHeader('Content-Encoding'))
        self.assertEqual(response.body, BEFORE)

    def test_setBody_compression_existing_encoding(self):
        BEFORE = b'foo' * 100  # body must get smaller on compression
        response = self._makeOne()
        response.setHeader('Content-Encoding', 'piglatin')
        response.enableHTTPCompression({'HTTP_ACCEPT_ENCODING': 'gzip'})
        response.setBody(BEFORE)
        self.assertEqual(response.getHeader('Content-Encoding'), 'piglatin')
        self.assertEqual(response.body, BEFORE)

    def test_setBody_compression_too_short_to_gzip(self):
        BEFORE = b'foo'  # body must get smaller on compression
        response = self._makeOne()
        response.enableHTTPCompression({'HTTP_ACCEPT_ENCODING': 'gzip'})
        response.setBody(BEFORE)
        self.assertFalse(response.getHeader('Content-Encoding'))
        self.assertEqual(response.body, BEFORE)

    def test_setBody_compression_no_prior_vary_header(self):
        # Vary header should be added here
        response = self._makeOne()
        response.enableHTTPCompression({'HTTP_ACCEPT_ENCODING': 'gzip'})
        response.setBody(b'foo' * 100)  # body must get smaller on compression
        self.assertTrue('Accept-Encoding' in response.getHeader('Vary'))

    def test_setBody_compression_w_prior_vary_header_wo_encoding(self):
        # Vary header should be added here
        response = self._makeOne()
        response.setHeader('Vary', 'Cookie')
        response.enableHTTPCompression({'HTTP_ACCEPT_ENCODING': 'gzip'})
        response.setBody(b'foo' * 100)  # body must get smaller on compression
        self.assertTrue('Accept-Encoding' in response.getHeader('Vary'))

    def test_setBody_compression_w_prior_vary_header_incl_encoding(self):
        # Vary header already had Accept-Ecoding', do'nt munge
        PRIOR = 'Accept-Encoding,Accept-Language'
        response = self._makeOne()
        response.enableHTTPCompression({'HTTP_ACCEPT_ENCODING': 'gzip'})
        response.setHeader('Vary', PRIOR)
        response.setBody(b'foo' * 100)
        self.assertEqual(response.getHeader('Vary'), PRIOR)

    def test_setBody_compression_no_prior_vary_header_but_forced(self):
        # Compression forced, don't add a Vary entry for compression.
        response = self._makeOne()
        response.enableHTTPCompression({'HTTP_ACCEPT_ENCODING': 'gzip'},
                                       force=True)
        response.setBody(b'foo' * 100)  # body must get smaller on compression
        self.assertEqual(response.getHeader('Vary'), None)

    def _redirectURLCheck(self, url, expected=None, lock=False, status=302):
        if not expected:
            expected = url
        response = self._makeOne()
        result = response.redirect(url, lock=lock, status=status)
        self.assertEqual(result, expected)
        self.assertEqual(response.getHeader('Location'), expected)
        return response

    def test_redirect_defaults(self):
        URL = 'http://example.com/@@login'
        response = self._redirectURLCheck(URL)
        self.assertEqual(response.status, 302)
        self.assertFalse(response._locked_status)

    def test_redirect_explicit_status(self):
        URL = 'http://example.com'
        response = self._redirectURLCheck(URL, status=307)
        self.assertEqual(response.status, 307)
        self.assertFalse(response._locked_status)

    def test_redirect_w_lock(self):
        URL = 'http://example.com'
        response = self._redirectURLCheck(URL, lock=True)
        self.assertEqual(response.status, 302)
        self.assertTrue(response._locked_status)

    def test_redirect_nonascii(self):
        URL = 'http://example.com/\xe4'
        BYTES_URL = URL.encode('UTF-8')
        ENC_URL = 'http://example.com/%C3%A4'

        # Pass in an unencoded string as URL
        self._redirectURLCheck(URL, expected=ENC_URL)

        # Pass in an encoded string as URL
        self._redirectURLCheck(BYTES_URL, expected=ENC_URL)

        # Pass in a HTTPException with an unencoded string as URL
        from zExceptions import HTTPMovedPermanently
        exc = HTTPMovedPermanently(URL)
        self._redirectURLCheck(exc, expected=ENC_URL)

        # Pass in a HTTPException with an encoded string as URL
        from zExceptions import HTTPMovedPermanently
        exc = HTTPMovedPermanently(BYTES_URL)
        self._redirectURLCheck(exc, expected=ENC_URL)

    def test_redirect_nonascii_everywhere(self):
        URL = "http://uä:pä@sä:80/pä?qä#fä"
        ENC_URL = "http://u%C3%A4:p%C3%A4@s%C3%A4:80/p%C3%A4?q%C3%A4#f%C3%A4"
        self._redirectURLCheck(URL, ENC_URL)

    def test_redirect_alreadyquoted(self):
        # If a URL is already quoted, don't double up on the quoting
        ENC_URL = 'http://example.com/M%C3%A4H'
        self._redirectURLCheck(ENC_URL)

    def test_redirect_unreserved_chars(self):
        # RFC 2396 section 2.3, characters that should not be encoded
        url = "http://example.com/-_.!~*'()"
        self._redirectURLCheck(url)

    def test_redirect_reserved_chars(self):
        # RFC 2396 section 3.3, characters with reserved meaning in a path
        url = 'http://example.com/+/$/;/,/=/?/&/@@index.html'
        self._redirectURLCheck(url)

    def test__encode_unicode_no_content_type_uses_default_encoding(self):
        UNICODE = '<h1>Tr\u0039s Bien</h1>'
        response = self._makeOne()
        self.assertEqual(response._encode_unicode(UNICODE),
                         UNICODE.encode('UTF8'))

    def test__encode_unicode_w_content_type_no_charset_updates_charset(self):
        UNICODE = '<h1>Tr\u0039s Bien</h1>'
        response = self._makeOne()
        response.setHeader('Content-Type', 'text/html')
        self.assertEqual(response._encode_unicode(UNICODE),
                         UNICODE.encode('UTF8'))
        response.getHeader('Content-Type', 'text/html; charset=UTF8')

    def test__encode_unicode_w_content_type_w_charset(self):
        UNICODE = '<h1>Tr\u0039s Bien</h1>'
        response = self._makeOne()
        response.setHeader('Content-Type', 'text/html; charset=latin1')
        self.assertEqual(response._encode_unicode(UNICODE),
                         UNICODE.encode('latin-1'))
        response.getHeader('Content-Type', 'text/html; charset=latin1')

    def test__encode_unicode_w_content_type_w_charset_xml_preamble(self):
        PREAMBLE = '<?xml version="1.0" ?>'
        ELEMENT = '<element>Tr\u0039s Bien</element>'
        UNICODE = '\n'.join([PREAMBLE, ELEMENT])
        response = self._makeOne()
        response.setHeader('Content-Type', 'text/html; charset=latin1')
        self.assertEqual(response._encode_unicode(UNICODE),
                         b'<?xml version="1.0" encoding="latin1" ?>\n'
                         + ELEMENT.encode('latin-1'))
        response.getHeader('Content-Type', 'text/html; charset=latin1')

    def test_quoteHTML(self):
        BEFORE = '<p>This is a story about a boy named "Sue"</p>'
        AFTER = ('&lt;p&gt;This is a story about a boy named '
                 '&quot;Sue&quot;&lt;/p&gt;')
        response = self._makeOne()
        self.assertEqual(response.quoteHTML(BEFORE), AFTER)

    def test_notFoundError(self):
        response = self._makeOne()
        try:
            response.notFoundError()
        except NotFound as raised:
            self.assertEqual(response.status, 404)
            self.assertTrue("<p><b>Resource:</b> Unknown</p>" in str(raised))
        else:
            self.fail("Didn't raise NotFound")

    def test_notFoundError_w_entry(self):
        response = self._makeOne()
        try:
            response.notFoundError('ENTRY')
        except NotFound as raised:
            self.assertEqual(response.status, 404)
            self.assertTrue("<p><b>Resource:</b> ENTRY</p>" in str(raised))
        else:
            self.fail("Didn't raise NotFound")

    def test_forbiddenError(self):
        response = self._makeOne()
        try:
            response.forbiddenError()
        except NotFound as raised:
            self.assertEqual(response.status, 404)
            self.assertTrue("<p><b>Resource:</b> Unknown</p>" in str(raised))
        else:
            self.fail("Didn't raise NotFound")

    def test_forbiddenError_w_entry(self):
        response = self._makeOne()
        try:
            response.forbiddenError('ENTRY')
        except NotFound as raised:
            self.assertEqual(response.status, 404)
            self.assertTrue("<p><b>Resource:</b> ENTRY</p>" in str(raised))
        else:
            self.fail("Didn't raise NotFound")

    def test_debugError(self):
        response = self._makeOne()
        try:
            response.debugError('testing')
        except NotFound as raised:
            self.assertEqual(response.status, 200)
            self.assertIn(
                "Zope has encountered a problem publishing your object. <p>'testing'</p>",  # noqa: E501
                str(raised),
            )
        else:
            self.fail("Didn't raise NotFound")
        try:
            response.debugError(("testing",))
        except NotFound as raised:
            self.assertEqual(response.status, 200)
            self.assertIn(
                "Zope has encountered a problem publishing your object. <p>(\'testing\',)</p>",  # noqa: E501
                str(raised),
            )
        else:
            self.fail("Didn't raise NotFound")
        try:
            response.debugError(("foo", "bar"))
        except NotFound as raised:
            self.assertEqual(response.status, 200)
            self.assertIn(
                "Zope has encountered a problem publishing your object. <p>(\'foo\', \'bar\')</p>",  # noqa: E501
                str(raised),
            )
        else:
            self.fail("Didn't raise NotFound")

    def test_badRequestError_valid_parameter_name(self):
        response = self._makeOne()
        try:
            response.badRequestError('some_parameter')
        except BadRequest as raised:
            self.assertEqual(response.status, 400)
            self.assertTrue("The parameter, <em>some_parameter</em>, "
                            "was omitted from the request." in str(raised))
        else:
            self.fail("Didn't raise BadRequest")

    def test_badRequestError_invalid_parameter_name(self):
        response = self._makeOne()
        try:
            response.badRequestError('URL1')
        except InternalError as raised:
            self.assertEqual(response.status, 400)
            self.assertTrue("Sorry, an internal error occurred in this "
                            "resource." in str(raised))
        else:
            self.fail("Didn't raise InternalError")

    def test__unauthorized_no_realm(self):
        response = self._makeOne()
        response.realm = ''
        response._unauthorized()
        self.assertFalse('WWW-Authenticate' in response.headers)

    def test__unauthorized_w_default_realm(self):
        response = self._makeOne()
        response._unauthorized()
        self.assertTrue('WWW-Authenticate' in response.headers)  # literal
        self.assertEqual(response.headers['WWW-Authenticate'],
                         'basic realm="Zope", charset="UTF-8"')

    def test__unauthorized_w_realm(self):
        response = self._makeOne()
        response.realm = 'Folly'
        response._unauthorized()
        self.assertTrue('WWW-Authenticate' in response.headers)  # literal
        self.assertEqual(response.headers['WWW-Authenticate'],
                         'basic realm="Folly", charset="UTF-8"')

    def test_unauthorized_no_debug_mode(self):
        response = self._makeOne()
        try:
            response.unauthorized()
        except Unauthorized as raised:
            self.assertEqual(response.status, 200)  # publisher sets 401 later
            self.assertTrue("You are not authorized "
                            "to access this resource." in str(raised))
        else:
            self.fail("Didn't raise Unauthorized")

    def test_unauthorized_w_debug_mode_no_credentials(self):
        response = self._makeOne()
        response.debug_mode = True
        try:
            response.unauthorized()
        except Unauthorized as raised:
            self.assertTrue("\nNo Authorization header found."
                            in str(raised))
        else:
            self.fail("Didn't raise Unauthorized")

    def test_unauthorized_w_debug_mode_w_credentials(self):
        response = self._makeOne()
        response.debug_mode = True
        response._auth = 'bogus'
        try:
            response.unauthorized()
        except Unauthorized as raised:
            self.assertTrue("\nUsername and password are not correct."
                            in str(raised))
        else:
            self.fail("Didn't raise Unauthorized")

    def test_finalize_empty(self):
        response = self._makeOne()
        status, headers = response.finalize()
        self.assertEqual(status, '200 OK')
        self.assertEqual(headers,
                         [('X-Powered-By', 'Zope (www.zope.dev), '
                                           'Python (www.python.org)'),
                          ('Content-Length', '0'),
                          ])

    def test_finalize_w_body(self):
        response = self._makeOne()
        response.body = b'TEST'
        status, headers = response.finalize()
        self.assertEqual(status, '200 OK')
        self.assertEqual(headers,
                         [('X-Powered-By', 'Zope (www.zope.dev), '
                                           'Python (www.python.org)'),
                          ('Content-Length', '4'),
                          ])

    def test_finalize_w_existing_content_length(self):
        response = self._makeOne()
        response.setHeader('Content-Length', '42')
        status, headers = response.finalize()
        self.assertEqual(status, '200 OK')
        self.assertEqual(headers,
                         [('X-Powered-By', 'Zope (www.zope.dev), '
                                           'Python (www.python.org)'),
                          ('Content-Length', '42'),
                          ])

    def test_finalize_w_transfer_encoding(self):
        response = self._makeOne()
        response.setHeader('Transfer-Encoding', 'slurry')
        status, headers = response.finalize()
        self.assertEqual(status, '200 OK')
        self.assertEqual(headers,
                         [('X-Powered-By', 'Zope (www.zope.dev), '
                                           'Python (www.python.org)'),
                          ('Transfer-Encoding', 'slurry'),
                          ])

    def test_finalize_after_redirect(self):
        response = self._makeOne()
        response.redirect('http://example.com/')
        status, headers = response.finalize()
        self.assertEqual(status, '302 Found')
        expected = {
            ('X-Powered-By', 'Zope (www.zope.dev), Python (www.python.org)'),
            ('Content-Length', '0'),
            ('Location', 'http://example.com/'),
        }
        self.assertEqual(set(headers), expected)

    def test_listHeaders_empty(self):
        response = self._makeOne()
        headers = response.listHeaders()
        self.assertEqual(headers,
                         [('X-Powered-By', 'Zope (www.zope.dev), '
                                           'Python (www.python.org)'),
                          ])

    def test_listHeaders_already_wrote(self):
        # listHeaders doesn't do the short-circuit on _wrote.
        response = self._makeOne()
        response._wrote = True
        headers = response.listHeaders()
        self.assertEqual(headers,
                         [('X-Powered-By', 'Zope (www.zope.dev), '
                                           'Python (www.python.org)'),
                          ])

    def test_listHeaders_existing_content_length(self):
        response = self._makeOne()
        response.setHeader('Content-Length', 42)
        headers = response.listHeaders()
        self.assertEqual(headers,
                         [('X-Powered-By', 'Zope (www.zope.dev), '
                                           'Python (www.python.org)'),
                          ('Content-Length', '42'),
                          ])

    def test_listHeaders_existing_transfer_encoding(self):
        # If 'Transfer-Encoding' is set, don't force 'Content-Length'.
        response = self._makeOne()
        response.setHeader('Transfer-Encoding', 'slurry')
        headers = response.listHeaders()
        self.assertEqual(headers,
                         [('X-Powered-By', 'Zope (www.zope.dev), '
                                           'Python (www.python.org)'),
                          ('Transfer-Encoding', 'slurry'),
                          ])

    def test_listHeaders_after_setHeader(self):
        response = self._makeOne()
        response.setHeader('x-consistency', 'Foolish')
        headers = response.listHeaders()
        self.assertEqual(headers,
                         [('X-Powered-By', 'Zope (www.zope.dev), '
                                           'Python (www.python.org)'),
                          ('X-Consistency', 'Foolish'),
                          ])

    def test_listHeaders_after_setHeader_literal(self):
        response = self._makeOne()
        response.setHeader('X-consistency', 'Foolish', literal=True)
        headers = response.listHeaders()
        self.assertEqual(headers,
                         [('X-Powered-By', 'Zope (www.zope.dev), '
                                           'Python (www.python.org)'),
                          ('X-consistency', 'Foolish'),
                          ])

    def test_listHeaders_after_redirect(self):
        response = self._makeOne()
        response.redirect('http://example.com/')
        headers = response.listHeaders()
        self.assertEqual(headers,
                         [('X-Powered-By', 'Zope (www.zope.dev), '
                                           'Python (www.python.org)'),
                          ('Location', 'http://example.com/'),
                          ])

    def test_listHeaders_after_setCookie_appendCookie(self):
        response = self._makeOne()
        response.setCookie('foo', 'bar', path='/')
        response.appendCookie('foo', 'baz')
        headers = response.listHeaders()
        self.assertEqual(headers,
                         [('X-Powered-By', 'Zope (www.zope.dev), '
                                           'Python (www.python.org)'),
                          ('Set-Cookie', 'foo=bar%3Abaz; Path=/'),
                          ])

    def test_listHeaders_after_expireCookie(self):
        response = self._makeOne()
        response.expireCookie('qux', path='/')
        headers = dict(response.listHeaders())
        cookie_header = headers.pop('Set-Cookie')
        headers = list(headers.items())
        expected = {
            ('X-Powered-By', 'Zope (www.zope.dev), Python (www.python.org)'),
        }
        self.assertEqual(set(headers), expected)
        self.assertEqual(
            set(cookie_header.split('; ')),
            {'qux=deleted', 'Path=/', 'Max-Age=0',
             'Expires=Wed, 31 Dec 1997 23:59:59 GMT'}
        )

    def test_listHeaders_after_addHeader(self):
        response = self._makeOne()
        response.addHeader('X-Consistency', 'Foolish')
        response.addHeader('X-Consistency', 'Oatmeal')
        headers = response.listHeaders()
        self.assertEqual(headers,
                         [('X-Powered-By', 'Zope (www.zope.dev), '
                                           'Python (www.python.org)'),
                          ('X-Consistency', 'Foolish'),
                          ('X-Consistency', 'Oatmeal'),
                          ])

    def test_listHeaders_w_body(self):
        response = self._makeOne()
        response.setBody(b'BLAH')
        headers = response.listHeaders()
        expected = {
            ('X-Powered-By', 'Zope (www.zope.dev), Python (www.python.org)'),
            ('Content-Length', '4'),
            ('Content-Type', 'text/plain; charset=utf-8'),
        }
        self.assertEqual(set(headers), expected)

    def test___str__already_wrote(self):
        response = self._makeOne()
        response._wrote = True
        self.assertEqual(bytes(response), b'')

    def test___str__empty(self):
        response = self._makeOne()
        result = bytes(response)
        lines = result.split(b'\r\n')
        self.assertEqual(len(lines), 5)
        expected = {
            b'Status: 200 OK',
            b'X-Powered-By: Zope (www.zope.dev), Python (www.python.org)',
            b'Content-Length: 0',
            b'',
        }
        self.assertEqual(set(lines), expected)

    def test___str__existing_content_length(self):
        # The application can break clients by setting a bogus length;  we
        # don't do anything to stop that.
        response = self._makeOne()
        response.setHeader('Content-Length', 42)
        result = bytes(response)
        lines = result.split(b'\r\n')
        self.assertEqual(len(lines), 5)
        expected = {
            b'Status: 200 OK',
            b'X-Powered-By: Zope (www.zope.dev), Python (www.python.org)',
            b'Content-Length: 42',
            b'',
        }
        self.assertEqual(set(lines), expected)

    def test___str__existing_transfer_encoding(self):
        # If 'Transfer-Encoding' is set, don't force 'Content-Length'.
        response = self._makeOne()
        response.setHeader('Transfer-Encoding', 'slurry')
        result = bytes(response)
        lines = result.split(b'\r\n')
        self.assertEqual(len(lines), 5)
        expected = {
            b'Status: 200 OK',
            b'X-Powered-By: Zope (www.zope.dev), Python (www.python.org)',
            b'Transfer-Encoding: slurry',
            b'',
        }
        self.assertEqual(set(lines), expected)

    def test___str__after_setHeader(self):
        response = self._makeOne()
        response.setHeader('x-consistency', 'Foolish')
        result = bytes(response)
        lines = result.split(b'\r\n')
        self.assertEqual(len(lines), 6)
        expected = {
            b'Status: 200 OK',
            b'X-Powered-By: Zope (www.zope.dev), Python (www.python.org)',
            b'Content-Length: 0',
            b'X-Consistency: Foolish',
            b'',
        }
        self.assertEqual(set(lines), expected)

    def test___str__after_setHeader_literal(self):
        response = self._makeOne()
        response.setHeader('X-consistency', 'Foolish', literal=True)
        result = bytes(response)
        lines = result.split(b'\r\n')
        self.assertEqual(len(lines), 6)
        expected = {
            b'Status: 200 OK',
            b'X-Powered-By: Zope (www.zope.dev), Python (www.python.org)',
            b'Content-Length: 0',
            b'X-consistency: Foolish',
            b'',
        }
        self.assertEqual(set(lines), expected)

    def test___str__after_redirect(self):
        response = self._makeOne()
        response.redirect('http://example.com/')
        result = bytes(response)
        lines = result.split(b'\r\n')
        self.assertEqual(len(lines), 6)
        expected = {
            b'Status: 302 Found',
            b'X-Powered-By: Zope (www.zope.dev), Python (www.python.org)',
            b'Content-Length: 0',
            b'Location: http://example.com/',
            b'',
        }
        self.assertEqual(set(lines), expected)

    def test___str__after_setCookie_appendCookie(self):
        response = self._makeOne()
        response.setCookie('foo', 'bar', path='/')
        response.appendCookie('foo', 'baz')
        result = bytes(response)
        lines = result.split(b'\r\n')
        self.assertEqual(len(lines), 6)
        expected = {
            b'Status: 200 OK',
            b'X-Powered-By: Zope (www.zope.dev), Python (www.python.org)',
            b'Content-Length: 0',
            b'Set-Cookie: foo=bar%3Abaz; Path=/',
            b'',
        }
        self.assertEqual(set(lines), expected)

    def test___str__after_expireCookie(self):
        response = self._makeOne()
        response.expireCookie('qux', path='/')
        result = bytes(response)
        lines = result.split(b'\r\n')
        cookie_line = [line for line in lines if b'Set-Cookie' in line][0]
        other_lines = [line for line in lines if b'Set-Cookie' not in line]
        self.assertEqual(len(lines), 6)
        expected = {
            b'Status: 200 OK',
            b'X-Powered-By: Zope (www.zope.dev), Python (www.python.org)',
            b'Content-Length: 0',
            b'',
        }
        self.assertEqual(set(other_lines), expected)
        cookie_value = cookie_line.split(b': ', 1)[-1]
        self.assertEqual(
            set(cookie_value.split(b'; ')),
            {b'qux=deleted', b'Path=/', b'Max-Age=0',
             b'Expires=Wed, 31 Dec 1997 23:59:59 GMT'}
        )

    def test___str__after_addHeader(self):
        response = self._makeOne()
        response.addHeader('X-Consistency', 'Foolish')
        response.addHeader('X-Consistency', 'Oatmeal')
        result = bytes(response)
        lines = result.split(b'\r\n')
        self.assertEqual(len(lines), 7)
        expected = {
            b'Status: 200 OK',
            b'X-Powered-By: Zope (www.zope.dev), Python (www.python.org)',
            b'Content-Length: 0',
            b'X-Consistency: Foolish',
            b'X-Consistency: Oatmeal',
            b'',
        }
        self.assertEqual(set(lines), expected)

    def test___str__w_body(self):
        response = self._makeOne()
        response.setBody(b'BLAH')
        result = bytes(response)
        lines = result.split(b'\r\n')
        self.assertEqual(len(lines), 6)
        expected = {
            b'Status: 200 OK',
            b'X-Powered-By: Zope (www.zope.dev), Python (www.python.org)',
            b'Content-Length: 4',
            b'Content-Type: text/plain; charset=utf-8',
            b'BLAH',
            b'',
        }
        self.assertEqual(set(lines), expected)
        # Body is separated by a newline
        self.assertEqual(lines[4], b'')
        self.assertEqual(lines[5], b'BLAH')

    def test_write_already_wrote(self):
        stdout = BytesIO()
        response = self._makeOne(stdout=stdout)
        response.write(b'Kilroy was here!')
        self.assertTrue(response._wrote)
        lines = stdout.getvalue().split(b'\r\n')
        self.assertEqual(len(lines), 5)
        expected = {
            b'Status: 200 OK',
            b'X-Powered-By: Zope (www.zope.dev), Python (www.python.org)',
            b'Content-Length: 0',
            b'Kilroy was here!',
            b'',
        }
        self.assertEqual(set(lines), expected)
        # Body is separated by a newline
        self.assertEqual(lines[3], b'')
        self.assertEqual(lines[4], b'Kilroy was here!')

    def test_write_not_already_wrote(self):
        stdout = BytesIO()
        response = self._makeOne(stdout=stdout)
        response._wrote = True
        response.write(b'Kilroy was here!')
        lines = stdout.getvalue().split(b'\r\n')
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0], b'Kilroy was here!')

    def test_exception_Internal_Server_Error(self):
        response = self._makeOne()
        try:
            raise AttributeError('ERROR VALUE')
        except AttributeError:
            body = response.exception()
            self.assertTrue(b'ERROR VALUE' in bytes(body))
            self.assertEqual(response.status, 500)
            self.assertEqual(response.errmsg, 'Internal Server Error')

    def test_exception_500_text(self):
        message = 'ERROR \xe4 VALUE'
        exc = AttributeError(message)
        expected = traceback.format_exception_only(
            exc.__class__, exc)[0].encode('utf-8')
        response = self._makeOne()
        try:
            raise exc
        except AttributeError:
            body = response.exception()
            self.assertTrue(expected in bytes(body))
            self.assertEqual(response.status, 500)
            self.assertEqual(response.errmsg, 'Internal Server Error')

    def test_isHTML_not_decodable_bytes(self):
        response = self._makeOne()
        self.assertFalse(response.isHTML('bïñårÿ'.encode('latin1')))

    def test_header_encoding(self):
        r = self._makeOne()
        r.setHeader("unencoded1", "€")
        r.setHeader("content-disposition", "a; p=€")
        r.addHeader("unencoded2", "€")
        r.addHeader("content-disposition", "a2; p2=€")
        r.addHeader("bytes", b"abc")
        hdrs = r.listHeaders()[1:]  # drop `X-Powered...`
        shdrs, ahdrs = dict(hdrs[:2]), dict(hdrs[2:])
        # for some reasons, `set` headers change their name
        #   while `add` headers do not
        self.assertEqual(shdrs["Unencoded1"], "€")
        self.assertEqual(ahdrs["unencoded2"], "€")
        self.assertEqual(shdrs["Content-Disposition"],
                         "a; p=?; p*=utf-8''%E2%82%AC")
        self.assertEqual(ahdrs["content-disposition"],
                         "a2; p2=?; p2*=utf-8''%E2%82%AC")
        self.assertEqual(ahdrs["bytes"], "abc")


class MakeDispositionHeaderTests(unittest.TestCase):

    def test_ascii(self):
        self.assertEqual(
            make_content_disposition('inline', 'iq.png'),
            'inline; filename="iq.png"')

    def test_latin_one(self):
        self.assertEqual(
            make_content_disposition('inline', 'Dänemark.png'),
            'inline; filename="b\'Dnemark.png\'"; filename*=UTF-8\'\'D%C3%A4nemark.png'  # noqa: E501
        )

    def test_unicode(self):
        """HTTP headers need to be latin-1 compatible

        In order to offer file downloads which contain unicode file names,
        the file name has to be treated in a special way, see
        https://stackoverflow.com/questions/1361604 .
        """
        self.assertEqual(
            make_content_disposition('inline', 'ıq.png'),
            'inline; filename="b\'q.png\'"; filename*=UTF-8\'\'%C4%B1q.png'
        )


class TestHeaderEncodingRegistry(unittest.TestCase):
    def setUp(self):
        self._copy = header_encoding_registry.copy()

    def tearDown(self):
        header_encoding_registry.clear()
        header_encoding_registry.update(self._copy)

    def test_default_registrations(self):
        self.assertIn('content-type', header_encoding_registry)
        self.assertEqual(header_encoding_registry["content-disposition"],
                         (encode_params, {}))

    def test_encode(self):
        def encode(value, param):
            return param
        header_encoding_registry.register("my-header", encode, param=1)
        # non-ISO-8859-1 encoded
        self.assertEqual(header_encoding_registry.encode("my-header", "€"),
                         1)
        # ISO-8859-1 not encoded
        self.assertEqual(header_encoding_registry.encode("my-header", "ä"),
                         "ä")
        # unregistered not encoded
        self.assertEqual(header_encoding_registry.encode("my-header2", "€"),
                         "€")
        # test header name not case sensitive
        self.assertEqual(header_encoding_registry.encode("My-Header", "€"),
                         1)
        # default
        header_encoding_registry.register(None, encode, param=2)
        self.assertEqual(header_encoding_registry.encode("my-header2", "€"),
                         2)
        self.assertEqual(header_encoding_registry.encode("my-header", "€"),
                         1)

    def test_encode_words(self):
        self.assertIn(encode_words("ä"),
                      ("=?utf-8?b?w6Q=?=", "=?utf-8?q?=C3=A4?="))

    def test_encode_params(self):
        self.assertEqual(encode_params('abc; p1=1; p2="2"; p3="€"; p4=€; '
                                       'p5="€"; p5*=5'),
                         'abc; p1=1; p2="2"; p3="?"; p4=?; p5="?"; p5*=5; '
                         'p3*=utf-8\'\'%E2%82%AC; p4*=utf-8\'\'%E2%82%AC')

    def test_case_insensitivity(self):
        header_encoding_registry.register("HdR", lambda value: 0)
        # Note: case insensitivity not implemented for `dict` methods
        self.assertIn("hdr", header_encoding_registry)
        self.assertEqual(header_encoding_registry.encode("HDR", "€"), 0)
        header_encoding_registry.unregister("hDr")
        header_encoding_registry.unregister("hDr")  # no exception
        self.assertNotIn("hdr", header_encoding_registry)
