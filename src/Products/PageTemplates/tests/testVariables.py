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

    # variables documented in the Zope Book
    VARIABLES = {
        "nothing",
        "default",
        "options",
        "repeat",
        # "attrs",  # special -- not contained in ``CONTEXTS``
        "root",
        "context",
        "container",
        "template",
        "request",
        "user",
        "modules",
        #   special
        #     - only usable as initial component in path expr
        #     - not contained in ``CONTEXTS``
        # "CONTEXTS",
    }

    def setUp(self):
        super().setUp()

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

    # ``test_attrs`` should have the previous definition
    # Unfortunately, "https://github.com/malthe/chameleon/issues/323"
    # (``attrs`` cannot be used in ``tal:define``)
    # lets it fail.
    # We must therefore test (what works with the current
    # ``chameleon``) in a different way.
    # Note ``chameleon > 3.8.0`` likely will allow the previous definition
    def test_attrs(self):  # noqa: F811
        t = self.g.t
        t.write("<div attr='attr' tal:content='python: attrs[\"attr\"]'/>")
        # the two template engines use different quotes - we
        #  must normalize
        self.assertEqual(t().replace("'", '"'), '<div attr="attr">attr</div>')

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

    def test_CONTEXTS(self):
        # the "Zope Book" describes ``CONTEXTS`` as a variable.
        # But, in fact, it is not a (regular) variable but a special
        # case of the initial component of a (sub)path expression.
        # As a consequence, it cannot be used in a Python expression
        # but only as the first component in a path expression
        # Therefore, we cannot use ``check`` to access it.
        t = self.g.t
        t.write("""<div tal:define="
                x CONTEXTS;
                dummy python:options['acc'].append(x)" />""")
        acc = []
        t(acc=acc)
        ctx = acc[0]
        self.assertIsInstance(ctx, dict)
        # all variables included?
        self.assertEqual(len(self.VARIABLES - set(ctx)), 0)

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
        super().setUp()
        useChameleonEngine()
