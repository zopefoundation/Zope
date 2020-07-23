##############################################################################
#
# Copyright (c) 2020 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################

from unittest import TestCase

from z3c.pt import pagetemplate
from zope.component import provideAdapter
from zope.component.testing import PlacelessSetup
from zope.i18nmessageid import ZopeMessageFactory as _
from zope.traversing.adapters import DefaultTraversable

from ..PageTemplate import PageTemplate
from .util import useChameleonEngine


def translate(*args, **kw):
    return "translated"


class TranslationLayer:
    """set up our translation function."""
    @classmethod
    def setUp(cls):
        cls._saved_translate = pagetemplate.fast_translate
        pagetemplate.fast_translate = translate

    @classmethod
    def tearDown(cls):
        pagetemplate.fast_translate = cls.__dict__["_saved_translate"]


class TranslationTests(PlacelessSetup, TestCase):
    layer = TranslationLayer

    def setUp(self):
        super().setUp()
        provideAdapter(DefaultTraversable, (None,))
        useChameleonEngine()

    def test_translation_body(self):
        t = PageTemplate()
        t.write("""<p i18n:translate="">text</p>""")
        self.assertEqual(t(), "<p>translated</p>")

    def test_translation_content(self):
        t = PageTemplate()
        t.write("""<p i18n:translate="" tal:content="string:x">text</p>""")
        self.assertEqual(t(), "<p>translated</p>")

    def test_translation_replace(self):
        t = PageTemplate()
        t.write("""<p i18n:translate="" tal:replace="string:x">text</p>""")
        self.assertEqual(t(), "translated")

    def test_translation_msgid(self):
        t = PageTemplate()
        t.write("""<p tal:replace="options/msgid">text</p>""")
        self.assertEqual(t(msgid=_("x")), "translated")

    def test_no_translation_body(self):
        t = PageTemplate()
        t.write("""<p>text</p>""")
        self.assertEqual(t(), "<p>text</p>")

    def test_no_translation_content(self):
        t = PageTemplate()
        t.write("""<p tal:content="string:x">text</p>""")
        self.assertEqual(t(), "<p>x</p>")

    def test_no_translation_replace(self):
        t = PageTemplate()
        t.write("""<p tal:replace="string:x">text</p>""")
        self.assertEqual(t(), "x")
