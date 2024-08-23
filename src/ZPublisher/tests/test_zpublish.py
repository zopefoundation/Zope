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

from Shared.DC.Scripts.Signature import FuncCode

from .. import zpublish
from .. import zpublish_mark
from .. import zpublish_marked
from .. import zpublish_wrap


class ZpublishTests(TestCase):
    def test_zpublish_true(self):
        @zpublish
        def f():
            pass

        self.assertTrue(zpublish_mark(f))
        self.assertTrue(zpublish_marked(f))

    def test_zpublish_false(self):
        @zpublish(False)
        def f():
            pass

        self.assertFalse(zpublish_mark(f))
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
        self.assertTrue(zpublish_mark(f, True))
        zpublish(f)
        self.assertTrue(zpublish_mark(f))

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
        self.assertTrue(zpublish_mark(wrapper))
        self.assertEqual(signature(wrapper), signature(f))
        self.assertIs(wrapper, zpublish_wrap(wrapper))
        wrapper2 = zpublish_wrap(wrapper, conditional=False, methods="put")
        self.assertIsNot(wrapper2, wrapper)
        self.assertEqual(zpublish_mark(wrapper2), ("PUT",))

        # test ``mapply`` signature

        class WithMapplySignature:
            __code__ = FuncCode(("a", "b", "c"), 2)
            __defaults__ = None

            def __call__(self, *args, **kw):
                pass

        f = WithMapplySignature()
        wrapper = zpublish_wrap(f)
        self.assertEqual(str(wrapper.__signature__), "(a, b)")
        WithMapplySignature.__defaults__ = 2,
        wrapper = zpublish_wrap(f)
        self.assertEqual(str(wrapper.__signature__), "(a, b=2)")
