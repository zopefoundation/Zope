"""Tests of PageTemplateFile."""

import os
import os.path
import tempfile
import unittest

import transaction
import Zope2
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from Testing.makerequest import makerequest

from .util import useChameleonEngine


class TypeSniffingTestCase(unittest.TestCase):

    def setUp(self):
        from Products.PageTemplates.interfaces import \
            IUnicodeEncodingConflictResolver
        from Products.PageTemplates.unicodeconflictresolver import \
            DefaultUnicodeEncodingConflictResolver
        from zope.component import provideUtility

        with tempfile.NamedTemporaryFile(suffix=".zpt", delete=False) as fp:
            self.TEMPFILENAME = fp.name

        # Make sure we use the new default chameleon engine
        useChameleonEngine()
        provideUtility(DefaultUnicodeEncodingConflictResolver,
                       IUnicodeEncodingConflictResolver)

    def tearDown(self):
        if os.path.exists(self.TEMPFILENAME):
            os.unlink(self.TEMPFILENAME)

    def check_content_type(self, bytes, expected_type, encoding=None):
        with open(self.TEMPFILENAME, "wb") as f:
            f.write(bytes)
        if encoding:
            pt = PageTemplateFile(self.TEMPFILENAME, encoding=encoding)
        else:
            pt = PageTemplateFile(self.TEMPFILENAME)
        pt.read()
        self.assertEqual(pt.content_type, expected_type)

    def test_sniffer_xml_ascii(self):
        self.check_content_type(
            b"<?xml version='1.0' encoding='ascii'?><doc/>",
            "text/xml")
        self.check_content_type(
            b"<?xml\tversion='1.0' encoding='ascii'?><doc/>",
            "text/xml")

    def test_sniffer_xml_utf8(self):
        # w/out byte order mark
        self.check_content_type(
            b"<?xml version='1.0' encoding='utf-8'?><doc/>",
            "text/xml")
        self.check_content_type(
            b"<?xml\tversion='1.0' encoding='utf-8'?><doc/>",
            "text/xml")
        # with byte order mark
        self.check_content_type(
            b"<?xml version='1.0' encoding='utf-8'?><doc/>",
            "text/xml")
        self.check_content_type(
            b"<?xml\tversion='1.0' encoding='utf-8'?><doc/>",
            "text/xml")

    def test_sniffer_xml_utf16_be(self):
        u_example1 = '<?xml version=".0" encoding="utf-16-be"?><doc/>'
        u_example2 = '<?xml   version=".0" encoding="utf-16-be"?><doc/>'
        b_example1 = u_example1.encode('utf-16-be')
        b_example2 = u_example2.encode('utf-16-be')
        # w/out byte order mark
        self.check_content_type(b_example1, "text/xml", encoding='utf-16-be')
        self.check_content_type(b_example2, "text/xml", encoding='utf-16-be')
        # with byte order mark
        self.check_content_type(
            b"\xfe\xff" + b_example1, "text/xml", encoding='utf-16-be'
        )
        self.check_content_type(
            b"\xfe\xff" + b_example2, "text/xml", encoding='utf-16-be'
        )

    def test_sniffer_xml_utf16_le(self):
        u_example1 = '<?xml version=".0" encoding="utf-16-le"?><doc/>'
        u_example2 = '<?xml   version=".0" encoding="utf-16-le"?><doc/>'
        b_example1 = u_example1.encode('utf-16-le')
        b_example2 = u_example2.encode('utf-16-le')
        # w/out byte order mark
        self.check_content_type(b_example1, "text/xml", encoding='utf-16-le')
        self.check_content_type(b_example2, "text/xml", encoding='utf-16-le')
        # with byte order mark
        self.check_content_type(
            b"\xff\xfe" + b_example1, "text/xml", encoding='utf-16-le'
        )
        self.check_content_type(
            b"\xff\xfe" + b_example2, "text/xml", encoding='utf-16-le'
        )

    HTML_PUBLIC_ID = b"-//W3C//DTD HTML 4.01 Transitional//EN"
    HTML_SYSTEM_ID = b"http://www.w3.org/TR/html4/loose.dtd"

    def test_sniffer_html_ascii(self):
        self.check_content_type(
            (b"<!DOCTYPE html [ SYSTEM '"
             + self.HTML_SYSTEM_ID
             + b"' ]><html></html>"),
            "text/html")
        self.check_content_type(
            b"<html><head><title>sample document</title></head></html>",
            "text/html")

    # XXX This reflects a case that simply isn't handled by the
    # sniffer; there are many, but it gets it right more often than
    # before.
    def donttest_sniffer_xml_simple(self):
        self.check_content_type(b"<doc><element/></doc>",
                                "text/xml")

    def test_getId(self):
        desired_id = os.path.splitext(os.path.split(self.TEMPFILENAME)[-1])[0]
        f = open(self.TEMPFILENAME, 'wb')
        f.write(b'Boring')
        f.close()
        pt = PageTemplateFile(self.TEMPFILENAME)
        pt_id = pt.getId()
        self.assertEqual(
            pt_id, desired_id,
            f'getId() returned {pt_id!r}. Expecting {desired_id!r}'
        )

    def test_getPhysicalPath(self):
        desired_id = os.path.splitext(os.path.split(self.TEMPFILENAME)[-1])[0]
        desired_path = (desired_id,)
        f = open(self.TEMPFILENAME, 'wb')
        f.write(b'Boring')
        f.close()
        pt = PageTemplateFile(self.TEMPFILENAME)
        pt_path = pt.getPhysicalPath()
        self.assertEqual(
            pt_path, desired_path,
            f'getPhysicalPath() returned {desired_path!r}.'
            f' Expecting {pt_path!r}'
        )


