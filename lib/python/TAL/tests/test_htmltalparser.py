#! /usr/bin/env python1.5
"""Tests for the HTMLTALParser code generator."""

import pprint
import sys

import utils
import unittest

from TAL import HTMLTALParser


class HTMLTALParserTestCases(unittest.TestCase):

    def _run_check(self, source, program, macros={}):
        parser = HTMLTALParser.HTMLTALParser()
        parser.parseString(source)
        got_program, got_macros = parser.getCode()
        self.assert_(got_program == program, got_program)
        self.assert_(got_macros == macros, got_macros)

    def _get_check(self, source, xxx=None):
        parser = HTMLTALParser.HTMLTALParser()
        parser.parseString(source)
        got_program, got_macros = parser.getCode()
        pprint.pprint(got_program)
        pprint.pprint(got_macros)

    def check_code_simple_identity(self):
        self._run_check("""<html a='b' b="c" c=d><title>My Title</html>""", [
            ('setPosition', (1, 0)),
            ('rawtext', '<html a="b" b="c" c="d">'),
            ('setPosition', (1, 22)),
            ('rawtext', '<title>My Title</title></html>'),
            ])

    def check_code_implied_list_closings(self):
        self._run_check("""<ul><li><p><p><li></ul>""", [
            ('setPosition', (1, 0)),
            ('rawtext', '<ul>'),
            ('setPosition', (1, 4)),
            ('rawtext', '<li>'),
            ('setPosition', (1, 8)),
            ('rawtext', '<p></p>'),
            ('setPosition', (1, 11)),
            ('rawtext', '<p></p></li>'),
            ('setPosition', (1, 14)),
            ('rawtext', '<li></li></ul>'),
            ])
        self._run_check("""<dl><dt><dt><dd><dd><ol><li><li></ol></dl>""", [
            ('setPosition', (1, 0)),
            ('rawtext', '<dl>'),
            ('setPosition', (1, 4)),
            ('rawtext', '<dt></dt>'),
            ('setPosition', (1, 8)),
            ('rawtext', '<dt></dt>'),
            ('setPosition', (1, 12)),
            ('rawtext', '<dd></dd>'),
            ('setPosition', (1, 16)),
            ('rawtext', '<dd>'),
            ('setPosition', (1, 20)),
            ('rawtext', '<ol>'),
            ('setPosition', (1, 24)),
            ('rawtext', '<li></li>'),
            ('setPosition', (1, 28)),
            ('rawtext', '<li></li></ol></dd></dl>'),
            ])

    def check_code_implied_table_closings(self):
        self._run_check("""<p>text <table><tr><th>head\t<tr><td>cell\t"""
                        """<table><tr><td>cell \n \t \n<tr>""", [
            ('setPosition', (1, 0)),
            ('rawtext', '<p>text</p> '),
            ('setPosition', (1, 8)),
            ('rawtext', '<table>'),
            ('setPosition', (1, 15)),
            ('rawtext', '<tr>'),
            ('setPosition', (1, 19)),
            ('rawtext', '<th>head</th></tr>\t'),
            ('setPosition', (1, 28)),
            ('rawtext', '<tr>'),
            ('setPosition', (1, 32)),
            ('rawtext', '<td>cell\t'),
            ('setPosition', (1, 41)),
            ('rawtext', '<table>'),
            ('setPosition', (1, 48)),
            ('rawtext', '<tr>'),
            ('setPosition', (1, 52)),
            ('rawtext', '<td>cell</td></tr> \n \t \n'),
            ('setPosition', (3, 0)),
            ('rawtext', '<tr></tr></table></td></tr></table>'),
            ])
        self._run_check("""<table><tr><td>cell """
                        """<table><tr><td>cell </table></table>""", [
            ('setPosition', (1, 0)),
            ('rawtext', '<table>'),
            ('setPosition', (1, 7)),
            ('rawtext', '<tr>'),
            ('setPosition', (1, 11)),
            ('rawtext', '<td>cell '),
            ('setPosition', (1, 20)),
            ('rawtext', '<table>'),
            ('setPosition', (1, 27)),
            ('rawtext', '<tr>'),
            ('setPosition', (1, 31)),
            ('rawtext', '<td>cell</td></tr> </table></td></tr></table>'),
            ])

    def check_code_bad_nesting(self):
        def check(self=self):
            self._run_check("<a><b></a></b>", [])
        self.assertRaises(HTMLTALParser.NestingError, check)

    def check_code_attr_syntax(self):
        output = [
            ('setPosition', (1, 0)),
            ('rawtext', '<a b="v" c="v" d="v" e></a>'),
            ]
        self._run_check("""<a b='v' c="v" d=v e>""", output)
        self._run_check("""<a  b = 'v' c = "v" d = v e>""", output)
        self._run_check("""<a\nb\n=\n'v'\nc\n=\n"v"\nd\n=\nv\ne>""", output)
        self._run_check("""<a\tb\t=\t'v'\tc\t=\t"v"\td\t=\tv\te>""", output)

    def check_code_attr_values(self):
        self._run_check(
            """<a b='xxx\n\txxx' c="yyy\t\nyyy" d='\txyz\n'>""",
            [('setPosition', (1, 0)),
             ('rawtext',
              '<a b="xxx\n\txxx" c="yyy\t\nyyy" d="\txyz\n"></a>')])
        self._run_check("""<a b='' c="" d=>""", [
            ('setPosition', (1, 0)),
            ('rawtext', '<a b="" c="" d=""></a>'),
            ])

    def check_code_attr_entity_replacement(self):
        # we expect entities *not* to be replaced by HTLMParser!
        self._run_check("""<a b='&amp;&gt;&lt;&quot;&apos;'>""", [
            ('setPosition', (1, 0)),
            ('rawtext', '<a b="&amp;&gt;&lt;&quot;\'"></a>'),
            ])
        self._run_check("""<a b='\"'>""", [
            ('setPosition', (1, 0)),
            ('rawtext', "<a b='\"'></a>"),
            ])
        self._run_check("""<a b='&'>""", [
            ('setPosition', (1, 0)),
            ('rawtext', '<a b="&amp;"></a>'),
            ])
        self._run_check("""<a b='<'>""", [
            ('setPosition', (1, 0)),
            ('rawtext', '<a b="&lt;"></a>'),
            ])

    def check_code_attr_funky_names(self):
        self._run_check("""<a a.b='v' c:d=v e-f=v>""", [
            ('setPosition', (1, 0)),
            ('rawtext', '<a a.b="v" c:d="v" e-f="v"></a>'),
            ])

    def check_code_pcdata_entityref(self):
        self._run_check("""&nbsp;""", [
            ('rawtext', '&nbsp;'),
            ])

    def check_code_short_endtags(self):
        self._run_check("""<html><img/></html>""", [
            ('setPosition', (1, 0)),
            ('rawtext', '<html>'),
            ('setPosition', (1, 6)),
            ('rawtext', '<img/></html>'),
            ])


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(HTMLTALParserTestCases, "check_"))
    return suite


if __name__ == "__main__":
    errs = utils.run_suite(test_suite())
    sys.exit(errs and 1 or 0)

