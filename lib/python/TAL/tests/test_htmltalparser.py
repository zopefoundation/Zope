#! /usr/bin/env python1.5
"""Tests for the HTMLTALParser code generator."""

import pprint
import sys

import utils
import unittest

from TAL import HTMLTALParser
from TAL.TALDefs import TAL_VERSION


class TestCaseBase(unittest.TestCase):

    prologue = ""
    epilogue = ""
    initial_program = [('version', TAL_VERSION), ('mode', 'html')]
    final_program = []

    def _merge(self, p1, p2):
        if p1 and p2 and p1[-1][0] == 'rawtext' and p2[0][0] == 'rawtext':
            return p1[:-1] + [('rawtext', p1[-1][1] + p2[0][1])] + p2[1:]
        else:
            return p1+p2

    def _run_check(self, source, program, macros={}):
        parser = HTMLTALParser.HTMLTALParser()
        parser.parseString(self.prologue + source + self.epilogue)
        got_program, got_macros = parser.getCode()
        program = self._merge(self.initial_program, program)
        program = self._merge(program, self.final_program)
        self.assert_(got_program == program, got_program)
        self.assert_(got_macros == macros, got_macros)

    def _get_check(self, source, xxx=None):
        parser = HTMLTALParser.HTMLTALParser()
        parser.parseString(source)
        got_program, got_macros = parser.getCode()
        pprint.pprint(got_program)
        pprint.pprint(got_macros)


class HTMLTALParserTestCases(TestCaseBase):

    def check_code_simple_identity(self):
        self._run_check("""<html a='b' b="c" c=d><title>My Title</html>""", [
            ('rawtext', '<html a="b" b="c" c="d">'
                        '<title>My Title</title></html>'),
            ])

    def check_code_implied_list_closings(self):
        self._run_check("""<ul><li><p><p><li></ul>""", [
            ('rawtext', '<ul><li><p></p><p></p></li><li></li></ul>'),
            ])
        self._run_check("""<dl><dt><dt><dd><dd><ol><li><li></ol></dl>""", [
            ('rawtext', '<dl><dt></dt><dt></dt><dd></dd>'
                        '<dd><ol><li></li><li></li></ol></dd></dl>'),
            ])

    def check_code_implied_table_closings(self):
        self._run_check("""<p>text <table><tr><th>head\t<tr><td>cell\t"""
                        """<table><tr><td>cell \n \t \n<tr>""", [
            ('rawtext', '<p>text</p> <table><tr><th>head</th>'
                        '</tr>\t<tr><td>cell\t<table><tr><td>cell</td>'
                        '</tr> \n \t \n<tr></tr></table></td></tr></table>'),
            ])
        self._run_check("""<table><tr><td>cell """
                        """<table><tr><td>cell </table></table>""", [
            ('rawtext', '<table><tr><td>cell <table><tr><td>cell</td></tr>'
                        ' </table></td></tr></table>'),
            ])

    def check_code_bad_nesting(self):
        def check(self=self):
            self._run_check("<a><b></a></b>", [])
        self.assertRaises(HTMLTALParser.NestingError, check)

    def check_code_attr_syntax(self):
        output = [
            ('rawtext', '<a b="v" c="v" d="v" e></a>'),
            ]
        self._run_check("""<a b='v' c="v" d=v e>""", output)
        self._run_check("""<a  b = 'v' c = "v" d = v e>""", output)
        self._run_check("""<a\nb\n=\n'v'\nc\n=\n"v"\nd\n=\nv\ne>""", output)
        self._run_check("""<a\tb\t=\t'v'\tc\t=\t"v"\td\t=\tv\te>""", output)

    def check_code_attr_values(self):
        self._run_check(
            """<a b='xxx\n\txxx' c="yyy\t\nyyy" d='\txyz\n'>""", [
            ('rawtext',
             '<a b="xxx\n\txxx" c="yyy\t\nyyy" d="\txyz\n"></a>')])
        self._run_check("""<a b='' c="" d=>""", [
            ('rawtext', '<a b="" c="" d=""></a>'),
            ])

    def check_code_attr_entity_replacement(self):
        # we expect entities *not* to be replaced by HTLMParser!
        self._run_check("""<a b='&amp;&gt;&lt;&quot;&apos;'>""", [
            ('rawtext', '<a b="&amp;&gt;&lt;&quot;\'"></a>'),
            ])
        self._run_check("""<a b='\"'>""", [
            ('rawtext', "<a b='\"'></a>"),
            ])
        self._run_check("""<a b='&'>""", [
            ('rawtext', '<a b="&amp;"></a>'),
            ])
        self._run_check("""<a b='<'>""", [
            ('rawtext', '<a b="&lt;"></a>'),
            ])

    def check_code_attr_funky_names(self):
        self._run_check("""<a a.b='v' c:d=v e-f=v>""", [
            ('rawtext', '<a a.b="v" c:d="v" e-f="v"></a>'),
            ])

    def check_code_pcdata_entityref(self):
        self._run_check("""&nbsp;""", [
            ('rawtext', '&nbsp;'),
            ])

    def check_code_short_endtags(self):
        self._run_check("""<html><img/></html>""", [
            ('rawtext', '<html><img/></html>'),
            ])


