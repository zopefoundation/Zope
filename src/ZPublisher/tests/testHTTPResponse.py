# -*- coding: iso-8859-15 -*-

import unittest
import sys


class HTTPResponseTests(unittest.TestCase):

    _old_default_encoding = None

    def tearDown(self):
        if self._old_default_encoding is not None:
            self._setDefaultEncoding(self._old_default_encoding)

    def _setDefaultEncoding(self, value):
        from ZPublisher import HTTPResponse as module
        (module.default_encoding,
         self._old_default_encoding) = (value, module.default_encoding)

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
        self.assertEqual(response.body, '')
        self.assertEqual(response.cookies, {})
        self.assertTrue(response.stdout is sys.stdout)
        self.assertTrue(response.stderr is sys.stderr)

    def test_ctor_w_body(self):
        response = self._makeOne(body='ABC')
        self.assertEqual(response.body, 'ABC')

    def test_ctor_w_headers(self):
        response = self._makeOne(headers={'foo': 'bar'})
        self.assertEqual(response.headers, {'foo': 'bar',
                                           })

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
        from zExceptions import Unauthorized
        response = self._makeOne(status=Unauthorized)
        self.assertEqual(response.status, 401)
        self.assertEqual(response.errmsg, 'Unauthorized')
        self.assertEqual(response.headers, {})

    def test_ctor_charset_no_content_type_header(self):
        response = self._makeOne(body='foo')
        self.assertEqual(response.headers.get('content-type'),
                         'text/plain; charset=iso-8859-15')

    def test_ctor_charset_text_header_no_charset_defaults_latin1(self):
        response = self._makeOne(body='foo',
                                 headers={'content-type': 'text/plain'})
        self.assertEqual(response.headers.get('content-type'),
                         'text/plain; charset=iso-8859-15')

    def test_ctor_charset_application_header_no_header(self):
        response = self._makeOne(body='foo',
                                 headers={'content-type': 'application/foo'})
        self.assertEqual(response.headers.get('content-type'),
                         'application/foo')

    def test_ctor_charset_application_header_with_header(self):
        response = self._makeOne(body='foo',
                                 headers={'content-type':
                                        'application/foo; charset: something'})
        self.assertEqual(response.headers.get('content-type'),
                         'application/foo; charset: something')

    def test_ctor_charset_unicode_body_application_header(self):
        BODY = unicode('ärger', 'iso-8859-15')
        response = self._makeOne(body=BODY,
                                 headers={'content-type': 'application/foo'})
        self.assertEqual(response.headers.get('content-type'),
                         'application/foo; charset=iso-8859-15')
        self.assertEqual(response.body, 'ärger')

    def test_ctor_charset_unicode_body_application_header_diff_encoding(self):
        BODY = unicode('ärger', 'iso-8859-15')
        response = self._makeOne(body=BODY,
                                 headers={'content-type':
                                            'application/foo; charset=utf-8'})
        self.assertEqual(response.headers.get('content-type'),
                         'application/foo; charset=utf-8')
        # Body is re-encoded to match the header
        self.assertEqual(response.body, BODY.encode('utf-8'))

    def test_ctor_body_recodes_to_match_content_type_charset(self):
        xml = (u'<?xml version="1.0" encoding="iso-8859-15" ?>\n'
                '<foo><bar/></foo>')
        response = self._makeOne(body=xml, headers={'content-type':
                                            'text/xml; charset=utf-8'})
        self.assertEqual(response.body, xml.replace('iso-8859-15', 'utf-8'))

    def test_ctor_body_already_matches_charset_unchanged(self):
        xml = (u'<?xml version="1.0" encoding="iso-8859-15" ?>\n'
                '<foo><bar/></foo>')
        response = self._makeOne(body=xml, headers={'content-type':
                                            'text/xml; charset=iso-8859-15'})
        self.assertEqual(response.body, xml)

    def test_retry(self):
        STDOUT, STDERR = object(), object()
        response = self._makeOne(stdout=STDOUT, stderr=STDERR)
        cloned = response.retry()
        self.assertTrue(isinstance(cloned, self._getTargetClass()))
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
        from zExceptions import BadRequest
        response = self._makeOne()
        response.setStatus(BadRequest)
        self.assertEqual(response.status, 400)
        self.assertEqual(response.errmsg, 'Bad Request')

    def test_setStatus_Unauthorized_exception(self):
        from zExceptions import Unauthorized
        response = self._makeOne()
        response.setStatus(Unauthorized)
        self.assertEqual(response.status, 401)
        self.assertEqual(response.errmsg, 'Unauthorized')

    def test_setStatus_Forbidden_exception(self):
        from zExceptions import Forbidden
        response = self._makeOne()
        response.setStatus(Forbidden)
        self.assertEqual(response.status, 403)
        self.assertEqual(response.errmsg, 'Forbidden')

    def test_setStatus_NotFound_exception(self):
        from zExceptions import NotFound
        response = self._makeOne()
        response.setStatus(NotFound)
        self.assertEqual(response.status, 404)
        self.assertEqual(response.errmsg, 'Not Found')

    def test_setStatus_ResourceLockedError_exception(self):
        response = self._makeOne()
        from webdav.Lockable import ResourceLockedError
        response.setStatus(ResourceLockedError)
        self.assertEqual(response.status, 423)
        self.assertEqual(response.errmsg, 'Locked')

    def test_setStatus_InternalError_exception(self):
        from zExceptions import InternalError
        response = self._makeOne()
        response.setStatus(InternalError)
        self.assertEqual(response.status, 500)
        self.assertEqual(response.errmsg, 'Internal Server Error')

    def test_setCookie_no_existing(self):
        response = self._makeOne()
        response.setCookie('foo', 'bar')
        cookie = response.cookies.get('foo', None)
        self.assertEqual(len(cookie), 2)
        self.assertEqual(cookie.get('value'), 'bar')
        self.assertEqual(cookie.get('quoted'), True)

    def test_setCookie_w_existing(self):
        response = self._makeOne()
        response.setCookie('foo', 'bar')
        response.setCookie('foo', 'baz')
        cookie = response.cookies.get('foo', None)
        self.assertEqual(len(cookie), 2)
        self.assertEqual(cookie.get('value'), 'baz')
        self.assertEqual(cookie.get('quoted'), True)

    def test_setCookie_no_attrs(self):
        response = self._makeOne()
        response.setCookie('foo', 'bar')
        cookie = response.cookies.get('foo', None)
        self.assertEqual(len(cookie), 2)
        self.assertEqual(cookie.get('value'), 'bar')
        self.assertEqual(cookie.get('quoted'), True)
        cookies = response._cookie_list()
        self.assertEqual(len(cookies), 1)
        self.assertEqual(cookies[0], ('Set-Cookie', 'foo="bar"'))

    def test_setCookie_w_expires(self):
        EXPIRES = 'Wed, 31-Dec-97 23:59:59 GMT'
        response = self._makeOne()
        response.setCookie('foo', 'bar', expires=EXPIRES)
        cookie = response.cookies.get('foo', None)
        self.assertTrue(cookie)
        self.assertEqual(cookie.get('value'), 'bar')
        self.assertEqual(cookie.get('expires'), EXPIRES)
        self.assertEqual(cookie.get('quoted'), True)

        cookies = response._cookie_list()
        self.assertEqual(len(cookies), 1)
        self.assertEqual(cookies[0],
                         ('Set-Cookie', 'foo="bar"; Expires=%s' % EXPIRES))

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
                         ('Set-Cookie', 'foo="bar"; Domain=example.com'))

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
        self.assertEqual(cookies[0], ('Set-Cookie', 'foo="bar"; Path=/'))

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
        self.assertEqual(cookies[0],
                         ('Set-Cookie', 'foo="bar"; Comment=COMMENT'))

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
        self.assertEqual(cookies[0], ('Set-Cookie','foo="bar"; Secure'))

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
        self.assertEqual(cookies[0], ('Set-Cookie', 'foo="bar"'))

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
        self.assertEqual(cookie_list[0], ('Set-Cookie', 'foo="bar"; HTTPOnly'))

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
        self.assertEqual(cookie_list[0], ('Set-Cookie', 'foo="bar"'))

    def test_setCookie_unquoted(self):
        response = self._makeOne()
        response.setCookie('foo', 'bar', quoted=False)
        cookie = response.cookies.get('foo', None)
        self.assertEqual(len(cookie), 2)
        self.assertEqual(cookie.get('value'), 'bar')
        self.assertEqual(cookie.get('quoted'), False)

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
        self.assertEqual(cookie.get('path'), '/')

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
        self.assertEqual(cookie.get('expires'), 'Wed, 31-Dec-97 23:59:59 GMT')
        self.assertEqual(cookie.get('max_age'), 0)
        self.assertEqual(cookie.get('path'), '/')

    def test_expireCookie1160(self):
        # Verify that the cookie is expired even if an expires kw arg is passed
        # http://zope.org/Collectors/Zope/1160
        response = self._makeOne()
        response.expireCookie('foo', path='/',
                              expires='Mon, 22-Mar-2004 17:59 GMT', max_age=99)
        cookie = response.cookies.get('foo', None)
        self.assertTrue(cookie)
        self.assertEqual(cookie.get('expires'), 'Wed, 31-Dec-97 23:59:59 GMT')
        self.assertEqual(cookie.get('max_age'), 0)
        self.assertEqual(cookie.get('path'), '/')

    def test_getHeader_nonesuch(self):
        response = self._makeOne()
        self.assertEqual(response.getHeader('nonesuch'), None)

    def test_getHeader_existing(self):
        response = self._makeOne(headers={'foo': 'bar'})
        self.assertEqual(response.getHeader('foo'), 'bar')

    def test_getHeader_existing_not_literal(self):
        response = self._makeOne(headers={'foo': 'bar'})
        self.assertEqual(response.getHeader('Foo'), 'bar')

    def test_getHeader_existing_w_literal(self):
        response = self._makeOne(headers={'Foo': 'Bar'})
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

    def test_setHeader_Set_Cookie_special_case(self):
        # This is crazy, given that we have APIs for cookies.  Special
        # behavior will go away in Zope 2.13
        response = self._makeOne()
        response.setHeader('Set-Cookie', 'foo="bar"')
        self.assertEqual(response.getHeader('Set-Cookie'), None)
        self.assertEqual(response.accumulated_headers,
                         [('Set-Cookie', 'foo="bar"')])

    def test_setHeader_drops_CRLF_when_accumulating(self):
        # RFC2616 disallows CRLF in a header value.
        # This is crazy, given that we have APIs for cookies.  Special
        # behavior will go away in Zope 2.13
        response = self._makeOne()
        response.setHeader('Set-Cookie', 'allowed="OK"')
        response.setHeader('Set-Cookie',
                       'violation="http://www.ietf.org/rfc/\r\nrfc2616.txt"')
        self.assertEqual(response.accumulated_headers,
                        [('Set-Cookie', 'allowed="OK"'),
                         ('Set-Cookie',
                          'violation="http://www.ietf.org/rfc/rfc2616.txt"')])

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
        response.body = 'BLAHBLAH'
        response.insertBase()
        self.assertEqual(response.body, 'BLAHBLAH')
        self.assertEqual(response.getHeader('Content-Length'), '8')

    def test_insertBase_HTML_no_base_w_head_not_munged(self):
        HTML = '<html><head></head><body></body></html>'
        response = self._makeOne()
        response.setHeader('Content-Type', 'text/html')
        response.setHeader('Content-Length', len(HTML))
        response.body = HTML
        response.insertBase()
        self.assertEqual(response.body, HTML)
        self.assertEqual(response.getHeader('Content-Length'), str(len(HTML)))

    def test_insertBase_HTML_w_base_no_head_not_munged(self):
        HTML = '<html><body></body></html>'
        response = self._makeOne()
        response.setHeader('Content-Type', 'text/html')
        response.setHeader('Content-Length', len(HTML))
        response.body = HTML
        response.insertBase()
        self.assertEqual(response.body, HTML)
        self.assertEqual(response.getHeader('Content-Length'), str(len(HTML)))

    def test_insertBase_HTML_w_base_w_head_munged(self):
        HTML = '<html><head></head><body></body></html>'
        MUNGED = ('<html><head>\n'
                  '<base href="http://example.com/base/" />\n'
                  '</head><body></body></html>')
        response = self._makeOne()
        response.setHeader('Content-Type', 'text/html')
        response.setHeader('Content-Length', 8)
        response.body = HTML
        response.setBase('http://example.com/base/')
        response.insertBase()
        self.assertEqual(response.body, MUNGED)
        self.assertEqual(response.getHeader('Content-Length'),
                         str(len(MUNGED)))

    def test_setBody_w_locking(self):
        response = self._makeOne()
        response.setBody('BEFORE', lock=True)
        result = response.setBody('AFTER')
        self.assertFalse(result)
        self.assertEqual(response.body, 'BEFORE')

    def test_setBody_empty_unchanged(self):
        response = self._makeOne()
        response.body = 'BEFORE'
        result = response.setBody('')
        self.assertTrue(result)
        self.assertEqual(response.body, 'BEFORE')
        self.assertEqual(response.getHeader('Content-Type'), None)
        self.assertEqual(response.getHeader('Content-Length'), None)

    def test_setBody_2_tuple_wo_is_error_converted_to_HTML(self):
        EXPECTED = ("<html>\n"
                    "<head>\n<title>TITLE</title>\n</head>\n"
                    "<body>\nBODY\n</body>\n"
                    "</html>\n")
        response = self._makeOne()
        response.body = 'BEFORE'
        result = response.setBody(('TITLE', 'BODY'))
        self.assertTrue(result)
        self.assertEqual(response.body, EXPECTED)
        self.assertEqual(response.getHeader('Content-Type'),
                         'text/html; charset=iso-8859-15')
        self.assertEqual(response.getHeader('Content-Length'),
                         str(len(EXPECTED)))

    def test_setBody_2_tuple_w_is_error_converted_to_Site_Error(self):
        response = self._makeOne()
        response.body = 'BEFORE'
        result = response.setBody(('TITLE', 'BODY'), is_error=True)
        self.assertTrue(result)
        self.assertFalse('BEFORE' in response.body)
        self.assertTrue('<h2>Site Error</h2>' in response.body)
        self.assertTrue('TITLE' in response.body)
        self.assertTrue('BODY' in response.body)
        self.assertEqual(response.getHeader('Content-Type'),
                         'text/html; charset=iso-8859-15')

    def test_setBody_string_not_HTML(self):
        response = self._makeOne()
        result = response.setBody('BODY')
        self.assertTrue(result)
        self.assertEqual(response.body, 'BODY')
        self.assertEqual(response.getHeader('Content-Type'),
                         'text/plain; charset=iso-8859-15')
        self.assertEqual(response.getHeader('Content-Length'), '4')

    def test_setBody_string_HTML(self):
        HTML = '<html><head></head><body></body></html>'
        response = self._makeOne()
        result = response.setBody(HTML)
        self.assertTrue(result)
        self.assertEqual(response.body, HTML)
        self.assertEqual(response.getHeader('Content-Type'),
                         'text/html; charset=iso-8859-15')
        self.assertEqual(response.getHeader('Content-Length'), str(len(HTML)))

    def test_setBody_object_with_asHTML(self):
        HTML = '<html><head></head><body></body></html>'
        class Dummy:
            def asHTML(self):
                return HTML
        response = self._makeOne()
        result = response.setBody(Dummy())
        self.assertTrue(result)
        self.assertEqual(response.body, HTML)
        self.assertEqual(response.getHeader('Content-Type'),
                         'text/html; charset=iso-8859-15')
        self.assertEqual(response.getHeader('Content-Length'), str(len(HTML)))

    def test_setBody_object_with_unicode(self):
        HTML = u'<html><head></head><body><h1>Tr\u0039s Bien</h1></body></html>'
        ENCODED = HTML.encode('iso-8859-15')
        response = self._makeOne()
        result = response.setBody(HTML)
        self.assertTrue(result)
        self.assertEqual(response.body, ENCODED)
        self.assertEqual(response.getHeader('Content-Type'),
                         'text/html; charset=iso-8859-15')
        self.assertEqual(response.getHeader('Content-Length'),
                         str(len(ENCODED)))

    def test_setBody_w_bogus_pseudo_HTML(self):
        # The 2001 checkin message which added the path-under-test says:
        # (r19315): "merged content type on error fixes from 2.3
        # If the str of the object returs a Python "pointer" looking mess,
        # don't let it get treated as HTML.
        from ZPublisher import NotFound
        BOGUS = '<Bogus a39d53d>'
        response = self._makeOne()
        self.assertRaises(NotFound, response.setBody, BOGUS)

    def test_setBody_html_no_charset_escapes_latin1_gt_lt(self):
        response = self._makeOne()
        BEFORE = ('<html><head></head><body><p>LT: \213</p>'
                  '<p>GT: \233</p></body></html>')
        AFTER = ('<html><head></head><body><p>LT: &lt;</p>'
                  '<p>GT: &gt;</p></body></html>')
        response.setHeader('Content-Type', 'text/html')
        result = response.setBody(BEFORE)
        self.assertTrue(result)
        self.assertEqual(response.body, AFTER)
        self.assertEqual(response.getHeader('Content-Length'), str(len(AFTER)))

    def test_setBody_latin_alias_escapes_latin1_gt_lt(self):
        response = self._makeOne()
        BEFORE = ('<html><head></head><body><p>LT: \213</p>'
                  '<p>GT: \233</p></body></html>')
        AFTER = ('<html><head></head><body><p>LT: &lt;</p>'
                  '<p>GT: &gt;</p></body></html>')
        response.setHeader('Content-Type', 'text/html; charset=latin1')
        result = response.setBody(BEFORE)
        self.assertTrue(result)
        self.assertEqual(response.body, AFTER)
        self.assertEqual(response.getHeader('Content-Length'), str(len(AFTER)))

    def test_setBody_calls_insertBase(self):
        response = self._makeOne()
        lamb = {}
        def _insertBase():
            lamb['flavor'] = 'CURRY'
        response.insertBase = _insertBase
        response.setBody('Garlic Naan')
        self.assertEqual(lamb['flavor'], 'CURRY')

    #def test_setBody_w_HTTP_content_compression(self):

    def test_setBody_compression_uncompressible_mimetype(self):
        BEFORE = 'foo' * 100 # body must get smaller on compression
        response = self._makeOne()
        response.setHeader('Content-Type', 'image/jpeg')
        response.enableHTTPCompression({'HTTP_ACCEPT_ENCODING': 'gzip'})
        response.setBody(BEFORE)
        self.assertFalse(response.getHeader('Content-Encoding'))
        self.assertEqual(response.body, BEFORE)

    def test_setBody_compression_existing_encoding(self):
        BEFORE = 'foo' * 100 # body must get smaller on compression
        response = self._makeOne()
        response.setHeader('Content-Encoding', 'piglatin')
        response.enableHTTPCompression({'HTTP_ACCEPT_ENCODING': 'gzip'})
        response.setBody(BEFORE)
        self.assertEqual(response.getHeader('Content-Encoding'), 'piglatin')
        self.assertEqual(response.body, BEFORE)

    def test_setBody_compression_too_short_to_gzip(self):
        BEFORE = 'foo' # body must get smaller on compression
        response = self._makeOne()
        response.enableHTTPCompression({'HTTP_ACCEPT_ENCODING': 'gzip'})
        response.setBody(BEFORE)
        self.assertFalse(response.getHeader('Content-Encoding'))
        self.assertEqual(response.body, BEFORE)

    def test_setBody_compression_no_prior_vary_header(self):
        # Vary header should be added here
        response = self._makeOne()
        response.enableHTTPCompression({'HTTP_ACCEPT_ENCODING': 'gzip'})
        response.setBody('foo' * 100) # body must get smaller on compression
        self.assertTrue('Accept-Encoding' in response.getHeader('Vary'))

    def test_setBody_compression_w_prior_vary_header_wo_encoding(self):
        # Vary header should be added here
        response = self._makeOne()
        response.setHeader('Vary', 'Cookie')
        response.enableHTTPCompression({'HTTP_ACCEPT_ENCODING': 'gzip'})
        response.setBody('foo' * 100) # body must get smaller on compression
        self.assertTrue('Accept-Encoding' in response.getHeader('Vary'))

    def test_setBody_compression_w_prior_vary_header_incl_encoding(self):
        # Vary header already had Accept-Ecoding', do'nt munge
        PRIOR = 'Accept-Encoding,Accept-Language'
        response = self._makeOne()
        response.enableHTTPCompression({'HTTP_ACCEPT_ENCODING': 'gzip'})
        response.setHeader('Vary', PRIOR)
        response.setBody('foo'*100)
        self.assertEqual(response.getHeader('Vary'), PRIOR)

    def test_setBody_compression_no_prior_vary_header_but_forced(self):
        # Compression forced, don't add a Vary entry for compression.
        response = self._makeOne()
        response.enableHTTPCompression({'HTTP_ACCEPT_ENCODING': 'gzip'},
                                       force=True)
        response.setBody('foo' * 100) # body must get smaller on compression
        self.assertEqual(response.getHeader('Vary'), None)

    def test_redirect_defaults(self):
        URL = 'http://example.com'
        response = self._makeOne()
        result = response.redirect(URL)
        self.assertEqual(result, URL)
        self.assertEqual(response.status, 302)
        self.assertEqual(response.getHeader('Location'), URL)
        self.assertFalse(response._locked_status)

    def test_redirect_explicit_status(self):
        URL = 'http://example.com'
        response = self._makeOne()
        result = response.redirect(URL, status=307)
        self.assertEqual(response.status, 307)
        self.assertEqual(response.getHeader('Location'), URL)
        self.assertFalse(response._locked_status)

    def test_redirect_w_lock(self):
        URL = 'http://example.com'
        response = self._makeOne()
        result = response.redirect(URL, lock=True)
        self.assertEqual(response.status, 302)
        self.assertEqual(response.getHeader('Location'), URL)
        self.assertTrue(response._locked_status)

    def test__encode_unicode_no_content_type_uses_default_encoding(self):
        self._setDefaultEncoding('UTF8')
        UNICODE = u'<h1>Tr\u0039s Bien</h1>'
        response = self._makeOne()
        self.assertEqual(response._encode_unicode(UNICODE),
                         UNICODE.encode('UTF8'))

    def test__encode_unicode_w_content_type_no_charset_updates_charset(self):
        self._setDefaultEncoding('UTF8')
        UNICODE = u'<h1>Tr\u0039s Bien</h1>'
        response = self._makeOne()
        response.setHeader('Content-Type', 'text/html')
        self.assertEqual(response._encode_unicode(UNICODE),
                         UNICODE.encode('UTF8'))
        response.getHeader('Content-Type', 'text/html; charset=UTF8')

    def test__encode_unicode_w_content_type_w_charset(self):
        self._setDefaultEncoding('UTF8')
        UNICODE = u'<h1>Tr\u0039s Bien</h1>'
        response = self._makeOne()
        response.setHeader('Content-Type', 'text/html; charset=latin1')
        self.assertEqual(response._encode_unicode(UNICODE),
                         UNICODE.encode('latin1'))
        response.getHeader('Content-Type', 'text/html; charset=latin1')

    def test__encode_unicode_w_content_type_w_charset_xml_preamble(self):
        self._setDefaultEncoding('UTF8')
        PREAMBLE = u'<?xml version="1.0" ?>'
        ELEMENT = u'<element>Tr\u0039s Bien</element>'
        UNICODE = u'\n'.join([PREAMBLE, ELEMENT])
        response = self._makeOne()
        response.setHeader('Content-Type', 'text/html; charset=latin1')
        self.assertEqual(response._encode_unicode(UNICODE),
                         '<?xml version="1.0" encoding="latin1" ?>\n'
                         + ELEMENT.encode('latin1'))
        response.getHeader('Content-Type', 'text/html; charset=latin1')

    def test_quoteHTML(self):
        BEFORE = '<p>This is a story about a boy named "Sue"</p>'
        AFTER = ('&lt;p&gt;This is a story about a boy named '
                 '&quot;Sue&quot;&lt;/p&gt;')
        response = self._makeOne()
        self.assertEqual(response.quoteHTML(BEFORE), AFTER)

    def test_notFoundError(self):
        from ZPublisher import NotFound
        response = self._makeOne()
        try:
            response.notFoundError()
        except NotFound, raised:
            self.assertEqual(response.status, 404)
            self.assertTrue("<p><b>Resource:</b> Unknown</p>" in str(raised))
        else:
            self.fail("Didn't raise NotFound")

    def test_notFoundError_w_entry(self):
        from ZPublisher import NotFound
        response = self._makeOne()
        try:
            response.notFoundError('ENTRY')
        except NotFound, raised:
            self.assertEqual(response.status, 404)
            self.assertTrue("<p><b>Resource:</b> ENTRY</p>" in str(raised))
        else:
            self.fail("Didn't raise NotFound")

    def test_forbiddenError(self):
        from ZPublisher import NotFound
        response = self._makeOne()
        try:
            response.forbiddenError()
        except NotFound, raised:
            self.assertEqual(response.status, 404)
            self.assertTrue("<p><b>Resource:</b> Unknown</p>" in str(raised))
        else:
            self.fail("Didn't raise NotFound")

    def test_forbiddenError_w_entry(self):
        from ZPublisher import NotFound
        response = self._makeOne()
        try:
            response.forbiddenError('ENTRY')
        except NotFound, raised:
            self.assertEqual(response.status, 404)
            self.assertTrue("<p><b>Resource:</b> ENTRY</p>" in str(raised))
        else:
            self.fail("Didn't raise NotFound")

    def test_debugError(self):
        from ZPublisher import NotFound
        response = self._makeOne()
        try:
            response.debugError('testing')
        except NotFound, raised:
            self.assertEqual(response.status, 200)
            self.assertTrue("Zope has encountered a problem publishing "
                            "your object.<p>\ntesting</p>" in str(raised))
        else:
            self.fail("Didn't raise NotFound")

    def test_badRequestError_valid_parameter_name(self):
        from ZPublisher import BadRequest
        response = self._makeOne()
        try:
            response.badRequestError('some_parameter')
        except BadRequest, raised:
            self.assertEqual(response.status, 400)
            self.assertTrue("The parameter, <em>some_parameter</em>, "
                            "was omitted from the request." in str(raised))
        else:
            self.fail("Didn't raise BadRequest")

    def test_badRequestError_invalid_parameter_name(self):
        from ZPublisher import InternalError
        response = self._makeOne()
        try:
            response.badRequestError('URL1')
        except InternalError, raised:
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
        self.assertTrue('WWW-Authenticate' in response.headers) #literal
        self.assertEqual(response.headers['WWW-Authenticate'],
                         'basic realm="Zope"')

    def test__unauthorized_w_realm(self):
        response = self._makeOne()
        response.realm = 'Folly'
        response._unauthorized()
        self.assertTrue('WWW-Authenticate' in response.headers) #literal
        self.assertEqual(response.headers['WWW-Authenticate'],
                         'basic realm="Folly"')

    def test_unauthorized_no_debug_mode(self):
        from zExceptions import Unauthorized
        response = self._makeOne()
        try:
            response.unauthorized()
        except Unauthorized, raised:
            self.assertEqual(response.status, 200) # publisher sets 401 later
            self.assertTrue("You are not authorized "
                            "to access this resource." in str(raised))
        else:
            self.fail("Didn't raise Unauthorized")

    def test_unauthorized_w_debug_mode_no_credentials(self):
        from zExceptions import Unauthorized
        response = self._makeOne()
        response.debug_mode = True
        try:
            response.unauthorized()
        except Unauthorized, raised:
            self.assertTrue("\nNo Authorization header found."
                            in str(raised))
        else:
            self.fail("Didn't raise Unauthorized")

    def test_unauthorized_w_debug_mode_w_credentials(self):
        from zExceptions import Unauthorized
        response = self._makeOne()
        response.debug_mode = True
        response._auth = 'bogus'
        try:
            response.unauthorized()
        except Unauthorized, raised:
            self.assertTrue("\nUsername and password are not correct."
                            in str(raised))
        else:
            self.fail("Didn't raise Unauthorized")

    def test_finalize_empty(self):
        response = self._makeOne()
        status, headers = response.finalize()
        self.assertEqual(status, '200 OK')
        self.assertEqual(headers,
                         [('X-Powered-By', 'Zope (www.zope.org), '
                                           'Python (www.python.org)'),
                          ('Content-Length', '0'),
                         ])

    def test_finalize_w_body(self):
        response = self._makeOne()
        response.body = 'TEST'
        status, headers = response.finalize()
        self.assertEqual(status, '200 OK')
        self.assertEqual(headers,
                         [('X-Powered-By', 'Zope (www.zope.org), '
                                           'Python (www.python.org)'),
                          ('Content-Length', '4'),
                         ])

    def test_finalize_w_existing_content_length(self):
        response = self._makeOne()
        response.setHeader('Content-Length', '42')
        status, headers = response.finalize()
        self.assertEqual(status, '200 OK')
        self.assertEqual(headers,
                         [('X-Powered-By', 'Zope (www.zope.org), '
                                           'Python (www.python.org)'),
                          ('Content-Length', '42'),
                         ])

    def test_finalize_w_transfer_encoding(self):
        response = self._makeOne()
        response.setHeader('Transfer-Encoding', 'slurry')
        status, headers = response.finalize()
        self.assertEqual(status, '200 OK')
        self.assertEqual(headers,
                         [('X-Powered-By', 'Zope (www.zope.org), '
                                           'Python (www.python.org)'),
                          ('Transfer-Encoding', 'slurry'),
                         ])

    def test_finalize_after_redirect(self):
        response = self._makeOne()
        response.redirect('http://example.com/')
        status, headers = response.finalize()
        self.assertEqual(status, '302 Moved Temporarily')
        self.assertEqual(headers,
                         [('X-Powered-By', 'Zope (www.zope.org), '
                                           'Python (www.python.org)'),
                          ('Content-Length', '0'),
                          ('Location', 'http://example.com/'),
                         ])

    def test_listHeaders_empty(self):
        response = self._makeOne()
        headers = response.listHeaders()
        self.assertEqual(headers,
                         [('X-Powered-By', 'Zope (www.zope.org), '
                                           'Python (www.python.org)'),
                         ])

    def test_listHeaders_already_wrote(self):
        # listHeaders doesn't do the short-circuit on _wrote.
        response = self._makeOne()
        response._wrote = True
        headers = response.listHeaders()
        self.assertEqual(headers,
                         [('X-Powered-By', 'Zope (www.zope.org), '
                                           'Python (www.python.org)'),
                         ])

    def test_listHeaders_existing_content_length(self):
        response = self._makeOne()
        response.setHeader('Content-Length', 42)
        headers = response.listHeaders()
        self.assertEqual(headers,
                         [('X-Powered-By', 'Zope (www.zope.org), '
                                           'Python (www.python.org)'),
                          ('Content-Length', '42'),
                         ])

    def test_listHeaders_existing_transfer_encoding(self):
        # If 'Transfer-Encoding' is set, don't force 'Content-Length'.
        response = self._makeOne()
        response.setHeader('Transfer-Encoding', 'slurry')
        headers = response.listHeaders()
        self.assertEqual(headers,
                         [('X-Powered-By', 'Zope (www.zope.org), '
                                           'Python (www.python.org)'),
                          ('Transfer-Encoding', 'slurry'),
                         ])

    def test_listHeaders_after_setHeader(self):
        response = self._makeOne()
        response.setHeader('x-consistency', 'Foolish')
        headers = response.listHeaders()
        self.assertEqual(headers,
                         [('X-Powered-By', 'Zope (www.zope.org), '
                                           'Python (www.python.org)'),
                          ('X-Consistency', 'Foolish'),
                         ])

    def test_listHeaders_after_setHeader_literal(self):
        response = self._makeOne()
        response.setHeader('X-consistency', 'Foolish', literal=True)
        headers = response.listHeaders()
        self.assertEqual(headers,
                         [('X-Powered-By', 'Zope (www.zope.org), '
                                           'Python (www.python.org)'),
                          ('X-consistency', 'Foolish'),
                         ])

    def test_listHeaders_after_redirect(self):
        response = self._makeOne()
        response.redirect('http://example.com/')
        headers = response.listHeaders()
        self.assertEqual(headers,
                         [('X-Powered-By', 'Zope (www.zope.org), '
                                           'Python (www.python.org)'),
                          ('Location', 'http://example.com/'),
                         ])

    def test_listHeaders_after_setCookie_appendCookie(self):
        response = self._makeOne()
        response.setCookie('foo', 'bar', path='/')
        response.appendCookie('foo', 'baz')
        headers = response.listHeaders()
        self.assertEqual(headers,
                         [('X-Powered-By', 'Zope (www.zope.org), '
                                           'Python (www.python.org)'),
                          ('Set-Cookie', 'foo="bar%3Abaz"; Path=/'),
                         ])

    def test_listHeaders_after_expireCookie(self):
        response = self._makeOne()
        response.expireCookie('qux', path='/')
        headers = response.listHeaders()
        self.assertEqual(headers,
                         [('X-Powered-By', 'Zope (www.zope.org), '
                                           'Python (www.python.org)'),
                          ('Set-Cookie', 'qux="deleted"; '
                                         'Path=/; '
                                         'Expires=Wed, 31-Dec-97 23:59:59 GMT; '
                                         'Max-Age=0'),
                         ])

    def test_listHeaders_after_addHeader(self):
        response = self._makeOne()
        response.addHeader('X-Consistency', 'Foolish')
        response.addHeader('X-Consistency', 'Oatmeal')
        headers = response.listHeaders()
        self.assertEqual(headers,
                         [('X-Powered-By', 'Zope (www.zope.org), '
                                           'Python (www.python.org)'),
                          ('X-Consistency', 'Foolish'),
                          ('X-Consistency', 'Oatmeal'),
                         ])

    def test_listHeaders_w_body(self):
        response = self._makeOne()
        response.setBody('BLAH')
        headers = response.listHeaders()
        self.assertEqual(headers,
                         [('X-Powered-By', 'Zope (www.zope.org), '
                                           'Python (www.python.org)'),
                          ('Content-Length', '4'),
                          ('Content-Type', 'text/plain; charset=iso-8859-15'),
                         ])

    def test___str__already_wrote(self):
        response = self._makeOne()
        response._wrote = True
        self.assertEqual(str(response), '')

    def test___str__empty(self):
        response = self._makeOne()
        result = str(response)
        lines = result.split('\r\n')
        self.assertEqual(len(lines), 5)
        self.assertEqual(lines[0], 'Status: 200 OK')
        self.assertEqual(lines[1], 'X-Powered-By: Zope (www.zope.org), '
                                   'Python (www.python.org)')
        self.assertEqual(lines[2], 'Content-Length: 0')
        self.assertEqual(lines[3], '')
        self.assertEqual(lines[4], '')

    def test___str__existing_content_length(self):
        # The application can break clients by setting a bogus length;  we
        # don't do anything to stop that.
        response = self._makeOne()
        response.setHeader('Content-Length', 42)
        result = str(response)
        lines = result.split('\r\n')
        self.assertEqual(len(lines), 5)
        self.assertEqual(lines[0], 'Status: 200 OK')
        self.assertEqual(lines[1], 'X-Powered-By: Zope (www.zope.org), '
                                   'Python (www.python.org)')
        self.assertEqual(lines[2], 'Content-Length: 42')
        self.assertEqual(lines[3], '')
        self.assertEqual(lines[4], '')

    def test___str__existing_transfer_encoding(self):
        # If 'Transfer-Encoding' is set, don't force 'Content-Length'.
        response = self._makeOne()
        response.setHeader('Transfer-Encoding', 'slurry')
        result = str(response)
        lines = result.split('\r\n')
        self.assertEqual(len(lines), 5)
        self.assertEqual(lines[0], 'Status: 200 OK')
        self.assertEqual(lines[1], 'X-Powered-By: Zope (www.zope.org), '
                                   'Python (www.python.org)')
        self.assertEqual(lines[2], 'Transfer-Encoding: slurry')
        self.assertEqual(lines[3], '')
        self.assertEqual(lines[4], '')

    def test___str__after_setHeader(self):
        response = self._makeOne()
        response.setHeader('x-consistency', 'Foolish')
        result = str(response)
        lines = result.split('\r\n')
        self.assertEqual(len(lines), 6)
        self.assertEqual(lines[0], 'Status: 200 OK')
        self.assertEqual(lines[1], 'X-Powered-By: Zope (www.zope.org), '
                                   'Python (www.python.org)')
        self.assertEqual(lines[2], 'Content-Length: 0')
        self.assertEqual(lines[3], 'X-Consistency: Foolish')
        self.assertEqual(lines[4], '')
        self.assertEqual(lines[5], '')

    def test___str__after_setHeader_literal(self):
        response = self._makeOne()
        response.setHeader('X-consistency', 'Foolish', literal=True)
        result = str(response)
        lines = result.split('\r\n')
        self.assertEqual(len(lines), 6)
        self.assertEqual(lines[0], 'Status: 200 OK')
        self.assertEqual(lines[1], 'X-Powered-By: Zope (www.zope.org), '
                                   'Python (www.python.org)')
        self.assertEqual(lines[2], 'Content-Length: 0')
        self.assertEqual(lines[3], 'X-consistency: Foolish')
        self.assertEqual(lines[4], '')
        self.assertEqual(lines[5], '')

    def test___str__after_redirect(self):
        response = self._makeOne()
        response.redirect('http://example.com/')
        result = str(response)
        lines = result.split('\r\n')
        self.assertEqual(len(lines), 6)
        self.assertEqual(lines[0], 'Status: 302 Moved Temporarily')
        self.assertEqual(lines[1], 'X-Powered-By: Zope (www.zope.org), '
                                   'Python (www.python.org)')
        self.assertEqual(lines[2], 'Content-Length: 0')
        self.assertEqual(lines[3], 'Location: http://example.com/')
        self.assertEqual(lines[4], '')
        self.assertEqual(lines[5], '')

    def test___str__after_setCookie_appendCookie(self):
        response = self._makeOne()
        response.setCookie('foo', 'bar', path='/')
        response.appendCookie('foo', 'baz')
        result = str(response)
        lines = result.split('\r\n')
        self.assertEqual(len(lines), 6)
        self.assertEqual(lines[0], 'Status: 200 OK')
        self.assertEqual(lines[1], 'X-Powered-By: Zope (www.zope.org), '
                                   'Python (www.python.org)')
        self.assertEqual(lines[2], 'Content-Length: 0')
        self.assertEqual(lines[3], 'Set-Cookie: foo="bar%3Abaz"; '
                                   'Path=/')
        self.assertEqual(lines[4], '')
        self.assertEqual(lines[5], '')

    def test___str__after_expireCookie(self):
        response = self._makeOne()
        response.expireCookie('qux', path='/')
        result = str(response)
        lines = result.split('\r\n')
        self.assertEqual(len(lines), 6)
        self.assertEqual(lines[0], 'Status: 200 OK')
        self.assertEqual(lines[1], 'X-Powered-By: Zope (www.zope.org), '
                                   'Python (www.python.org)')
        self.assertEqual(lines[2], 'Content-Length: 0')
        self.assertEqual(lines[3], 'Set-Cookie: qux="deleted"; '
                                   'Path=/; '
                                   'Expires=Wed, 31-Dec-97 23:59:59 GMT; '
                                   'Max-Age=0')
        self.assertEqual(lines[4], '')
        self.assertEqual(lines[5], '')

    def test___str__after_addHeader(self):
        response = self._makeOne()
        response.addHeader('X-Consistency', 'Foolish')
        response.addHeader('X-Consistency', 'Oatmeal')
        result = str(response)
        lines = result.split('\r\n')
        self.assertEqual(len(lines), 7)
        self.assertEqual(lines[0], 'Status: 200 OK')
        self.assertEqual(lines[1], 'X-Powered-By: Zope (www.zope.org), '
                                   'Python (www.python.org)')
        self.assertEqual(lines[2], 'Content-Length: 0')
        self.assertEqual(lines[3], 'X-Consistency: Foolish')
        self.assertEqual(lines[4], 'X-Consistency: Oatmeal')
        self.assertEqual(lines[5], '')
        self.assertEqual(lines[6], '')

    def test___str__w_body(self):
        response = self._makeOne()
        response.setBody('BLAH')
        result = str(response)
        lines = result.split('\r\n')
        self.assertEqual(len(lines), 6)
        self.assertEqual(lines[0], 'Status: 200 OK')
        self.assertEqual(lines[1], 'X-Powered-By: Zope (www.zope.org), '
                                   'Python (www.python.org)')
        self.assertEqual(lines[2], 'Content-Length: 4')
        self.assertEqual(lines[3],
                         'Content-Type: text/plain; charset=iso-8859-15')
        self.assertEqual(lines[4], '')
        self.assertEqual(lines[5], 'BLAH')

    def test_write_already_wrote(self):
        from StringIO import StringIO
        stdout = StringIO()
        response = self._makeOne(stdout=stdout)
        response.write('Kilroy was here!')
        self.assertTrue(response._wrote)
        lines = stdout.getvalue().split('\r\n')
        self.assertEqual(len(lines), 5)
        self.assertEqual(lines[0], 'Status: 200 OK')
        self.assertEqual(lines[1], 'X-Powered-By: Zope (www.zope.org), '
                                   'Python (www.python.org)')
        self.assertEqual(lines[2], 'Content-Length: 0')
        self.assertEqual(lines[3], '')
        self.assertEqual(lines[4], 'Kilroy was here!')

    def test_write_not_already_wrote(self):
        from StringIO import StringIO
        stdout = StringIO()
        response = self._makeOne(stdout=stdout)
        response._wrote = True
        response.write('Kilroy was here!')
        lines = stdout.getvalue().split('\r\n')
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0], 'Kilroy was here!')

    def test__setBCIHeaders(self):
        response = self._makeOne()
        try:
            raise AttributeError('ERROR VALUE')
        except AttributeError:
            t, v, tb = sys.exc_info()
            response._setBCIHeaders(t, tb)
            # required by Bobo Call Interface (BCI)
            self.assertEqual(response.headers['bobo-exception-type'],
                             "<type 'exceptions.AttributeError'>")
            self.assertEqual(response.headers['bobo-exception-value'],
                             'See the server error log for details')
            self.assertTrue('bobo-exception-file' in response.headers)
            self.assertTrue('bobo-exception-line' in response.headers)
        finally:
            del tb

    def test_exception_Internal_Server_Error(self):
        response = self._makeOne()
        try:
            raise AttributeError('ERROR VALUE')
        except AttributeError:
            body = response.exception()
            self.assertTrue('ERROR VALUE' in str(body))
            self.assertEqual(response.status, 500)
            self.assertEqual(response.errmsg, 'Internal Server Error')
            # required by Bobo Call Interface (BCI)
            self.assertEqual(response.headers['bobo-exception-type'],
                             "<type 'exceptions.AttributeError'>")
            self.assertEqual(response.headers['bobo-exception-value'],
                             'See the server error log for details')
            self.assertTrue('bobo-exception-file' in response.headers)
            self.assertTrue('bobo-exception-line' in response.headers)

    #TODO
    # def test_exception_* WAAAAAA!


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(HTTPResponseTests, 'test'))
    return suite
