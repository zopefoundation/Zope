#! /usr/bin/env python1.5
"""Tests for XMLParser.py."""

import string
import sys

from TAL.tests import utils
import unittest

from TAL import XMLParser


class EventCollector(XMLParser.XMLParser):

    def __init__(self):
        self.events = []
        self.append = self.events.append
        XMLParser.XMLParser.__init__(self)
        self.parser.ordered_attributes = 1

    def get_events(self):
        # Normalize the list of events so that buffer artefacts don't
        # separate runs of contiguous characters.
        L = []
        prevtype = None
        for event in self.events:
            type = event[0]
            if type == prevtype == "data":
                L[-1] = ("data", L[-1][1] + event[1])
            else:
                L.append(event)
            prevtype = type
        self.events = L
        return L

    # structure markup

    def StartElementHandler(self, tag, attrs):
        self.append(("starttag", tag, attrs))

    def EndElementHandler(self, tag):
        self.append(("endtag", tag))

    # all other markup

    def CommentHandler(self, data):
        self.append(("comment", data))

    def handle_charref(self, data):
        self.append(("charref", data))

    def CharacterDataHandler(self, data):
        self.append(("data", data))

    def StartDoctypeDeclHandler(self, rootelem, publicId, systemId, subset):
        self.append(("doctype", rootelem, systemId, publicId, subset))

    def XmlDeclHandler(self, version, encoding, standalone):
        self.append(("decl", version, encoding, standalone))

    def ExternalEntityRefHandler(self, data):
        self.append(("entityref", data))

    def ProcessingInstructionHandler(self, target, data):
        self.append(("pi", target, data))


class EventCollectorExtra(EventCollector):

    def handle_starttag(self, tag, attrs):
        EventCollector.handle_starttag(self, tag, attrs)
        self.append(("starttag_text", self.get_starttag_text()))


class SegmentedFile:
    def __init__(self, parts):
        self.parts = list(parts)

    def read(self, bytes):
        if self.parts:
            s = self.parts.pop(0)
        else:
            s = ''
        return s


