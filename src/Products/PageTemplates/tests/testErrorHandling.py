##############################################################################
#
# Copyright (c) 2019 Zope Foundation and Contributors.
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

from zope.component.testing import PlacelessSetup

from ..PageTemplate import PageTemplate
from .util import useChameleonEngine


class ErrorHandlingTests(PlacelessSetup, TestCase):
    def setUp(self):
        super().setUp()
        useChameleonEngine()

    def test_repr_error_info(self):
        class WithRepr:
            def __repr__(self):
                return "with repr"

        t = PageTemplate()
        t.write("<div tal:content='python: 1/0'/>")
        try:
            t(obj=WithRepr())
        except ZeroDivisionError as e:
            self.assertIn("'obj': with repr", str(e))
