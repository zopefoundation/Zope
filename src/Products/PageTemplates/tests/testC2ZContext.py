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

from ..engine import _C2ZContextWrapper


class C2ZContextTests(unittest.TestCase):
    def setUp(self):
        self.c_context = c_context = Scope()
        c_context["__zt_context__"] = Context(None, {})
        self.z_context = _C2ZContextWrapper(c_context, None)

    def test_elementary_functions(self):
        c = self.z_context
        c.setLocal("a", "A")
        c.setLocal("b", "B")
        self.assertEqual(c["a"], "A")
        self.assertEqual(c.get("b"), "B")
        self.assertIsNone(c.get("c"))
        with self.assertRaises(KeyError):
            c["c"]
        self.assertEqual(sorted(c.keys()), ["__zt_context__", "a", "b"])
        self.assertEqual(sorted(c), ["__zt_context__", "a", "b"])
        vs = c.values()
        for v in ("A", "B"):
            self.assertIn(v, vs)
        its = c.items()
        for k in "ab":
            self.assertIn((k, k.capitalize()), its)
        self.assertIn("a", c)
        self.assertNotIn("c", c)
        self.assertEqual(len(c), 3)
        # templates typically use ``vars`` as ``dict`` instead of API methods
        self.assertIs(c.vars, c)

    def test_setGlobal(self):
        top_context = self.z_context
        c_context = self.c_context.copy()  # context push
        c = _C2ZContextWrapper(c_context, None)  # local ``zope`` context
        c.setLocal("a", "A")
        self.assertIn("a", c)
        self.assertNotIn("a", top_context)
        c.setGlobal("b", "B")
        # the following (commented code) line fails due to
        #   "https://github.com/malthe/chameleon/issues/305"
        # self.assertIn("b", c)
        self.assertIn("b", top_context)
        self.assertEqual(c["b"], "B")
        self.assertEqual(top_context["b"], "B")
        # Note: "https://github.com/malthe/chameleon/issues/305":
        #   ``dict`` methods are unreliable in presence of global variables
        #   We therefore do not test them.

    def test_unimplemented(self):
        c = self.z_context
        cd = Context.__dict__
        for m in ("beginScope", "endScope", "setSourceFile", "setPosition"):
            self.assertIn(m, cd)  # check against spelling errors
            with self.assertRaises(NotImplementedError):
                getattr(c, m)()

    def test_attribute_delegation(self):
        c = self.z_context
        self.assertIsNone(c._engine)

    def test_attrs(self):
        c = self.z_context
        self.assertIsNone(c["attrs"])
        c.setLocal("attrs", "hallo")
        self.assertEqual(c["attrs"], "hallo")

    def test_faithful_wrapping(self):
        class MyContext(object):
            def set(self, v):
                self.attr = v

            def get_vars(self):
                return self.vars

            def my_get(self, k):
                return self[k]
        
        c_context = self.c_context
        c_context["__zt_context__"] = my_context = MyContext()
        zc = _C2ZContextWrapper(c_context, None) 
        # attributes in ``my_context``
        #   -- via method
        zc.set("attr")
        self.assertEqual(my_context.attr, "attr")
        #  -- via wrapper
        zc.wattr = "wattr"
        self.assertEqual(my_context.wattr, "wattr")
        # correct ``vars``
        self.assertIs(zc.get_vars(), zc)
        # correct subscription
        zc.setLocal("a", "a")
        self.assertEqual(zc.my_get("a"), "a")
        # correct attribute access
        my_context.my_attr = "my_attr"
        self.assertEqual(zc.my_attr, "my_attr")