class XMLParserTestCase(unittest.TestCase):

    def _run_check(self, source, events, collector=EventCollector):
        parser = collector()
        if isinstance(source, type([])):
            parser.parseStream(SegmentedFile(source))
        else:
            parser.parseString(source)
        if utils.oldexpat:
            while events[0][0] in ('decl', 'doctype'):
                del events[0]
        self.assertEquals(parser.get_events(), events)

    def _run_check_extra(self, source, events):
        self._run_check(source, events, EventCollectorExtra)

    def _parse_error(self, source):
        def parse(source=source):
            parser = XMLParser.XMLParser()
            parser.parseString(source)
        self.assertRaises(XMLParser.XMLParseError, parse)

    def check_processing_instruction_plus(self):
        self._run_check("<?processing instruction?><a/>", [
            ("pi", "processing", "instruction"),
            ("starttag", "a", []),
            ("endtag", "a"),
            ])

    def _check_simple_html(self):
        self._run_check("""\
<?xml version='1.0' encoding='iso-8859-1'?>
<!DOCTYPE html PUBLIC 'foo' 'bar'>
<html>&entity;&#32;
<!--comment1a
-></foo><bar>&lt;<?pi?></foo<bar
comment1b-->
<img src='Bar' ismap=''/>sample
text
<!--comment2a- -comment2b-->
</html>
""", [
    ("decl", "1.0", "iso-8859-1", -1),
    ("doctype", "html", "foo", "bar", 0),
    ("starttag", "html", []),
#    ("entityref", "entity"),
    ("data", " \n"),
    ("comment", "comment1a\n-></foo><bar>&lt;<?pi?></foo<bar\ncomment1b"),
    ("data", "\n"),
    ("starttag", "img", ["src", "Bar", "ismap", ""]),
    ("endtag", "img"),
    ("data", "sample\ntext\n"),
    ("comment", "comment2a- -comment2b"),
    ("data", "\n"),
    ("endtag", "html"),
    ])

    def check_bad_nesting(self):
        try:
            self._run_check("<a><b></a></b>", [
                ("starttag", "a", []),
                ("starttag", "b", []),
                ("endtag", "a"),
                ("endtag", "b"),
                ])
        except:
            e = sys.exc_info()[1]
            self.assert_(e.lineno == 1,
                         "did not receive correct position information")
        else:
            self.fail("expected parse error: bad nesting")

    def check_attr_syntax(self):
        output = [
          ("starttag", "a", ["b", "v", "c", "v"]),
          ("endtag", "a"),
          ]
        self._run_check("""<a b='v' c="v"/>""", output)
        self._run_check("""<a  b = 'v' c = "v"/>""", output)
        self._run_check("""<a\nb\n=\n'v'\nc\n=\n"v"\n/>""", output)
        self._run_check("""<a\tb\t=\t'v'\tc\t=\t"v"\t/>""", output)

    def check_attr_values(self):
        self._run_check("""<a b='xxx\n\txxx' c="yyy\t\nyyy" d='\txyz\n'/>""",
                        [("starttag", "a", ["b", "xxx  xxx",
                                            "c", "yyy  yyy",
                                            "d", " xyz "]),
                         ("endtag", "a"),
                         ])
        self._run_check("""<a b='' c="" d=''/>""", [
            ("starttag", "a", ["b", "", "c", "", "d", ""]),
            ("endtag", "a"),
            ])

    def check_attr_entity_replacement(self):
        self._run_check("""<a b='&amp;&gt;&lt;&quot;&apos;'/>""", [
            ("starttag", "a", ["b", "&><\"'"]),
            ("endtag", "a"),
            ])

    def check_attr_funky_names(self):
        self._run_check("""<a a.b='v' e-f='v'/>""", [
            ("starttag", "a", ["a.b", "v", "e-f", "v"]),
            ("endtag", "a"),
            ])

    def check_starttag_end_boundary(self):
        self._run_check("""<a b='&lt;'/>""", [
            ("starttag", "a", ["b", "<"]),
            ("endtag", "a"),
            ])
        self._run_check("""<a b='&gt;'/>""", [
            ("starttag", "a", ["b", ">"]),
            ("endtag", "a"),
            ])

    def check_buffer_artefacts(self):
        output = [("starttag", "a", ["b", "<"]), ("endtag", "a")]
        self._run_check(["<a b='&lt;'/>"], output)
        self._run_check(["<a ", "b='&lt;'/>"], output)
        self._run_check(["<a b", "='&lt;'/>"], output)
        self._run_check(["<a b=", "'&lt;'/>"], output)
        self._run_check(["<a b='&lt;", "'/>"], output)
        self._run_check(["<a b='&lt;'", "/>"], output)

        output = [("starttag", "a", ["b", ">"]), ("endtag", "a")]
        self._run_check(["<a b='&gt;'/>"], output)
        self._run_check(["<a ", "b='&gt;'/>"], output)
        self._run_check(["<a b", "='&gt;'/>"], output)
        self._run_check(["<a b=", "'&gt;'/>"], output)
        self._run_check(["<a b='&gt;", "'/>"], output)
        self._run_check(["<a b='&gt;'", "/>"], output)

    def check_starttag_junk_chars(self):
        self._parse_error("<")
        self._parse_error("<>")
        self._parse_error("</>")
        self._parse_error("</$>")
        self._parse_error("</")
        self._parse_error("</a")
        self._parse_error("</a")
        self._parse_error("<a<a>")
        self._parse_error("</a<a>")
        self._parse_error("<$")
        self._parse_error("<$>")
        self._parse_error("<!")
        self._parse_error("<a $>")
        self._parse_error("<a")
        self._parse_error("<a foo='bar'")
        self._parse_error("<a foo='bar")
        self._parse_error("<a foo='>'")
        self._parse_error("<a foo='>")

    def check_declaration_junk_chars(self):
        self._parse_error("<!DOCTYPE foo $ >")


# Support for the Zope regression test framework:
def test_suite(skipxml=utils.skipxml):
    suite = unittest.TestSuite()
    if not skipxml:
        suite.addTest(unittest.makeSuite(XMLParserTestCase, "check_"))
    return suite


if __name__ == "__main__":
    errs = utils.run_suite(test_suite(skipxml=0))
    sys.exit(errs and 1 or 0)
