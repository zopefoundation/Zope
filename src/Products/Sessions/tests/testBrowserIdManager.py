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
Test suite for session id manager.
"""
import unittest

class TestBrowserIdManager(unittest.TestCase):

    def _getTargetClass(self):
        from Products.Sessions.BrowserIdManager import BrowserIdManager
        return BrowserIdManager

    def _makeOne(self, request=None, name='browser_id_manager'):
        bid = self._getTargetClass()(name)
        if request is not None:
            bid.REQUEST = request
        return bid

    def test_hasBrowserId_already_set_on_request_invalid(self):
        request = DummyRequest(browser_id_='xxx')
        mgr = self._makeOne(request)
        self.failIf(mgr.hasBrowserId())

    def test_hasBrowserId_already_set_on_request(self):
        from Products.Sessions.BrowserIdManager import getNewBrowserId
        request = DummyRequest(browser_id_=getNewBrowserId())
        mgr = self._makeOne(request)
        self.failUnless(mgr.hasBrowserId())

    def test_hasBrowserId_namespace_hit(self):
        from Products.Sessions.BrowserIdManager import getNewBrowserId
        request = DummyRequest(cookies={'bid': getNewBrowserId()})
        mgr = self._makeOne(request)
        mgr.setBrowserIdName('bid')
        self.failUnless(mgr.hasBrowserId())

    def test_hasBrowserId_namespace_miss(self):
        request = DummyRequest()
        mgr = self._makeOne(request)
        self.failIf(mgr.hasBrowserId())
        self.assertRaises(AttributeError, getattr, request, 'browser_id_')
        self.assertRaises(AttributeError, getattr, request, 'browser_id_ns_')

    def test_getBrowserId_already_set_on_request_invalid_raises(self):
        request = DummyRequest(browser_id_='xxx')
        mgr = self._makeOne(request)
        self.assertRaises(ValueError, mgr.getBrowserId)

    def test_getBrowserId_already_set_on_request(self):
        from Products.Sessions.BrowserIdManager import getNewBrowserId
        bid = getNewBrowserId()
        request = DummyRequest(browser_id_=bid)
        mgr = self._makeOne(request)
        self.assertEqual(mgr.getBrowserId(), bid)

    def test_getBrowserId_namespace_hit(self):
        from Products.Sessions.BrowserIdManager import getNewBrowserId
        bid = getNewBrowserId()
        request = DummyRequest(cookies={'bid': bid})
        mgr = self._makeOne(request)
        mgr.setBrowserIdName('bid')
        self.failUnless(mgr.hasBrowserId())
        self.assertEqual(request.browser_id_, bid)
        self.assertEqual(request.browser_id_ns_, 'cookies')

    def test_getBrowserId_namespace_miss_no_create(self):
        request = DummyRequest()
        mgr = self._makeOne(request)
        mgr.setBrowserIdName('bid')
        self.assertEqual(mgr.getBrowserId(create=False), None)
        self.assertRaises(AttributeError, getattr, request, 'browser_id_')
        self.assertRaises(AttributeError, getattr, request, 'browser_id_ns_')

    def test_getBrowserId_namespace_miss_w_create_no_cookies(self):
        from Products.Sessions.BrowserIdManager import isAWellFormedBrowserId
        request = DummyRequest()
        mgr = self._makeOne(request)
        mgr.setBrowserIdName('bid')
        mgr.setBrowserIdNamespaces(())
        bid = mgr.getBrowserId()
        self.failUnless(isAWellFormedBrowserId(bid))
        self.assertEqual(request.browser_id_, bid)
        self.assertEqual(request.browser_id_ns_, None)

    def test_getBrowserId_namespace_miss_w_create_w_cookies(self):
        from Products.Sessions.BrowserIdManager import isAWellFormedBrowserId
        response = DummyResponse(cookies={})
        request = DummyRequest(RESPONSE=response)
        mgr = self._makeOne(request)
        mgr.setBrowserIdName('bid')
        mgr.setBrowserIdNamespaces(('cookies',))
        bid = mgr.getBrowserId()
        self.failUnless(isAWellFormedBrowserId(bid))
        self.assertEqual(request.browser_id_, bid)
        self.assertEqual(request.browser_id_ns_, None)
        self.assertEqual(response.cookies['bid'], {'path': '/', 'value': bid})

    def test_isBrowserIdNew_nonesuch_raises(self):
        request = DummyRequest()
        mgr = self._makeOne(request)
        self.assertRaises(ValueError, mgr.isBrowserIdNew)

    def test_isBrowserIdNew_no_ns(self):
        from Products.Sessions.BrowserIdManager import getNewBrowserId
        bid = getNewBrowserId()
        request = DummyRequest(browser_id_=bid, browser_id_ns_=None)
        mgr = self._makeOne(request)
        self.failUnless(mgr.isBrowserIdNew())

    def test_isBrowserIdNew_w_ns(self):
        from Products.Sessions.BrowserIdManager import getNewBrowserId
        bid = getNewBrowserId()
        request = DummyRequest(browser_id_=bid, browser_id_ns_='url')
        mgr = self._makeOne(request)
        self.failIf(mgr.isBrowserIdNew())

    def test_isBrowserIdFromCookie_nonesuch_raises(self):
        request = DummyRequest()
        mgr = self._makeOne(request)
        self.assertRaises(ValueError, mgr.isBrowserIdFromCookie)

    def test_isBrowserIdFromCookie_wrong_ns(self):
        from Products.Sessions.BrowserIdManager import getNewBrowserId
        bid = getNewBrowserId()
        request = DummyRequest(browser_id_=bid, browser_id_ns_='url')
        mgr = self._makeOne(request)
        self.failIf(mgr.isBrowserIdFromCookie())

    def test_isBrowserIdFromCookie_right_ns(self):
        from Products.Sessions.BrowserIdManager import getNewBrowserId
        bid = getNewBrowserId()
        request = DummyRequest(browser_id_=bid, browser_id_ns_='cookies')
        mgr = self._makeOne(request)
        self.failUnless(mgr.isBrowserIdFromCookie())

    def test_isBrowserIdFromForm_nonesuch_raises(self):
        request = DummyRequest()
        mgr = self._makeOne(request)
        self.assertRaises(ValueError, mgr.isBrowserIdFromForm)

    def test_isBrowserIdFromForm_wrong_ns(self):
        from Products.Sessions.BrowserIdManager import getNewBrowserId
        bid = getNewBrowserId()
        request = DummyRequest(browser_id_=bid, browser_id_ns_='url')
        mgr = self._makeOne(request)
        self.failIf(mgr.isBrowserIdFromForm())

    def test_isBrowserIdFromForm_right_ns(self):
        from Products.Sessions.BrowserIdManager import getNewBrowserId
        bid = getNewBrowserId()
        request = DummyRequest(browser_id_=bid, browser_id_ns_='form')
        mgr = self._makeOne(request)
        self.failUnless(mgr.isBrowserIdFromForm())

    def test_isBrowserIdFromUrl_nonesuch_raises(self):
        request = DummyRequest()
        mgr = self._makeOne(request)
        self.assertRaises(ValueError, mgr.isBrowserIdFromUrl)

    def test_isBrowserIdFromUrl_wrong_ns(self):
        from Products.Sessions.BrowserIdManager import getNewBrowserId
        bid = getNewBrowserId()
        request = DummyRequest(browser_id_=bid, browser_id_ns_='form')
        mgr = self._makeOne(request)
        self.failIf(mgr.isBrowserIdFromUrl())

    def test_isBrowserIdFromUrl_right_ns(self):
        from Products.Sessions.BrowserIdManager import getNewBrowserId
        bid = getNewBrowserId()
        request = DummyRequest(browser_id_=bid, browser_id_ns_='url')
        mgr = self._makeOne(request)
        self.failUnless(mgr.isBrowserIdFromUrl())

    def test_flushBrowserIdCookie_wrong_ns_raises(self):
        mgr = self._makeOne()
        mgr.setBrowserIdNamespaces(('url', 'form'))
        self.assertRaises(ValueError, mgr.flushBrowserIdCookie)

    def test_flushBrowserIdCookie_ok(self):
        response = DummyResponse(cookies={})
        request = DummyRequest(RESPONSE=response)
        mgr = self._makeOne(request)
        mgr.setBrowserIdName('bid')
        mgr.setBrowserIdNamespaces(('cookies',))
        mgr.flushBrowserIdCookie()
        self.assertEqual(response.cookies['bid'],
                         {'path': '/',
                          'expires': 'Sun, 10-May-1971 11:59:00 GMT',
                          'value': 'deleted'})

    def test_setBrowserIdCookieByForce_wrong_ns_raises(self):
        from Products.Sessions.BrowserIdManager import getNewBrowserId
        bid = getNewBrowserId()
        mgr = self._makeOne()
        mgr.setBrowserIdNamespaces(('url', 'form'))
        self.assertRaises(ValueError, mgr.setBrowserIdCookieByForce, bid)

    def test_setBrowserIdCookieByForce_ok(self):
        from Products.Sessions.BrowserIdManager import getNewBrowserId
        bid = getNewBrowserId()
        response = DummyResponse(cookies={})
        request = DummyRequest(RESPONSE=response)
        mgr = self._makeOne(request)
        mgr.setBrowserIdName('bid')
        mgr.setBrowserIdNamespaces(('cookies',))
        mgr.setBrowserIdCookieByForce(bid)
        self.assertEqual(response.cookies['bid'], {'path': '/', 'value': bid})

    def test_getHiddenFormField(self):
        from Products.Sessions.BrowserIdManager import getNewBrowserId
        bid = getNewBrowserId()
        request = DummyRequest(browser_id_=bid)
        mgr = self._makeOne(request)
        mgr.setBrowserIdName('bid')
        self.assertEqual(mgr.getHiddenFormField(),
                         '<input type="hidden" name="bid" value="%s" />' % bid)

    def test_encodeUrl_no_create_no_bid_raises(self):
        URL = 'http://example.com/'
        request = DummyRequest()
        mgr = self._makeOne(request)
        self.assertRaises(ValueError, mgr.encodeUrl, URL, create=False)

    def test_encodeUrl_no_create_w_bid_querystring_style(self):
        from Products.Sessions.BrowserIdManager import getNewBrowserId
        URL = 'http://example.com/'
        bid = getNewBrowserId()
        request = DummyRequest(browser_id_=bid)
        mgr = self._makeOne(request)
        mgr.setBrowserIdName('bid')
        munged = mgr.encodeUrl(URL, create=False)
        self.assertEqual(munged, '%s?bid=%s' % (URL, bid))

    def test_encodeUrl_no_create_w_bid_querystring_style_existing_qs(self):
        from Products.Sessions.BrowserIdManager import getNewBrowserId
        URL = 'http://example.com/'
        QS = 'foo=bar'
        bid = getNewBrowserId()
        request = DummyRequest(browser_id_=bid)
        mgr = self._makeOne(request)
        mgr.setBrowserIdName('bid')
        munged = mgr.encodeUrl('%s?%s' % (URL, QS), create=False)
        self.assertEqual(munged, '%s?%s&amp;bid=%s' % (URL, QS, bid))

    def test_encodeUrl_no_create_w_bid_inline_style(self):
        from Products.Sessions.BrowserIdManager import getNewBrowserId
        NETHOST = 'http://example.com'
        PATH_INFO = 'path/to/page'
        URL = '%s/%s' % (NETHOST, PATH_INFO)
        bid = getNewBrowserId()
        request = DummyRequest(browser_id_=bid)
        mgr = self._makeOne(request)
        mgr.setBrowserIdName('bid')
        munged = mgr.encodeUrl(URL, style='inline', create=False)
        self.assertEqual(munged, '%s/bid/%s/%s' % (NETHOST, bid, PATH_INFO))

    def test_setBrowserIdName_empty_string_raises(self):
        mgr = self._makeOne()
        self.assertRaises(ValueError, mgr.setBrowserIdName, '')

    def test_setBrowserIdName_non_string_raises(self):
        mgr = self._makeOne()
        self.assertRaises(ValueError, mgr.setBrowserIdName, 1)

    def test_setBrowserIdName_normal(self):
        mgr = self._makeOne()
        mgr.setBrowserIdName('foo')
        self.assertEqual(mgr.getBrowserIdName(), 'foo')

    def test_setBrowserIdNamespaces_invalid_raises(self):
        mgr = self._makeOne()
        self.assertRaises(ValueError,
                          mgr.setBrowserIdNamespaces, ('gummy', 'froopy'))

    def test_setBrowserIdNamespaces_normal(self):
        NAMESPACES = ('cookies', 'url', 'form')
        mgr = self._makeOne()
        mgr.setBrowserIdNamespaces(NAMESPACES)
        self.assertEqual(mgr.getBrowserIdNamespaces(), NAMESPACES)

    def test_setCookiePath_invalid_raises(self):
        mgr = self._makeOne()
        self.assertRaises(ValueError, mgr.setCookiePath, '/;')

    def test_setCookiePath_normal(self):
        mgr = self._makeOne()
        mgr.setCookiePath('/foo')
        self.assertEqual(mgr.getCookiePath(), '/foo')

    def test_setCookieLifeDays_invalid_raises(self):
        mgr = self._makeOne()
        self.assertRaises(ValueError, mgr.setCookieLifeDays, '')

    def test_setCookieLifeDays_normal(self):
        mgr = self._makeOne()
        mgr.setCookieLifeDays(1)
        self.assertEqual(mgr.getCookieLifeDays(), 1)

    def test_setCookieDomain_non_string_raises(self):
        mgr = self._makeOne()
        self.assertRaises(ValueError, mgr.setCookieDomain, {1:1})

    def test_setCookieDomain_no_dots_raises(self):
        mgr = self._makeOne()
        self.assertRaises(ValueError, mgr.setCookieDomain, 'gubble')

    def test_setCookieDomain_one_dot_raises(self):
        mgr = self._makeOne()
        self.assertRaises(ValueError, mgr.setCookieDomain, 'zope.org')

    def test_setCookieDomain_trailing_semicolon_raises(self):
        mgr = self._makeOne()
        self.assertRaises(ValueError, mgr.setCookieDomain, '.zope.org;')

    def test_setCookieDomain_empty_OK(self):
        mgr = self._makeOne()
        mgr.setCookieDomain('')
        self.assertEqual(mgr.getCookieDomain(), '')

    def test_setCookieDomain_two_dots(self):
        mgr = self._makeOne()
        mgr.setCookieDomain('.zope.org')
        self.assertEqual(mgr.getCookieDomain(), '.zope.org')

    def test_setCookieDomain_three_dots(self):
        mgr = self._makeOne()
        mgr.setCookieDomain('.dev.zope.org')
        self.assertEqual(mgr.getCookieDomain(), '.dev.zope.org')

    def test_setCookieSecure_int(self):
        mgr = self._makeOne()
        mgr.setCookieSecure(1)
        self.failUnless(mgr.getCookieSecure())
        mgr.setCookieSecure(0)
        self.failIf(mgr.getCookieSecure())

    def test_setCookieSecure_bool(self):
        mgr = self._makeOne()
        mgr.setCookieSecure(True)
        self.failUnless(mgr.getCookieSecure())
        mgr.setCookieSecure(False)
        self.failIf(mgr.getCookieSecure())

    def test_setCookieHTTPOnly_bool(self):
        mgr = self._makeOne()
        mgr.setCookieHTTPOnly(True)
        self.failUnless(mgr.getCookieHTTPOnly())
        mgr.setCookieHTTPOnly(False)
        self.failIf(mgr.getCookieHTTPOnly())

    def test_setAutoUrlEncoding_bool(self):
        mgr = self._makeOne()
        mgr.setAutoUrlEncoding(True)
        self.failUnless(mgr.getAutoUrlEncoding())
        mgr.setAutoUrlEncoding(False)
        self.failIf(mgr.getAutoUrlEncoding())

    def test_isUrlInBidNamespaces(self):
        mgr = self._makeOne()
        mgr.setBrowserIdNamespaces(('cookies', 'url', 'form'))
        self.failUnless(mgr.isUrlInBidNamespaces())
        mgr.setBrowserIdNamespaces(('cookies', 'form'))
        self.failIf(mgr.isUrlInBidNamespaces())

    def test__setCookie_remove(self):
        response = DummyResponse(cookies={})
        request = DummyRequest(RESPONSE=response)
        mgr = self._makeOne(request)
        mgr.setBrowserIdName('bid')
        mgr._setCookie('xxx', request, remove=True)
        self.assertEqual(response.cookies['bid'],
                         {'path': '/', 'value': 'xxx',
                          'expires': 'Sun, 10-May-1971 11:59:00 GMT'})

    def test__setCookie_cookie_life_days(self):
        response = DummyResponse(cookies={})
        request = DummyRequest(RESPONSE=response)
        mgr = self._makeOne(request)
        mgr.setBrowserIdName('bid')
        mgr.setCookieLifeDays(1)
        mgr._setCookie('xxx', request,
                       now=lambda: 1,
                       strftime=lambda x, y: 'Seconds: %d' % y,
                       gmtime=lambda x: x)
        self.assertEqual(response.cookies['bid'],
                         {'path': '/', 'value': 'xxx',
                          'expires': 'Seconds: 86401'})

    def test__setCookie_cookie_secure_no_URL1_sets_no_cookie(self):
        request = DummyRequest()
        mgr = self._makeOne(request)
        mgr.setBrowserIdName('bid')
        mgr.setCookieSecure(True)
        mgr._setCookie('xxx', request) # no response, doesn't blow up

    def test__setCookie_cookie_secure_not_https_sets_no_cookie(self):
        request = DummyRequest(URL1='http://example.com/')
        mgr = self._makeOne(request)
        mgr.setBrowserIdName('bid')
        mgr.setCookieSecure(True)
        mgr._setCookie('xxx', request) # no response, doesn't blow up

    def test__setCookie_cookie_secure_is_https(self):
        response = DummyResponse(cookies={})
        request = DummyRequest(RESPONSE=response, URL1='https://example.com/')
        mgr = self._makeOne(request)
        mgr.setBrowserIdName('bid')
        mgr.setCookieSecure(True)
        mgr._setCookie('xxx', request)
        self.assertEqual(response.cookies['bid'],
                         {'path': '/', 'value': 'xxx', 'secure': True})

    def test__setCookie_domain(self):
        response = DummyResponse(cookies={})
        request = DummyRequest(RESPONSE=response)
        mgr = self._makeOne(request)
        mgr.setBrowserIdName('bid')
        mgr.setCookieDomain('.zope.org')
        mgr._setCookie('xxx', request)
        self.assertEqual(response.cookies['bid'],
                         {'path': '/', 'value': 'xxx', 'domain': '.zope.org'})

    def test__setCookie_path(self):
        response = DummyResponse(cookies={})
        request = DummyRequest(RESPONSE=response)
        mgr = self._makeOne(request)
        mgr.setBrowserIdName('bid')
        mgr.setCookiePath('/path/')
        mgr._setCookie('xxx', request)
        self.assertEqual(response.cookies['bid'],
                         {'path': '/path/', 'value': 'xxx'})

    def test__setCookie_http_only(self):
        response = DummyResponse(cookies={})
        request = DummyRequest(RESPONSE=response, URL1='https://example.com/')
        mgr = self._makeOne(request)
        mgr.setBrowserIdName('bid')
        mgr.setCookieHTTPOnly(True)
        mgr._setCookie('xxx', request)
        self.assertEqual(response.cookies['bid'],
                         {'path': '/', 'value': 'xxx', 'http_only': True})

    def test__setCookie_http_only_missing_attr(self):
        # See https://bugs.launchpad.net/bugs/374816
        response = DummyResponse(cookies={})
        request = DummyRequest(RESPONSE=response, URL1='https://example.com/')
        mgr = self._makeOne(request)
        del mgr.cookie_http_only # pre-2.12 instances didn't have this
        mgr.setBrowserIdName('bid')
        mgr._setCookie('xxx', request)
        self.assertEqual(response.cookies['bid'],
                         {'path': '/', 'value': 'xxx'})

    def test__setId_same_id_noop(self):
        mgr = self._makeOne(name='foo')
        mgr._setId('foo')

    def test__setId_different_id_raises(self):
        mgr = self._makeOne(name='foo')
        self.assertRaises(ValueError, mgr._setId, 'bar')

    def test_setCookieSecure_non_HTTPS_doesnt_set_cookie(self):
        # Document the "feature" that 'setCookieSecure' allows returning
        # a browser ID even where the URL is not HTTPS, and therefor no
        # cookie is set.
        response = DummyResponse(cookies={})
        request = DummyRequest(RESPONSE=response, URL1='http://example.com/')
        mgr = self._makeOne(request)
        mgr.setCookieSecure(1)
        bid = mgr.getBrowserId() # doesn't raise
        self.assertEqual(len(response.cookies), 0)

    def test_hasTraversalHook_missing(self):
        mgr = self._makeOne()
        parent = DummyObject()
        self.failIf(mgr.hasTraversalHook(parent))

    def test_hasTraversalHook_present(self):
        mgr = self._makeOne()
        parent = DummyObject()
        parent.__before_traverse__ = {(0, 'BrowserIdManager'): object()}
        self.failUnless(mgr.hasTraversalHook(parent))

    def test_updateTraversalData_w_url_ns(self):
        from Acquisition import Implicit
        from ZPublisher.BeforeTraverse import queryBeforeTraverse
        from Products.Sessions.BrowserIdManager import BrowserIdManagerTraverser
        class Parent(Implicit):
            pass
        mgr = self._makeOne()
        mgr.setBrowserIdNamespaces(('url',))
        parent = Parent()
        parent.browser_id_manager = mgr
        parent.browser_id_manager.updateTraversalData() # needs wrapper
        hooks = queryBeforeTraverse(parent, 'BrowserIdManager')
        self.assertEqual(len(hooks), 1)
        self.assertEqual(hooks[0][0], 40)
        self.failUnless(isinstance(hooks[0][1], BrowserIdManagerTraverser))

    def test_updateTraversalData_not_url_ns(self):
        from Acquisition import Implicit
        from ZPublisher.BeforeTraverse import queryBeforeTraverse
        class Parent(Implicit):
            pass
        mgr = self._makeOne()
        mgr.setBrowserIdNamespaces(('cookies', 'form'))
        parent = Parent()
        parent.__before_traverse__ = {(0, 'BrowserIdManager'): object()}
        parent.browser_id_manager = mgr
        parent.browser_id_manager.updateTraversalData() # needs wrapper
        self.failIf(queryBeforeTraverse(mgr, 'BrowserIdManager'))

    def test_registerTraversalHook_doesnt_replace_existing(self):
        from Acquisition import Implicit
        from ZPublisher.BeforeTraverse import queryBeforeTraverse
        class Parent(Implicit):
            pass
        mgr = self._makeOne()
        parent = Parent()
        hook = object()
        parent.__before_traverse__ = {(0, 'BrowserIdManager'): hook}
        parent.browser_id_manager = mgr
        parent.browser_id_manager.registerTraversalHook() # needs wrapper
        hooks = queryBeforeTraverse(parent, 'BrowserIdManager')
        self.assertEqual(len(hooks), 1)
        self.assertEqual(hooks[0][0], 0)
        self.failUnless(hooks[0][1] is hook)

    def test_registerTraversalHook_normal(self):
        from Acquisition import Implicit
        from ZPublisher.BeforeTraverse import queryBeforeTraverse
        from Products.Sessions.BrowserIdManager import BrowserIdManagerTraverser
        class Parent(Implicit):
            pass
        mgr = self._makeOne()
        parent = Parent()
        parent.browser_id_manager = mgr
        parent.browser_id_manager.registerTraversalHook() # needs wrapper
        hooks = queryBeforeTraverse(parent, 'BrowserIdManager')
        self.assertEqual(len(hooks), 1)
        self.assertEqual(hooks[0][0], 40)
        self.failUnless(isinstance(hooks[0][1], BrowserIdManagerTraverser))

    def test_unregisterTraversalHook_nonesuch_doesnt_raise(self):
        from Acquisition import Implicit
        class Parent(Implicit):
            pass
        mgr = self._makeOne()
        parent = Parent()
        parent.browser_id_manager = mgr
        parent.browser_id_manager.unregisterTraversalHook() # needs wrapper

    def test_unregisterTraversalHook_normal(self):
        from Acquisition import Implicit
        from ZPublisher.BeforeTraverse import queryBeforeTraverse
        class Parent(Implicit):
            pass
        mgr = self._makeOne()
        parent = Parent()
        parent.__before_traverse__ = {(0, 'BrowserIdManager'): object()}
        parent.browser_id_manager = mgr
        parent.browser_id_manager.unregisterTraversalHook() # needs wrapper
        self.failIf(queryBeforeTraverse(mgr, 'BrowserIdManager'))
    

class TestBrowserIdManagerTraverser(unittest.TestCase):

    def _getTargetClass(self):
        from Products.Sessions.BrowserIdManager \
            import BrowserIdManagerTraverser
        return BrowserIdManagerTraverser

    def _makeOne(self):
        return self._getTargetClass()()

    def test___call___no_mgr(self):
        traverser = self._makeOne()
        container = DummyObject()
        request = DummyRequest()
        traverser(container, request) # doesn't raise

    def test___call___w_mgr_request_has_no_stack(self):
        traverser = self._makeOne()
        mgr = DummyBrowserIdManager()
        container = DummyObject(browser_id_manager=mgr)
        request = DummyRequest()
        traverser(container, request) # doesn't raise

    def test___call___w_mgr_request_has_stack_no_auto_encode(self):
        from Products.Sessions.BrowserIdManager import getNewBrowserId
        bid = getNewBrowserId()
        traverser = self._makeOne()
        mgr = DummyBrowserIdManager()
        container = DummyObject(browser_id_manager=mgr)
        request = DummyRequest(
                    TraversalRequestNameStack=[bid, 'bid'])
        traverser(container, request)
        self.assertEqual(request.browser_id_, bid)
        self.assertEqual(request.browser_id_ns_, 'url')
        self.assertEqual(len(request.TraversalRequestNameStack), 0)

    def test___call___w_mgr_request_has_stack_w_auto_encode(self):
        from Products.Sessions.BrowserIdManager import getNewBrowserId
        bid = getNewBrowserId()
        traverser = self._makeOne()
        mgr = DummyBrowserIdManager(True)
        container = DummyObject(browser_id_manager=mgr)
        request = DummyRequest(
                    TraversalRequestNameStack=[bid, 'bid'], _script=[])
        traverser(container, request)
        self.assertEqual(request.browser_id_, bid)
        self.assertEqual(request.browser_id_ns_, 'url')
        self.assertEqual(len(request.TraversalRequestNameStack), 0)
        self.assertEqual(len(request._script), 2)
        self.assertEqual(request._script[0], 'bid')
        self.assertEqual(request._script[1], bid)

    def test___call___w_mgr_request_empty_stack_w_auto_encode(self):
        from Products.Sessions.BrowserIdManager import isAWellFormedBrowserId
        traverser = self._makeOne()
        mgr = DummyBrowserIdManager(True)
        container = DummyObject(browser_id_manager=mgr)
        request = DummyRequest( TraversalRequestNameStack=[], _script=[])
        traverser(container, request)
        bid = request.browser_id_
        self.failUnless(isAWellFormedBrowserId(bid))
        self.assertEqual(request.browser_id_ns_, None)
        self.assertEqual(len(request.TraversalRequestNameStack), 0)
        self.assertEqual(len(request._script), 2)
        self.assertEqual(request._script[0], 'bid')
        self.assertEqual(request._script[1], bid)


class DummyObject:
    def __init__(self, **kw):
        self.__dict__.update(kw)

class DummyResponse(DummyObject):
    pass

class DummyRequest(DummyObject):
    def __getitem__(self, key):
        return getattr(self, key)
    def get(self, key, default=None):
        return getattr(self, key, default)

class DummyBrowserIdManager:
    def __init__(self, auto=False):
        self._auto = auto
    def getBrowserIdName(self):
        return 'bid'
    def getAutoUrlEncoding(self):
        return self._auto

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(TestBrowserIdManager),
        unittest.makeSuite(TestBrowserIdManagerTraverser),
    ))
