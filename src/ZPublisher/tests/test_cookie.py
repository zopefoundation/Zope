##############################################################################
#
# Copyright (c) 2022 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Cookie tests."""

from re import match
from unittest import TestCase

from ..cookie import CookieParameterRegistry
from ..cookie import DefaultCookieParamPolicy
from ..cookie import DefaultCookieValuePolicy
from ..cookie import convertCookieParameter
from ..cookie import defaultCookieParamPolicy
from ..cookie import defaultCookieValuePolicy
from ..cookie import getCookieParamPolicy
from ..cookie import getCookieValuePolicy
from ..cookie import mmap
from ..cookie import normalizeCookieParameterName
from ..cookie import wdmap


def assertRfc1123(self, s):
    """check *s* is an RFC1123 date."""
    m = match(r"(.{3}), \d{2} (.{3}) \d{4} \d{2}:\d{2}:\d{2} GMT$", s)
    self.assertIsNotNone(m)
    self.assertIn(m.group(1), tuple(wdmap.values()))
    self.assertIn(m.group(2), tuple(mmap.values()))


class DefaultPolicyTests(TestCase):
    def test_parameters(self):
        parameters = defaultCookieParamPolicy.parameters
        # normal
        self.assertEqual(
            tuple(parameters("n", dict(value="v", param="p"))),
            (("param", "p"),))
        # with ``Max-Age=-1`` without ``Expires``
        np = dict(parameters("n", {"Max-Age": "-1"}))
        self.assertEqual(np, {"Max-Age": "-1",
                              "Expires": "Wed, 31 Dec 1997 23:59:59 GMT"})
        # with ``Max-Age>0``, without ``Expires``
        np = dict(parameters("n", {"Max-Age": "1"}))
        assertRfc1123(self, np["Expires"])
        # with ``Max-Age>0``, with ``Expires``
        op = {"Max-Age": "1", "Expires": "exp"}
        self.assertEqual(op, dict(parameters("n", op)))

    def test_check_consistency(self):
        # it does nothing -- thus, just check the correct signature
        defaultCookieParamPolicy.check_consistency("n", {})

    def test_dump_load(self):
        dump = defaultCookieValuePolicy.dump
        load = defaultCookieValuePolicy.load

        def check(s):
            ds = dump("name", s)
            self.assertRegex(ds, r"[a-zA-Z0-9%_/]*$")
            ls = load("name", ds)
            self.assertEqual(ls, s)

        check("abc")
        check("a/b/c")
        check("äöü")
        check("!\"§$&/()=?´´'#@+*~,;.-_")
        check(" 	\n")


if not hasattr(DefaultPolicyTests, "assertRegex"):  # compatibility
    DefaultPolicyTests.assertRegex = DefaultPolicyTests.assertRegexpMatches


