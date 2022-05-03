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
import unittest

from chameleon.utils import Scope

from zope.tales.tales import Context

from ..engine import DEFAULT_MARKER
from ..engine import _C2ZContextWrapper
from ..engine import _context_class_registry
from ..engine import _with_vars_from_chameleon as wrap


class C2ZContextTests(unittest.TestCase):
    def setUp(self):
        self.c_context = c_context = Scope()
        z_context = Context(None, {})
        z_context.setContext("default", DEFAULT_MARKER)
        c_context["__zt_context__"] = wrap(z_context)
        self.z_context = _C2ZContextWrapper(c_context, None)

    def test_elementary_functions(self):
        c = self.z_context
        cv = c.vars
        c.setLocal("a", "A")
        c.setLocal("b", "B")
        self.assertEqual(cv["a"], "A")
        self.assertEqual(c.get("b"), "B")
        self.assertIsNone(c.get("c"))
        with self.assertRaises(KeyError):
            cv["c"]
        self.assertEqual(sorted(cv.keys()),
                         ["__zt_context__", "a", "attrs", "b"])
        self.assertEqual(sorted(cv), ["__zt_context__", "a", "attrs", "b"])
        vs = cv.values()
        for v in ("A", "B"):
            self.assertIn(v, vs)
        its = cv.items()
        for k in "ab":
            self.assertIn((k, k.capitalize()), its)
        self.assertIn("a", cv)
        self.assertNotIn("c", cv)
        self.assertEqual(len(cv), 4)

    def test_setGlobal(self):
        top_context = self.z_context.vars
        c_context = self.c_context.copy()  # context push
        c = _C2ZContextWrapper(c_context, None)  # local ``zope`` context
        cv = c.vars
        c.setLocal("a", "A")
        self.assertIn("a", cv)
        self.assertNotIn("a", top_context)
        c.setGlobal("b", "B")
        # the following (commented code) line fails due to
        #   "https://github.com/malthe/chameleon/issues/305"
        # self.assertIn("b", c)
        self.assertIn("b", top_context)
        self.assertEqual(cv["b"], "B")
        self.assertEqual(top_context["b"], "B")
        # Note: "https://github.com/malthe/chameleon/issues/305":
        #   ``dict`` methods are unreliable in presence of global variables
        #   We therefore do not test them.

    def test_unimplemented(self):
        c = self.z_context
        cd = Context.__dict__
        for m in ("beginScope", "endScope", "setSourceFile", "setPosition",
                  "setRepeat"):
            self.assertIn(m, cd)  # check against spelling errors
            with self.assertRaises(NotImplementedError):
                getattr(c, m)()

    def test_attribute_delegation(self):
        c = self.z_context
        self.assertIsNone(c._engine)

    def test_attrs(self):
        c = self.z_context
        self.assertIsNone(c.vars["attrs"])
        c.setLocal("attrs", "hallo")
        self.assertEqual(c.vars["attrs"], "hallo")

    def test_faithful_wrapping(self):
        class MyContextBase:
            var = None
            var2 = None

            def get_vars(self):
                return self.vars

        class MyContext(MyContextBase):
            var = None

            def set(self, v):
                self.attr = v

            def get_vars(self):
                return super().get_vars()

            def my_get(self, k):
                return self.vars[k]

            def override_var(self):
                self.var = "var"

        c_context = self.c_context
        my_context = MyContext()
        my_context.var2 = "var2"
        c_context["__zt_context__"] = wrap(my_context)
        zc = _C2ZContextWrapper(c_context, None)
        # attributes
        #   -- via method
        zc.set("attr")
        self.assertEqual(zc.attr, "attr")
        #  -- via wrapper
        zc.wattr = "wattr"
        self.assertEqual(zc.wattr, "wattr")
        # correct ``vars``; including ``super``
        self.assertEqual(zc.get_vars(), zc.vars)
        # correct subscription
        zc.setLocal("a", "a")
        self.assertEqual(zc.my_get("a"), "a")
        # correct attribute access
        my_context.my_attr = "my_attr"
        self.assertEqual(zc.my_attr, "my_attr")
        # override class variable
        self.assertIsNone(zc.var)
        zc.override_var()
        self.assertEqual(zc.var, "var")
        # instance variable over class variable
        self.assertEqual(zc.var2, "var2")

    def test_context_class_registry(self):
        class MyContext:
            pass

        class_regs = len(_context_class_registry)
        wc1 = wrap(MyContext())()
        self.assertEqual(len(_context_class_registry), class_regs + 1)
        wc2 = wrap(MyContext())()
        self.assertEqual(len(_context_class_registry), class_regs + 1)
        self.assertIs(wc1.__class__, wc2.__class__)

    def test_default(self):
        c = self.z_context
        self.assertIs(c.getDefault(), DEFAULT_MARKER)
