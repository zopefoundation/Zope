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
"""Partial ``ProductContext`` tests.
"""

from types import ModuleType
from types import SimpleNamespace
from unittest import TestCase

from ZPublisher import zpublish_marked

from ..ProductContext import ProductContext


class ProductContextTests(TestCase):
    def setUp(self):
        self.args = _Product(), _App(), ModuleType("pack")
        self.pc = ProductContext(*self.args)
        # ``ProductContext.registerClass`` has a lot of global
        # side effects. We save the original values, set up values
        # for our tests and restore the original values in ``teadDown``
        # When further tests are added, the list likely needs to
        # be extended
        self._saved = {}
        for ospec, val in {
                "sys.modules['Products']": ModuleType("Products"),
                "AccessControl.Permission._registeredPermissions": {},
                "AccessControl.Permission._ac_permissions": (),
                "AccessControl.Permission.ApplicationDefaultPermissions":
                _ApplicationDefaultPermissions}.items():
            obj = _resolve(ospec)
            self._saved[ospec] = obj.get()
            obj.set(val)

    def tearDown(self):
        for ospec, val in self._saved.items():
            _resolve(ospec).set(val)

    def test_initial_tuple(self):

        def c():
            pass

        self.pc.registerClass(meta_type="test", permission="test",
                              constructors=(("name", c),))
        self._verify_reg("name", "c")

    def test_initial_named(self):

        def c():
            pass

        self.pc.registerClass(meta_type="test", permission="test",
                              constructors=(c,))
        self._verify_reg("c", "c")

    def test_constructor_tuple(self):

        def initial():
            pass

        def c():
            pass

        self.pc.registerClass(meta_type="test", permission="test",
                              constructors=(initial, ("name", c),))
        self._verify_reg("name", "c")

    def test_constructor_named(self):

        def initial():
            pass

        def c():
            pass

        self.pc.registerClass(meta_type="test", permission="test",
                              constructors=(initial, c,))
        self._verify_reg("c", "c")

    def test_constructor_noncallable(self):

        def initial():
            pass

        nc = SimpleNamespace(__name__="nc")
        with self.assertWarns(DeprecationWarning):
            self.pc.registerClass(meta_type="test", permission="test",
                                  constructors=(initial, nc))
        self._verify_reg("nc", nc)

    def test_resource_tuple(self):

        def initial():
            pass

        r = SimpleNamespace()
        self.pc.registerClass(meta_type="test", permission="test",
                              constructors=(initial,),
                              resources=(("r", r),))
        self._verify_reg("r", r)

    def test_resource_named(self):

        def initial():
            pass

        r = SimpleNamespace(__name__="r")
        self.pc.registerClass(meta_type="test", permission="test",
                              constructors=(initial,),
                              resources=(r,))
        self._verify_reg("r", r)

    def _verify_reg(self, name, obj):
        pack = self.args[-1]
        m = pack._m
        fo = m[name]
        if isinstance(obj, str):
            self.assertEqual(obj, fo.__name__)
            self.assertTrue(zpublish_marked(fo))
        else:
            self.assertIs(obj, fo)


class _Product:
    """Product mockup."""

    def __init__(self):
        self.id = "pid"


class _App:
    """Application mockup"""


class _ApplicationDefaultPermissions:
    """ApplicationDefaultPermissions mockup."""


class _Attr(SimpleNamespace):
    """an attribute."""

    def get(self):
        return getattr(self.o, self.a)

    def set(self, val):
        setattr(self.o, self.a, val)


class _Item(SimpleNamespace):
    """a (mapping) item."""

    def get(self):
        # we use ``_Item`` for missiong
        return self.o.get(self.a, _Item)

    def set(self, val):
        # we use ``_Item`` for missiong
        if val is _Item:
            del self.o[self.a]
        else:
            self.o[self.a] = val


def _resolve(spec):
    """resolve *spec* into an ``_Attr`` or ``_Item``.

    *spec* is a dotted name, optionally followed by a subscription.
    """
    if "[" in spec:
        dotted, sub = spec[:-1].split("[")
    else:
        dotted, sub = spec, None
    o = None
    segs = dotted.split(".")
    for i in range(0, len(segs) - (0 if sub is not None else 1)):
        seg = segs[i]
        o = getattr(o, seg, None)
        if o is None:
            o = __import__(".".join(segs[:i + 1]), fromlist=(seg,))
    return _Attr(o=o, a=segs[-1]) if sub is None else _Item(o=o, a=eval(sub))