class CookieParameterRegistryTests(TestCase):
    def test_basics(self):
        reg = CookieParameterRegistry()
        register = reg.register

        def converter(value):
            return "pref" + value

        register("Max-Age", converter)
        for n in "Max-Age max-age Max_Age max_age".split():
            self.assertIs(reg._normalize[n], "Max-Age")
        self.assertIs(reg["Max-Age"], converter)
        self.assertEqual(reg.convert("max_age", ""), ("Max-Age", "pref"))
        self.assertEqual(normalizeCookieParameterName("http_only"),
                         "HttpOnly")

    def test_expires(self):
        # check int/float
        n, v = convertCookieParameter("expires", 1643714434)
        self.assertEqual(n, "Expires")
        self.assertEqual(v, "Tue, 01 Feb 2022 11:20:34 GMT")
        _, v = convertCookieParameter("expires", 1643714434.9)
        self.assertEqual(v, "Tue, 01 Feb 2022 11:20:34 GMT")
        # check naive datetime
        from datetime import datetime
        from datetime import timedelta
        tt = 2022, 2, 1, 11, 20, 34, 1, 32, -1
        _, v = convertCookieParameter("expires", datetime(*tt[:6]))
        self.assertEqual(v, "Tue, 01 Feb 2022 11:20:34 GMT")
        # check tzinfo datetime
        from ..cookie import UTC

        class CET(UTC):
            ZERO = timedelta(hours=1)

        cet = CET()
        tt = 2022, 2, 1, 12, 20, 34, 1, 32, -1
        _, v = convertCookieParameter("expires", datetime(*tt[:6], tzinfo=cet))
        self.assertEqual(v, "Tue, 01 Feb 2022 11:20:34 GMT")
        # check DateTime
        from DateTime import DateTime
        _, v = convertCookieParameter("expires", DateTime(1643714434, "CET"))
        self.assertEqual(v, "Tue, 01 Feb 2022 11:20:34 GMT")

    def test_max_age(self):
        n, v = convertCookieParameter("max_age", 0)
        self.assertEqual(n, "Max-Age")
        self.assertEqual(v, "0")
        with self.assertRaises(ValueError):
            convertCookieParameter("max_age", "abc")

    def test_domain(self):
        # already encoded
        n, v = convertCookieParameter("domain", "xn--dmin-moa0i.example")
        self.assertEqual(n, "Domain")
        self.assertEqual(v, "xn--dmin-moa0i.example")
        # perform encoding
        _, v = convertCookieParameter("domain", "dömäin.example")
        self.assertEqual(v, "xn--dmin-moa0i.example")
        # check IDNA2003
        _, v = convertCookieParameter("domain", "Fußball.example")
        self.assertEqual(v, "fussball.example")
        # check ``bytes`` handling
        _, v = convertCookieParameter("domain",
                                      "Fußball.example".encode())
        self.assertEqual(v, "fussball.example")
        # a leading dot is stripped as it is ignored according to
        # https://www.rfc-editor.org/rfc/rfc6265#section-4.1.2.3
        _, v = convertCookieParameter("domain", ".zope.dev")
        self.assertEqual(v, "zope.dev")

    def test_path(self):
        # test object
        class PathAware:
            def absolute_url_path(self):
                return "aup"
        obj = PathAware()
        n, v = convertCookieParameter("path", obj)
        self.assertEqual(n, "Path")
        self.assertEqual(v, "aup")
        # check path safe
        _, v = convertCookieParameter("path", "/a/b/c")
        self.assertEqual(v, "/a/b/c")
        _, v = convertCookieParameter("path", "/a/%20/c")
        self.assertEqual(v, "/a/%20/c")
        # check quote
        _, v = convertCookieParameter("path", "/a/ /c")
        self.assertEqual(v, "/a/%20/c")
        # check ``%`` dominates
        _, v = convertCookieParameter("path", "/a/%20/ ")
        self.assertEqual(v, "/a/%20/ ")

    def test_http_only(self):
        # test true
        n, v = convertCookieParameter("Http_Only", True)
        self.assertEqual(n, "HttpOnly")
        self.assertIs(v, True)
        # test false
        _, v = convertCookieParameter("http_only", False)
        self.assertIsNone(v)

    def test_secure(self):
        n, v = convertCookieParameter("secure", True)
        self.assertEqual(n, "Secure")
        self.assertIs(v, True)

    def test_samesite(self):
        for t in "None Lax Strict".split():
            n, v = convertCookieParameter("samesite", t.lower())
            self.assertEqual(n, "SameSite")
            self.assertEqual(v, t)
        # bad value
        with self.assertRaises(ValueError):
            convertCookieParameter("samesite", "abc")

    def test_comment(self):
        n, v = convertCookieParameter("comment", "comment")
        self.assertEqual(n, "Comment")
        self.assertEqual(v, "comment")

    def test_unknown_parameter(self):
        with self.assertRaises(KeyError):
            convertCookieParameter("xyz", "abc")


class GetCookiePolicyTests(TestCase):
    def tearDown(self):
        from zope.testing.cleanup import cleanUp

        # clear the component registry
        cleanUp()

    def test_defaults(self):
        self.assertIs(getCookieParamPolicy(), defaultCookieParamPolicy)
        self.assertIs(getCookieValuePolicy(), defaultCookieValuePolicy)

    def test_customization(self):
        from zope.component import provideUtility
        pp = DefaultCookieParamPolicy()
        provideUtility(pp)
        vp = DefaultCookieValuePolicy()
        provideUtility(vp)
        self.assertIs(getCookieParamPolicy(), pp)
        self.assertIs(getCookieValuePolicy(), vp)