class LineEndingsTestCase(unittest.TestCase):

    TAL = (b'''<html tal:replace="python: ' '.join(('foo',''',
           b'''                                    'bar',''',
           b'''                                    'spam',''',
           b'''                                    'eggs'))"></html>''')
    OUTPUT = 'foo bar spam eggs'

    def setUp(self):
        with tempfile.NamedTemporaryFile(suffix=".zpt", delete=False) as fp:
            self.TEMPFILENAME = fp.name
        transaction.begin()
        self.root = makerequest(Zope2.app())

    def tearDown(self):
        if os.path.exists(self.TEMPFILENAME):
            os.unlink(self.TEMPFILENAME)
        transaction.abort()
        self.root._p_jar.close()

    def runPTWithLineEndings(self, lineendings=b'\n'):
        text = lineendings.join(self.TAL)
        f = open(self.TEMPFILENAME, "wb")
        f.write(text)
        f.close()
        pt = PageTemplateFile(self.TEMPFILENAME).__of__(self.root)
        return pt()

    def test_unix(self):
        self.assertEqual(self.runPTWithLineEndings(), self.OUTPUT)

    def test_dos(self):
        self.assertEqual(self.runPTWithLineEndings(), self.OUTPUT)

    def test_mac(self):
        self.assertEqual(self.runPTWithLineEndings(), self.OUTPUT)


class LazyLoadingTestCase(unittest.TestCase):

    def setUp(self):
        with tempfile.NamedTemporaryFile(suffix=".zpt", delete=False) as fp:
            self.TEMPFILENAME = fp.name

    def tearDown(self):
        if os.path.exists(self.TEMPFILENAME):
            os.unlink(self.TEMPFILENAME)

    def test_lazy(self):
        f = open(self.TEMPFILENAME, 'wb')
        f.write(b'Laziness')
        f.close()
        pt = PageTemplateFile(self.TEMPFILENAME)
        self.assertTrue(not pt._text and not pt._v_program)


class RenderTestCase(unittest.TestCase):

    def testXMLPageTemplateFile(self):
        dirname = os.path.dirname(__file__)

        filename = os.path.join(dirname, 'utf8.xml')
        with open(filename, 'rb') as f:
            self.assertEqual(
                PageTemplateFile(filename).pt_render(),
                f.read().decode('utf8'),
            )
