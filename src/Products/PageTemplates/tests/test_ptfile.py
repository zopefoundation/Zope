"""Tests of PageTemplateFile."""

import os
import os.path
import tempfile
import unittest
import Zope2
import transaction

from Testing.makerequest import makerequest

from Products.PageTemplates.PageTemplateFile import PageTemplateFile


class TypeSniffingTestCase(unittest.TestCase):

    TEMPFILENAME = tempfile.mktemp(".zpt")

    def setUp(self):
        from zope.component import provideUtility
        from Products.PageTemplates.interfaces import \
            IUnicodeEncodingConflictResolver
        from Products.PageTemplates.unicodeconflictresolver import \
            DefaultUnicodeEncodingConflictResolver
        provideUtility(DefaultUnicodeEncodingConflictResolver,
                       IUnicodeEncodingConflictResolver)

    def tearDown(self):
        if os.path.exists(self.TEMPFILENAME):
            os.unlink(self.TEMPFILENAME)

    def check_content_type(self, text, expected_type):
        f = open(self.TEMPFILENAME, "wb")
        f.write(text)
        f.close()
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
            b"\xef\xbb\xbf<?xml version='1.0' encoding='utf-8'?><doc/>",
            "text/xml")
        self.check_content_type(
            b"\xef\xbb\xbf<?xml\tversion='1.0' encoding='utf-8'?><doc/>",
            "text/xml")

    def test_sniffer_xml_utf16_be(self):
        # w/out byte order mark
        self.check_content_type(
            b"\0<\0?\0x\0m\0l\0 \0v\0e\0r\0s\0i\0o\0n\0=\0'\01\0.\0000\0'"
            b"\0 \0e\0n\0c\0o\0d\0i\0n\0g\0=\0'\0u\0t\0f\0-\08\0'\0?\0>"
            b"\0<\0d\0o\0c\0/\0>",
            "text/xml")
        self.check_content_type(
            b"\0<\0?\0x\0m\0l\0\t\0v\0e\0r\0s\0i\0o\0n\0=\0'\01\0.\0000\0'"
            b"\0 \0e\0n\0c\0o\0d\0i\0n\0g\0=\0'\0u\0t\0f\0-\08\0'\0?\0>"
            b"\0<\0d\0o\0c\0/\0>",
            "text/xml")
        # with byte order mark
        self.check_content_type(
            b"\xfe\xff"
            b"\0<\0?\0x\0m\0l\0 \0v\0e\0r\0s\0i\0o\0n\0=\0'\01\0.\0000\0'"
            b"\0 \0e\0n\0c\0o\0d\0i\0n\0g\0=\0'\0u\0t\0f\0-\08\0'\0?\0>"
            b"\0<\0d\0o\0c\0/\0>",
            "text/xml")
        self.check_content_type(
            b"\xfe\xff"
            b"\0<\0?\0x\0m\0l\0\t\0v\0e\0r\0s\0i\0o\0n\0=\0'\01\0.\0000\0'"
            b"\0 \0e\0n\0c\0o\0d\0i\0n\0g\0=\0'\0u\0t\0f\0-\08\0'\0?\0>"
            b"\0<\0d\0o\0c\0/\0>",
            "text/xml")

    def test_sniffer_xml_utf16_le(self):
        # w/out byte order mark
        self.check_content_type(
            b"<\0?\0x\0m\0l\0 \0v\0e\0r\0s\0i\0o\0n\0=\0'\01\0.\0000\0'\0"
            b" \0e\0n\0c\0o\0d\0i\0n\0g\0=\0'\0u\0t\0f\0-\08\0'\0?\0>\0"
            b"<\0d\0o\0c\0/\0>\n",
            "text/xml")
        self.check_content_type(
            b"<\0?\0x\0m\0l\0\t\0v\0e\0r\0s\0i\0o\0n\0=\0'\01\0.\0000\0'\0"
            b" \0e\0n\0c\0o\0d\0i\0n\0g\0=\0'\0u\0t\0f\0-\08\0'\0?\0>\0"
            b"<\0d\0o\0c\0/\0>\0",
            "text/xml")
        # with byte order mark
        self.check_content_type(
            b"\xff\xfe"
            b"<\0?\0x\0m\0l\0 \0v\0e\0r\0s\0i\0o\0n\0=\0'\01\0.\0000\0'\0"
            b" \0e\0n\0c\0o\0d\0i\0n\0g\0=\0'\0u\0t\0f\0-\08\0'\0?\0>\0"
            b"<\0d\0o\0c\0/\0>\0",
            "text/xml")
        self.check_content_type(
            b"\xff\xfe"
            b"<\0?\0x\0m\0l\0\t\0v\0e\0r\0s\0i\0o\0n\0=\0'\01\0.\0000\0'\0"
            b" \0e\0n\0c\0o\0d\0i\0n\0g\0=\0'\0u\0t\0f\0-\08\0'\0?\0>\0"
            b"<\0d\0o\0c\0/\0>\0",
            "text/xml")

    HTML_PUBLIC_ID = b"-//W3C//DTD HTML 4.01 Transitional//EN"
    HTML_SYSTEM_ID = b"http://www.w3.org/TR/html4/loose.dtd"

    def test_sniffer_html_ascii(self):
        self.check_content_type(
            b"<!DOCTYPE html [ SYSTEM '" + self.HTML_SYSTEM_ID + b"' ]><html></html>",
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
            'getId() returned %r. Expecting %r' % (pt_id, desired_id)
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
            'getPhysicalPath() returned %r. Expecting %r' % (
                desired_path, pt_path,
            )
        )


class LineEndingsTestCase(unittest.TestCase):

    TEMPFILENAME = tempfile.mktemp(".zpt")
    TAL = (b'''<html tal:replace="python: ' '.join(('foo',''',
           b'''                                    'bar',''',
           b'''                                    'spam',''',
           b'''                                    'eggs'))"></html>''')
    OUTPUT = 'foo bar spam eggs'

    def setUp(self):
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

    TEMPFILENAME = tempfile.mktemp(".zpt")

    def tearDown(self):
        if os.path.exists(self.TEMPFILENAME):
            os.unlink(self.TEMPFILENAME)

    def test_lazy(self):
        f = open(self.TEMPFILENAME, 'wb')
        f.write(b'Laziness')
        f.close()
        pt = PageTemplateFile(self.TEMPFILENAME)
        self.assertTrue(not pt._text and not pt._v_program)
