##############################################################################
#
# Copyright (c) 2023 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
import unittest
from io import BytesIO

from paste.deploy import loadfilter

from ..pastefilter import LimitedFileReader


class TestLimitedFileReader(unittest.TestCase):
    def test_enforce_limit(self):
        f = LimitedFileReader(BytesIO(), 10)
        enforce = f._enforce_limit
        self.assertEqual(enforce(None), 10)
        self.assertEqual(enforce(-1), 10)
        self.assertEqual(enforce(20), 10)
        self.assertEqual(enforce(5), 5)

    def test_read(self):
        f = LimitedFileReader(BytesIO(b"123\n567\n901\n"), 10)
        self.assertEqual(len(f.read()), 10)
        self.assertEqual(len(f.read()), 0)
        f = LimitedFileReader(BytesIO(b"123\n567\n901\n"), 10)
        self.assertEqual(len(f.read(8)), 8)
        self.assertEqual(len(f.read(3)), 2)
        self.assertEqual(len(f.read(3)), 0)

    def test_readline(self):
        f = LimitedFileReader(BytesIO(b"123\n567\n901\n"), 10)
        self.assertEqual(f.readline(), b"123\n")
        self.assertEqual(f.readline(), b"567\n")
        self.assertEqual(f.readline(), b"90")
        self.assertEqual(f.readline(), b"")
        f = LimitedFileReader(BytesIO(b"123\n567\n901\n"), 10)
        self.assertEqual(f.readline(1), b"1")

    def test_iteration(self):
        f = LimitedFileReader(BytesIO(b"123\n567\n901\n"), 10)
        self.assertEqual(list(f), [b"123\n", b"567\n", b"90"])

    def test_discard_remaining(self):
        fp = BytesIO(b"123\n567\n901\n")
        LimitedFileReader(fp, 10).discard_remaining()
        self.assertEqual(fp.read(), b"1\n")

    def test_delegation(self):
        f = LimitedFileReader(BytesIO(b"123\n567\n901\n"), 10)
        with self.assertRaises(AttributeError):
            f.write
        f.close()


class TestFilters(unittest.TestCase):
    def test_content_length(self):
        filter = loadfilter("egg:Zope", "content_length")

        def app(env, start_response):
            return iter((env["wsgi.input"],))

        def request(env, app=filter(app)):
            return app(env, None)

        fp = BytesIO()
        env = {"wsgi.input": fp}
        self.assertIs(next(request(env)), fp)

        fp = BytesIO(b"123")
        env = {"wsgi.input": fp}
        env["CONTENT_LENGTH"] = "3"
        response = request(env)
        r = next(response)
        self.assertIsInstance(r, LimitedFileReader)
        self.assertEqual(r.limit, 3)
        with self.assertRaises(StopIteration):
            next(response)
        self.assertFalse(fp.read())