class TALGeneratorTestCases(TestCaseBase):

    def check_null(self):
        self._run_check("", [])

    def check_define(self):
        self._run_check("<p tal:define='xyzzy string:spam'></p>", [
            ('setPosition', (1, 0)),
            ('beginScope',),
            ('setLocal', 'xyzzy', '$string:spam$'),
            ('rawtext', '<p tal:define="xyzzy string:spam"></p>'),
            ('endScope',),
            ])
        self._run_check("<p tal:define='local xyzzy string:spam'></p>", [
            ('setPosition', (1, 0)),
            ('beginScope',),
            ('setLocal', 'xyzzy', '$string:spam$'),
            ('rawtext', '<p tal:define="local xyzzy string:spam"></p>'),
            ('endScope',),
            ])
        self._run_check("<p tal:define='global xyzzy string:spam'></p>", [
            ('setPosition', (1, 0)),
            ('beginScope',),
            ('setGlobal', 'xyzzy', '$string:spam$'),
            ('rawtext', '<p tal:define="global xyzzy string:spam"></p>'),
            ('endScope',),
            ])
        self._run_check("<p tal:define='x string:spam; y x'></p>", [
            ('setPosition', (1, 0)),
            ('beginScope',),
            ('setLocal', 'x', '$string:spam$'),
            ('setLocal', 'y', '$x$'),
            ('rawtext', '<p tal:define="x string:spam; y x"></p>'),
            ('endScope',),
            ])
        self._run_check("<p tal:define='x string:;;;;; y x'></p>", [
            ('setPosition', (1, 0)),
            ('beginScope',),
            ('setLocal', 'x', '$string:;;$'),
            ('setLocal', 'y', '$x$'),
            ('rawtext', '<p tal:define="x string:;;;;; y x"></p>'),
            ('endScope',),
            ])
        self._run_check(
            "<p tal:define='x string:spam; global y x; local z y'></p>", [
            ('setPosition', (1, 0)),
            ('beginScope',),
            ('setLocal', 'x', '$string:spam$'),
            ('setGlobal', 'y', '$x$'),
            ('setLocal', 'z', '$y$'),
            ('rawtext',
             '<p tal:define="x string:spam; global y x; local z y"></p>'),
            ('endScope',),
            ])

    def check_condition(self):
        self._run_check(
            "<p><span tal:condition='python:1'><b>foo</b></span></p>", [
            ('rawtext', '<p>'),
            ('setPosition', (1, 3)),
            ('condition', '$python:1$',
             [('rawtext',
               '<span tal:condition="python:1"><b>foo</b></span>')]),
            ('rawtext', '</p>'),
            ])

    def check_content(self):
        self._run_check("<p tal:content='string:foo'>bar</p>", [
             ('setPosition', (1, 0)),
             ('rawtext', '<p tal:content="string:foo">'),
             ('insertText', '$string:foo$', [('rawtext', 'bar')]),
             ('rawtext', '</p>'),
             ])
        self._run_check("<p tal:content='text string:foo'>bar</p>", [
             ('setPosition', (1, 0)),
             ('rawtext', '<p tal:content="text string:foo">'),
             ('insertText', '$string:foo$', [('rawtext', 'bar')]),
             ('rawtext', '</p>'),
             ])
        self._run_check("<p tal:content='structure string:<br>'>bar</p>", [
             ('setPosition', (1, 0)),
             ('rawtext', '<p tal:content="structure string:&lt;br&gt;">'),
             ('insertStructure', '$string:<br>$', {}, [('rawtext', 'bar')]),
             ('rawtext', '</p>'),
             ])

    def check_replace(self):
        self._run_check("<p tal:replace='string:foo'>bar</p>", [
             ('setPosition', (1, 0)),
             ('insertText', '$string:foo$',
              [('rawtext', '<p tal:replace="string:foo">bar</p>')]),
             ])
        self._run_check("<p tal:replace='text string:foo'>bar</p>", [
             ('setPosition', (1, 0)),
             ('insertText', '$string:foo$',
              [('rawtext', '<p tal:replace="text string:foo">bar</p>')]),
             ])
        self._run_check("<p tal:replace='structure string:<br>'>bar</p>", [
             ('setPosition', (1, 0)),
             ('insertStructure', '$string:<br>$', {},
              [('rawtext',
                '<p tal:replace="structure string:&lt;br&gt;">bar</p>')]),
             ])

    def check_repeat(self):
        self._run_check("<p tal:repeat='x python:(1,2,3)'>"
                        "<span tal:replace='x'>dummy</span></p>", [
             ('setPosition', (1, 0)),
             ('beginScope',),
             ('loop', 'x', '$python:(1,2,3)$',
              [('rawtext', '<p tal:repeat="x python:(1,2,3)">'),
               ('setPosition', (1, 33)),
               ('insertText', '$x$',
                [('rawtext', '<span tal:replace="x">dummy</span>')]),
               ('rawtext', '</p>')]),
             ('endScope',),
             ])

    def check_attributes(self):
        self._run_check("<a href='foo' name='bar' tal:attributes="
                        "'href string:http://www.zope.org; x string:y'>"
                        "link</a>", [
            ('setPosition', (1, 0)),
            ('startTag', 'a',
             [('href', 'foo', 'replace', '$string:http://www.zope.org$'),
              ('name', 'bar'),
              ('tal:attributes',
               'href string:http://www.zope.org; x string:y'),
              ('x', '', 'replace', '$string:y$')]),
            ('rawtext', 'link</a>'),
            ])
        self._run_check("<p tal:replace='structure string:<img>' "
                        "tal:attributes='src string:foo.png'>duh</p>", [
            ('setPosition', (1, 0)),
            ('insertStructure', '$string:<img>$',
             {'src': '$string:foo.png$'},
             [('rawtext',
               '<p tal:replace="structure string:&lt;img&gt;" '
               'tal:attributes="src string:foo.png">duh</p>')]),
            ])

    def check_on_error(self):
        self._run_check("<p tal:on-error='string:error' "
                        "tal:content='notHere'>okay</p>", [
            ('setPosition', (1, 0)),
            ('onError',
             [('rawtext',
               '<p tal:on-error="string:error" tal:content="notHere">'),
              ('insertText', '$notHere$', [('rawtext', 'okay')]),
              ('rawtext', '</p>')],
             [('rawtext',
               '<p tal:on-error="string:error" tal:content="notHere">'),
              ('insertText', '$string:error$', []),
              ('rawtext', '</p>')]),
            ])
        self._run_check("<p tal:on-error='string:error' "
                        "tal:replace='notHere'>okay</p>", [
            ('setPosition', (1, 0)),
            ('onError',
             [('insertText', '$notHere$',
               [('rawtext',
                 '<p tal:on-error="string:error" '
                 'tal:replace="notHere">okay</p>')])],
             [('rawtext',
               '<p tal:on-error="string:error" tal:replace="notHere">'),
              ('insertText', '$string:error$', []),
              ('rawtext', '</p>')]),
            ])


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(HTMLTALParserTestCases, "check_"))
    suite.addTest(unittest.makeSuite(TALGeneratorTestCases, "check_"))
    return suite


if __name__ == "__main__":
    errs = utils.run_suite(test_suite())
    sys.exit(errs and 1 or 0)
