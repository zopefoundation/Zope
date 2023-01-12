import unittest

from Products.Five import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Testing.ZopeTestCase import ZopeTestCase

from .util import useChameleonEngine


class SimpleView(BrowserView):
    index = ViewPageTemplateFile('simple.pt')


class ProcessingInstructionTestView(BrowserView):
    index = ViewPageTemplateFile('pi.pt')


class LocalsView(BrowserView):
    def available(self):
        return 'yes'

    index = ViewPageTemplateFile('locals.pt')


class OptionsView(BrowserView):
    index = ViewPageTemplateFile('options.pt')


class SecureView(BrowserView):
    index = ViewPageTemplateFile('secure.pt')

    __allow_access_to_unprotected_subobjects__ = True

    def tagsoup(self):
        return '<foo></bar>'


class MissingView(BrowserView):
    index = ViewPageTemplateFile('missing.pt')


class TestPageTemplateFile(ZopeTestCase):

    def afterSetUp(self):
        useChameleonEngine()

    def test_simple(self):
        view = SimpleView(self.folder, self.folder.REQUEST)
        result = view.index()
        self.assertTrue('Hello world!' in result)

    def test_secure(self):
        view = SecureView(self.folder, self.folder.REQUEST)
        from zExceptions import Unauthorized
        try:
            result = view.index()
        except Unauthorized:
            self.fail("Unexpected exception.")
        else:
            self.assertTrue('&lt;foo&gt;&lt;/bar&gt;' in result)

    def test_locals(self):
        view = LocalsView(self.folder, self.folder.REQUEST)
        result = view.index()
        self.assertTrue("view:yes" in result)
        self.assertTrue('here==context:True' in result)
        self.assertTrue('here==container:True' in result)
        self.assertTrue("root:(\'\',)" in result)
        self.assertTrue("nothing:" in result)
        # test for the existence of the cgi.parse function
        self.assertTrue("parse" in result)

    def test_options(self):
        view = OptionsView(self.folder, self.folder.REQUEST)
        options = dict(
            a=1,
            b=2,
            c='abc',
        )
        result = view.index(**options)
        self.assertTrue("a : 1" in result)
        self.assertTrue("c : abc" in result)

    def test_processing_instruction(self):
        view = ProcessingInstructionTestView(self.folder, self.folder.REQUEST)
        self.assertRaises(ZeroDivisionError, view.index)


def test_suite():
    return unittest.defaultTestLoader.loadTestsFromTestCase(
        TestPageTemplateFile)
