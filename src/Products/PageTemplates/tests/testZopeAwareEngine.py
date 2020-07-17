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

from zope.component import provideAdapter
from zope.component.testing import PlacelessSetup
from zope.pagetemplate.engine import Engine as base_engine

from ..engine import Program
from ..expression import getEngine as getChameleonEngine
from ..Expressions import getEngine as getZopeEngine
from ..interfaces import IZopeAwareEngine


def adapt(engine):
    return getZopeEngine()


class TestsWithoutAdapter(PlacelessSetup, TestCase):
    def test_ch_engine(self):
        self.check(getChameleonEngine())

    def test_zope_engine(self):
        self.check(getZopeEngine())

    def test_base_engine(self):
        self.check(base_engine, getZopeEngine())

    def check(self, engine, zengine=None):
        zengine = self.should(zengine)
        if zengine is None:
            zengine = engine
        p = Program(None, engine)
        self.assertIs(p.engine, zengine)

    def should(self, zengine):
        # without adapter, we must ignore *zengine*
        return


class TestWithsAdapter(TestsWithoutAdapter):
    def setUp(self):
        super().setUp()
        provideAdapter(adapt, (None,), IZopeAwareEngine)

    def should(self, zengine):
        # with adapter, *zengine* specifies the result
        return zengine
