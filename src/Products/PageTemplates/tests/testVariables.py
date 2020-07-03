from unittest import TestCase

from OFS.Folder import Folder
from zope.component.testing import PlacelessSetup

from ..Expressions import getTrustedEngine
from ..ZopePageTemplate import ZopePageTemplate
from .util import useChameleonEngine


class PageTemplate(ZopePageTemplate):
    def pt_getEngine(self):
        return getTrustedEngine()


class TestPredefinedVariables(PlacelessSetup, TestCase):
    """test predefined variables

    as documented by
    `<https://zope.readthedocs.io/en/latest/zopebook/AppendixC.html#built-in-names`_
    """
    def setUp(self):
        super(TestPredefinedVariables, self).setUp()

        def add(dest, id, factory):
            nid = dest._setObject(id, factory(id))
            obj = dest._getOb(nid)
            if hasattr(obj, "_setId"):
                obj._setId(nid)
            return obj

        self.root = Folder()
        self.root.getPhysicalRoot = lambda: self.root
        self.f = add(self.root, "f", Folder)
        self.g = add(self.f, "g", Folder)
        self.template = add(self.f, "t", PageTemplate)
        # useChameleonEngine()

    def test_nothing(self):
        self.assertIsNone(self.check("nothing"))

    def test_default(self):
        self.assertTrue(self.check("default"))

    def test_options(self):
        self.assertTrue(self.check("options"))

    def test_repeat(self):
        self.check("repeat")

    def test_attrs(self):
        attrs = self.check("attrs")
        self.assertEqual(attrs["attr"], "attr")

    def test_root(self):
        self.assertEqual(self.check("root"), self.root)

    def test_context(self):
        self.assertEqual(self.check("context"), self.g)

    def test_container(self):
        self.assertEqual(self.check("container"), self.f)

    def test_template(self):
        self.assertEqual(self.check("template"), self.template)

    def test_request(self):
        self.check("request")

    def test_user(self):
        self.check("user")

    def test_modules(self):
        self.check("modules")

    def check(self, what):
        t = self.g.t
        t.write("<div attr='attr' "
                """tal:define="dummy python:options['acc'].append(%s)"/>"""
                % what)
        acc = []
        t(acc=acc)
        return acc[0]


class TestPredefinedVariables_chameleon(TestPredefinedVariables):
    def setUp(self):
        super(TestPredefinedVariables_chameleon, self).setUp()
        useChameleonEngine()
