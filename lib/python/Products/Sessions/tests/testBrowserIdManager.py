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
Test suite for session id manager.

$Id: testBrowserIdManager.py,v 1.6 2001/11/27 03:46:33 chrism Exp $
"""
__version__ = "$Revision: 1.6 $"[11:-2]

import sys
if __name__ == "__main__":
    sys.path.insert(0, '../../..')
    sys.path.insert(0, '..')
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
