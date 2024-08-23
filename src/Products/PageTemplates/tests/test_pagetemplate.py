import os
import unittest

from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from Testing.ZopeTestCase import ZopeTestCase
from zope.component import provideAdapter
from zope.traversing.adapters import DefaultTraversable

from .util import useChameleonEngine


path = os.path.dirname(__file__)


class TestPageTemplateFile(ZopeTestCase):

    def afterSetUp(self):
        useChameleonEngine()
        provideAdapter(DefaultTraversable, (None,))

    def _makeOne(self, name):
        return PageTemplateFile(os.path.join(path, name)).__of__(self.app)

    def test_rr(self):
        class Prioritized:
            __allow_access_to_unprotected_subobjects__ = 1

            def __init__(self, order):
                self.order = order

            def __str__(self):
                return 'P%d' % self.order

        template = self._makeOne('rr.pt')
        result = template(refs=[Prioritized(1), Prioritized(2)])
        self.assertIn('P1', result)
        self.assertLess(result.index('P1'), result.index('P2'))

    def test_locals(self):
        template = self._makeOne('locals.pt')
        result = template()
        self.assertIn('function test', result)
        self.assertIn('function same_type', result)

    def test_locals_base(self):
        template = self._makeOne('locals_base.pt')
        result = template()
        self.assertIn('Application', result)

    def test_nocall(self):
        template = self._makeOne("nocall.pt")

        def dont_call():
            raise RuntimeError()
        result = template(callable=dont_call)
        self.assertIn(repr(dont_call), result)

    def test_exists(self):
        template = self._makeOne("exists.pt")

        def dont_call():
            raise RuntimeError()
        result = template(callable=dont_call)
        self.assertIn('ok', result)

    def test_simple(self):
        template = self._makeOne("simple.pt")
        result = template()
        self.assertIn('Hello world!', result)

    def test_secure(self):
        soup = '<foo></bar>'
        template = self._makeOne("secure.pt")
        from zExceptions import Unauthorized
        try:
            result = template(soup=soup)
        except Unauthorized:
            pass
        else:
            self.fail("Expected unauthorized.")

        from AccessControl.SecurityInfo import allow_module
        allow_module('html')
        result = template(soup=soup)
        self.assertIn('&lt;foo&gt;&lt;/bar&gt;', result)

    def test_structure(self):
        template = self._makeOne("structure.pt")
        param = "<span>abc</span>"
        result = template(param=param)
        self.assertIn(param, result)


def test_suite():
    return unittest.defaultTestLoader.loadTestsFromTestCase(
        TestPageTemplateFile)
