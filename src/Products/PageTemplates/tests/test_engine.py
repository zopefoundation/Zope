import os
import unittest

from Testing.ZopeTestCase import ZopeTestCase
from Testing.ZopeTestCase.sandbox import Sandboxed

from .util import useChameleonEngine


path = os.path.dirname(__file__)


class TestPatches(Sandboxed, ZopeTestCase):

    def afterSetUp(self):
        useChameleonEngine()

    def test_pagetemplate(self):
        from Products.PageTemplates.PageTemplate import PageTemplate
        template = PageTemplate()

        # test rendering engine
        with open(os.path.join(path, "simple.pt")) as fd:
            data = fd.read()
        template.write(data)
        self.assertTrue('world' in template())

        # test arguments
        with open(os.path.join(path, "options.pt")) as fd:
            data = fd.read()
        template.write(data)
        self.assertTrue('Hello world' in template(greeting='Hello world'))

    def test_pagetemplatefile(self):
        from Products.PageTemplates.PageTemplateFile import PageTemplateFile

        # test rendering engine
        template = PageTemplateFile(os.path.join(path, "simple.pt"))
        template = template.__of__(self.folder)
        self.assertTrue('world' in template())

    def test_pagetemplatefile_processing_instruction_skipped(self):
        from Products.PageTemplates.PageTemplateFile import PageTemplateFile

        # test rendering engine
        template = PageTemplateFile(os.path.join(path, "pi.pt"))
        template = template.__of__(self.folder)
        self.assertIn('world', template())

    def test_zopepagetemplate(self):
        from Products.PageTemplates.ZopePageTemplate import \
            manage_addPageTemplate
        template = manage_addPageTemplate(self.folder, 'test')

        # aq-wrap before we proceed
        template = template.__of__(self.folder)

        # test rendering engine
        with open(os.path.join(path, "simple.pt")) as fd:
            data = fd.read()
        template.write(data)
        self.assertTrue('world' in template())

        # test arguments
        with open(os.path.join(path, "options.pt")) as fd:
            data = fd.read()
        template.write(data)
        self.assertTrue('Hello world' in template(
            greeting='Hello world'))

        # test commit
        import transaction
        transaction.commit()

    def test_zopepagetemplate_processing_instruction_skipped(self):
        from Products.PageTemplates.ZopePageTemplate import \
            manage_addPageTemplate
        template = manage_addPageTemplate(self.folder, 'test')

        # aq-wrap before we proceed
        template = template.__of__(self.folder)

        # test rendering engine
        with open(os.path.join(path, "pi.pt")) as fd:
            data = fd.read()
        template.write(data)
        self.assertIn('world', template())

    def test_macros_access(self):
        from Products.PageTemplates.ZopePageTemplate import \
            manage_addPageTemplate
        from zExceptions import Unauthorized
        template = manage_addPageTemplate(self.folder, 'test')

        # aq-wrap before we proceed
        template = template.__of__(self.folder)

        # test rendering engine
        with open(os.path.join(path, "macros.pt")) as fd:
            data = fd.read()
        template.write(data)
        try:
            output = template()
            raised = False
        except Unauthorized:
            raised = True
        self.assertFalse(raised, 'Unauthorized exception raised')
        self.assertIn('<i>bar</i><i>bar</i><i>bar</i>', output)


def test_suite():
    return unittest.defaultTestLoader.loadTestsFromTestCase(TestPatches)
