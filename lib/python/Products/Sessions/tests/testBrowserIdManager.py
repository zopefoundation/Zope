##############################################################################
#
# Copyright (c) 2001 Zope Corporation and Contributors. All Rights Reserved.
# 
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
# 
##############################################################################
"""
Test suite for session id manager.

$Id: testBrowserIdManager.py,v 1.8 2002/06/12 20:39:18 shane Exp $
"""
__version__ = "$Revision: 1.8 $"[11:-2]

import sys
import ZODB
from Products.Sessions.BrowserIdManager import BrowserIdManager, BrowserIdManagerErr
from unittest import TestCase, TestSuite, TextTestRunner, makeSuite
from ZPublisher.HTTPRequest import HTTPRequest
from ZPublisher.HTTPResponse import HTTPResponse
from sys import stdin
from os import environ

class TestBrowserIdManager(TestCase):
    def setUp(self):
        self.m = BrowserIdManager('foo')
        resp = HTTPResponse()
        environ['SERVER_NAME']='fred'
        environ['SERVER_PORT']='80'
        req = HTTPRequest(stdin, environ, resp)
        self.m.REQUEST = req
        
    def tearDown(self):
        del self.m

    def testSetBrowserIdName(self):
        self.m.setBrowserIdName('foo')
        assert self.m.getBrowserIdName()== 'foo'

    def testSetBadBrowserIdName(self):
        try:
            self.m.setBrowserIdName('')
        except BrowserIdManagerErr:
            pass
        else:
            assert 1 == 2
        try:
            self.m.setBrowserIdName(1)
        except BrowserIdManagerErr:
            pass
        else:
            assert 1 == 2
            
    def testSetBadNamespaces(self):
        d = {1:'gummy', 2:'froopy'}
        try:
            self.m.setBrowserIdNamespaces(d)
        except BrowserIdManagerErr:
            pass
        else:
            assert 1 == 2
            
    def testSetGoodNamespaces(self):
        d = {1:'cookies', 2:'form'}
        self.m.setBrowserIdNamespaces(d)
        assert self.m.getBrowserIdNamespaces() == d

    def testSetNamespacesByLocation(self):
        self.m.setBrowserIdLocation('cookiesonly')
        assert self.m.getBrowserIdNamespaces() == {1:'cookies'}
        assert self.m.getBrowserIdLocation() == 'cookiesonly'
        self.m.setBrowserIdLocation('cookiesthenform')
        assert self.m.getBrowserIdNamespaces() == {1:'cookies', 2:'form'}
        assert self.m.getBrowserIdLocation() == 'cookiesthenform'
        self.m.setBrowserIdLocation('formonly')
        assert self.m.getBrowserIdNamespaces() == {1:'form'}
        assert self.m.getBrowserIdLocation() == 'formonly'
        self.m.setBrowserIdLocation('formthencookies')
        assert self.m.getBrowserIdNamespaces() == {1:'form', 2:'cookies'}
        assert self.m.getBrowserIdLocation() == 'formthencookies'

    def testSetBadCookiePath(self):
        path = '/;'
        try:
            self.m.setCookiePath(path)
        except BrowserIdManagerErr:
            pass
        else:
            assert 1 == 2

    def testSetGoodCookiePath(self):
        self.m.setCookiePath('/foo')
        assert self.m.getCookiePath() == '/foo'

    def testSetBadCookieLifeDays(self):
        life = ''
        try:
            self.m.setCookieLifeDays('')
        except BrowserIdManagerErr:
            pass
        else:
            assert 1 == 2

    def testSetGoodCookieLifeDays(self):
        self.m.setCookieLifeDays(1)
        assert self.m.getCookieLifeDays() == 1

    def testSetBadCookieDomain(self):
        life = ''
        try:
            self.m.setCookieDomain('gubble')
        except BrowserIdManagerErr:
            pass
        else:
            assert 1 == 2

    def testSetGoodCookieLifeDays(self):
        self.m.setCookieLifeDays(1)
        assert self.m.getCookieLifeDays() == 1

    def testSetNoCookieDomain(self):
        domain = ''
        self.m.setCookieDomain(domain)
        setdomain = self.m.getCookieDomain()
        assert setdomain == domain, "%s" % setdomain

    def testSetBadCookieDomain(self):
        domain = 'zope.org' # not enough dots
        try:
            self.m.setCookieDomain(domain)
        except BrowserIdManagerErr:
            pass
        else:
            assert 1 == 2

        domain = {1:1} # must be stringtype
        try:
            self.m.setCookieDomain(domain)
        except BrowserIdManagerErr:
            pass
        else:
            assert 1 == 2
            
        domain = '.zope.org;' # semicolon follows
        try:
            self.m.setCookieDomain(domain)
        except BrowserIdManagerErr:
            pass
        else:
            assert 1 == 2

    def testSetGoodCookieDomain(self):
        self.m.setCookieDomain('.zope.org')
        setdomain = self.m.getCookieDomain()
        assert setdomain == '.zope.org', "%s" % setdomain
        
    def testSetCookieSecure(self):
        self.m.setCookieSecure(1)
        assert self.m.getCookieSecure() == 1

    def testGetBrowserIdCookie(self):
        token = self.m.getBrowserId()
        self.m.REQUEST.browser_id_ = token
        self.m.REQUEST.browser_id_ns_ = 'cookies'
        tokenkey = self.m.getBrowserIdName()
        self.m.REQUEST.cookies[tokenkey] = token
        a = self.m.getBrowserId()
        assert a == token, repr(a)
        assert self.m.isBrowserIdFromCookie()

    def testSetBrowserIdDontCreate(self):
        a = self.m.getBrowserId(0)
        assert a == None

    def testSetBrowserIdCreate(self):
        a = self.m.getBrowserId(1)
        tokenkey = self.m.getBrowserIdName()
        b = self.m.REQUEST.RESPONSE.cookies[tokenkey]
        assert a == b['value'], (a, b)

    def testHasBrowserId(self):
        assert not self.m.hasBrowserId()
        a = self.m.getBrowserId()
        assert self.m.hasBrowserId()
        
    def testBrowserIdIsNew(self):
        a = self.m.getBrowserId()
        assert self.m.isBrowserIdNew()

    def testIsBrowserIdFromCookieFirst(self):
        token = self.m.getBrowserId()
        self.m.REQUEST.browser_id_ = token
        self.m.REQUEST.browser_id_ns_ = 'cookies'
        tokenkey = self.m.getBrowserIdName()
        self.m.REQUEST.cookies[tokenkey] = token
        self.m.setBrowserIdNamespaces({1:'cookies', 2:'form'})
        a = self.m.getBrowserId()
        assert self.m.isBrowserIdFromCookie()

    def testIsBrowserIdFromFormFirst(self):
        token = self.m.getBrowserId()
        self.m.REQUEST.browser_id_ = token
        self.m.REQUEST.browser_id_ns_ = 'form'
        tokenkey = self.m.getBrowserIdName()
        self.m.REQUEST.form[tokenkey] = token
        self.m.setBrowserIdNamespaces({1:'form', 2:'cookies'})
        a = self.m.getBrowserId()
        assert self.m.isBrowserIdFromForm()

    def testIsBrowserIdFromCookieOnly(self):
        token = self.m.getBrowserId()
        self.m.REQUEST.browser_id_ = token
        self.m.REQUEST.browser_id_ns_ = 'cookies'
        tokenkey = self.m.getBrowserIdName()
        self.m.REQUEST.form[tokenkey] = token
        self.m.setBrowserIdNamespaces({1:'cookies'})
        a = self.m.getBrowserId()
        assert self.m.isBrowserIdFromCookie()
        assert not self.m.isBrowserIdFromForm()
 
    def testIsBrowserIdFromFormOnly(self):
        token = self.m.getBrowserId()
        self.m.REQUEST.browser_id_ = token
        self.m.REQUEST.browser_id_ns_ = 'form'
        tokenkey = self.m.getBrowserIdName()
        self.m.REQUEST.form[tokenkey] = token
        self.m.setBrowserIdNamespaces({1:'form'})
        a = self.m.getBrowserId()
        assert not self.m.isBrowserIdFromCookie()
        assert self.m.isBrowserIdFromForm()

    def testFlushBrowserIdCookie(self):
        token = self.m.getBrowserId()
        self.m.REQUEST.browser_id_ = token
        self.m.REQUEST.browser_id_ns_ = 'cookies'
        tokenkey = self.m.getBrowserIdName()
        self.m.REQUEST.cookies[tokenkey] = token
        a = self.m.getBrowserId()
        assert a == token, repr(a)
        assert self.m.isBrowserIdFromCookie()
        self.m.flushBrowserIdCookie()
        c = self.m.REQUEST.RESPONSE.cookies[tokenkey]
        assert c['value'] == 'deleted', c
        
    def testSetBrowserIdCookieByForce(self):
        token = self.m.getBrowserId()
        self.m.REQUEST.browser_id_ = token
        self.m.REQUEST.browser_id_ns_ = 'cookies'
        tokenkey = self.m.getBrowserIdName()
        self.m.REQUEST.cookies[tokenkey] = token
        a = self.m.getBrowserId()
        assert a == token, repr(a)
        assert self.m.isBrowserIdFromCookie()
        token = 'abcdefghijk'
        self.m.setBrowserIdCookieByForce(token)
        c = self.m.REQUEST.RESPONSE.cookies[tokenkey]
        assert c['value'] == token, c

    def testEncodeUrl(self):
        keystring = self.m.getBrowserIdName()
        key = self.m.getBrowserId()
        u = '/home/chrism/foo'
        r = self.m.encodeUrl(u)
        assert r == '%s?%s=%s' % (u, keystring, key)
        u = 'http://www.zope.org/Members/mcdonc?foo=bar&spam=eggs'
        r = self.m.encodeUrl(u)
        assert r == '%s&amp;%s=%s' % (u, keystring, key)

def test_suite():
    testsuite = makeSuite(TestBrowserIdManager, 'test')
    return testsuite
        
if __name__ == '__main__':
    runner = TextTestRunner(verbosity=9)
    runner.run(test_suite())
