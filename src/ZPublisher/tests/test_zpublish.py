##############################################################################
#
# Copyright (c) 2024 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""``zpublish`` related tests."""

from inspect import signature
from unittest import TestCase

from .. import zpublish
from .. import zpublish_mark
from .. import zpublish_marked
from .. import zpublish_wrap


class ZpublishTests(TestCase):
    def test_zpublish_true(self):
        @zpublish
        def f():
            pass

        self.assertIs(zpublish_mark(f), True)
        self.assertTrue(zpublish_marked(f))

    def test_zpublish_false(self):
        @zpublish(False)
        def f():
            pass

        self.assertIs(zpublish_mark(f), False)
        self.assertTrue(zpublish_marked(f))

    def test_zpublish_method(self):
        @zpublish(methods="method")
        def f():
            pass

        self.assertEqual(zpublish_mark(f), ("METHOD",))
        self.assertTrue(zpublish_marked(f))

    def test_zpublish_methods(self):
        @zpublish(methods="m1 m2".split())
        def f():
            pass

        self.assertEqual(zpublish_mark(f), ("M1", "M2"))
        self.assertTrue(zpublish_marked(f))

    def test_zpublish_mark(self):
        def f():
            pass

        self.assertIsNone(zpublish_mark(f))
        self.assertIs(zpublish_mark(f, True), True)
        zpublish(f)
        self.assertIs(zpublish_mark(f), True)

    def test_zpublish_marked(self):
        def f():
            pass

        self.assertFalse(zpublish_marked(f))
        zpublish(f)
        self.assertTrue(zpublish_marked(f))

    def test_zpublish_wrap(self):
        def f():
            pass

        self.assertFalse(zpublish_marked(f))
        wrapper = zpublish_wrap(f)
        self.assertFalse(zpublish_marked(f))
        self.assertIs(zpublish_mark(wrapper), True)
        self.assertEqual(signature(wrapper), signature(f))
        self.assertIs(wrapper, zpublish_wrap(wrapper))
