#! /usr/bin/env python
##############################################################################
#
# Copyright (c) 2001, 2002 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Tests for the HTMLTALParser code generator."""

import pprint
import sys

from TAL.tests import utils
import unittest


from TAL import HTMLTALParser
from TAL.TALDefs import TAL_VERSION, TALError, METALError


class TestCaseBase(unittest.TestCase):

    prologue = ""
    epilogue = ""
    initial_program = [('version', TAL_VERSION), ('mode', 'html')]
    final_program = []

    def _merge(self, p1, p2):
        if p1 and p2:
            op1, args1 = p1[-1]
            op2, args2 = p2[0]
            if op1.startswith('rawtext') and op2.startswith('rawtext'):
                return (p1[:-1]
                        + [rawtext(args1[0] + args2[0])]
                        + p2[1:])
        return p1+p2

    def _run_check(self, source, program, macros={}):
        parser = HTMLTALParser.HTMLTALParser()
        parser.parseString(self.prologue + source + self.epilogue)
        got_program, got_macros = parser.getCode()
        program = self._merge(self.initial_program, program)
        program = self._merge(program, self.final_program)
        self.assert_(got_program == program,
                     "Program:\n" + pprint.pformat(got_program)
                     + "\nExpected:\n" + pprint.pformat(program))
        self.assert_(got_macros == macros,
                     "Macros:\n" + pprint.pformat(got_macros)
                     + "\nExpected:\n" + pprint.pformat(macros))

    def _get_check(self, source, program=[], macros={}):
        parser = HTMLTALParser.HTMLTALParser()
        parser.parseString(source)
        got_program, got_macros = parser.getCode()
        pprint.pprint(got_program)
        pprint.pprint(got_macros)

    def _should_error(self, source, exc=TALError):
        def parse(self=self, source=source):
            parser = HTMLTALParser.HTMLTALParser()
            parser.parseString(self.prologue + source + self.epilogue)
        self.assertRaises(exc, parse)


def rawtext(s):
    """Compile raw text to the appropriate instruction."""
    if "\n" in s:
        return ("rawtextColumn", (s, len(s) - (s.rfind("\n") + 1)))
    else:
        return ("rawtextOffset", (s, len(s)))


class HTMLTALParserTestCases(TestCaseBase):

    def check_code_simple_identity(self):
        self._run_check("""<html a='b' b="c" c=d><title>My Title</html>""", [
            rawtext('<html a="b" b="c" c="d">'
                    '<title>My Title</title></html>'),
            ])

    def check_code_implied_list_closings(self):
        self._run_check("""<ul><li><p><p><li></ul>""", [
            rawtext('<ul><li><p></p><p></p></li><li></li></ul>'),
            ])
        self._run_check("""<dl><dt><dt><dd><dd><ol><li><li></ol></dl>""", [
            rawtext('<dl><dt></dt><dt></dt><dd></dd>'
                    '<dd><ol><li></li><li></li></ol></dd></dl>'),
            ])

    def check_code_implied_table_closings(self):
        self._run_check("""<p>text <table><tr><th>head\t<tr><td>cell\t"""
                        """<table><tr><td>cell \n \t \n<tr>""", [
            rawtext('<p>text</p> <table><tr><th>head</th>'
                    '</tr>\t<tr><td>cell\t<table><tr><td>cell</td>'
                    '</tr> \n \t \n<tr></tr></table></td></tr></table>'),
            ])
        self._run_check("""<table><tr><td>cell """
                        """<table><tr><td>cell </table></table>""", [
            rawtext('<table><tr><td>cell <table><tr><td>cell</td></tr>'
                    ' </table></td></tr></table>'),
            ])

    def check_code_bad_nesting(self):
        def check(self=self):
            self._run_check("<a><b></a></b>", [])
        self.assertRaises(HTMLTALParser.NestingError, check)

    def check_code_attr_syntax(self):
        output = [
            rawtext('<a b="v" c="v" d="v" e></a>'),
            ]
        self._run_check("""<a b='v' c="v" d=v e>""", output)
        self._run_check("""<a  b = 'v' c = "v" d = v e>""", output)
        self._run_check("""<a\nb\n=\n'v'\nc\n=\n"v"\nd\n=\nv\ne>""", output)
        self._run_check("""<a\tb\t=\t'v'\tc\t=\t"v"\td\t=\tv\te>""", output)

    def check_code_attr_values(self):
        self._run_check(
            """<a b='xxx\n\txxx' c="yyy\t\nyyy" d='\txyz\n'>""", [
            rawtext('<a b="xxx\n\txxx" c="yyy\t\nyyy" d="\txyz\n"></a>')])
        self._run_check("""<a b='' c="">""", [
            rawtext('<a b="" c=""></a>'),
            ])

    def check_code_attr_entity_replacement(self):
        # we expect entities *not* to be replaced by HTLMParser!
        self._run_check("""<a b='&amp;&gt;&lt;&quot;&apos;'>""", [
            rawtext('<a b="&amp;&gt;&lt;&quot;\'"></a>'),
            ])
        self._run_check("""<a b='\"'>""", [
            rawtext('<a b="&quot;"></a>'),
            ])
        self._run_check("""<a b='&'>""", [
            rawtext('<a b="&amp;"></a>'),
            ])
        self._run_check("""<a b='<'>""", [
            rawtext('<a b="&lt;"></a>'),
            ])

    def check_code_attr_funky_names(self):
        self._run_check("""<a a.b='v' c:d=v e-f=v>""", [
            rawtext('<a a.b="v" c:d="v" e-f="v"></a>'),
            ])

    def check_code_pcdata_entityref(self):
        self._run_check("""&nbsp;""", [
            rawtext('&nbsp;'),
            ])

    def check_code_short_endtags(self):
        self._run_check("""<html><img/></html>""", [
            rawtext('<html><img /></html>'),
            ])


class METALGeneratorTestCases(TestCaseBase):

    def check_null(self):
        self._run_check("", [])

    def check_define_macro(self):
        macro = self.initial_program + [
            ('startTag', ('p', [('metal:define-macro', 'M', 'metal')])),
            rawtext('booh</p>'),
            ]
        program = [
            ('setPosition', (1, 0)),
            ('defineMacro', ('M', macro)),
            ]
        macros = {'M': macro}
        self._run_check('<p metal:define-macro="M">booh</p>', program, macros)

    def check_use_macro(self):
        self._run_check('<p metal:use-macro="M">booh</p>', [
            ('setPosition', (1, 0)),
            ('useMacro',
             ('M', '$M$', {},
              [('startTag', ('p', [('metal:use-macro', 'M', 'metal')])),
               rawtext('booh</p>')])),
            ])

    def check_define_slot(self):
        macro = self.initial_program + [
            ('startTag', ('p', [('metal:define-macro', 'M', 'metal')])),
            rawtext('foo'),
            ('setPosition', (1, 29)),
            ('defineSlot', ('S',
             [('startTag', ('span', [('metal:define-slot', 'S', 'metal')])),
              rawtext('spam</span>')])),
            rawtext('bar</p>'),
            ]
        program = [('setPosition', (1, 0)),
                   ('defineMacro', ('M', macro))]
        macros = {'M': macro}
        self._run_check('<p metal:define-macro="M">foo'
                        '<span metal:define-slot="S">spam</span>bar</p>',
                        program, macros)

    def check_fill_slot(self):
        self._run_check('<p metal:use-macro="M">foo'
                        '<span metal:fill-slot="S">spam</span>bar</p>', [
            ('setPosition', (1, 0)),
            ('useMacro',
             ('M', '$M$',
              {'S': [('startTag', ('span',
                                   [('metal:fill-slot', 'S', 'metal')])),
                     rawtext('spam</span>')]},
             [('startTag', ('p', [('metal:use-macro', 'M', 'metal')])),
              rawtext('foo'),
              ('setPosition', (1, 26)),
              ('fillSlot', ('S',
               [('startTag', ('span', [('metal:fill-slot', 'S', 'metal')])),
                rawtext('spam</span>')])),
              rawtext('bar</p>')])),
            ])


class TALGeneratorTestCases(TestCaseBase):

    def check_null(self):
        self._run_check("", [])

    def check_define_1(self):
        self._run_check("<p tal:define='xyzzy string:spam'></p>", [
            ('setPosition', (1, 0)),
            ('beginScope', {'tal:define': 'xyzzy string:spam'}),
            ('setLocal', ('xyzzy', '$string:spam$')),
            ('startTag', ('p', [('tal:define', 'xyzzy string:spam', 'tal')])),
            ('endScope', ()),
            rawtext('</p>'),
            ])

    def check_define_2(self):
        self._run_check("<p tal:define='local xyzzy string:spam'></p>", [
            ('setPosition', (1, 0)),
            ('beginScope', {'tal:define': 'local xyzzy string:spam'}),
            ('setLocal', ('xyzzy', '$string:spam$')),
            ('startTag', ('p',
             [('tal:define', 'local xyzzy string:spam', 'tal')])),
            ('endScope', ()),
            rawtext('</p>'),
            ])

    def check_define_3(self):
        self._run_check("<p tal:define='global xyzzy string:spam'></p>", [
            ('setPosition', (1, 0)),
            ('beginScope', {'tal:define': 'global xyzzy string:spam'}),
            ('setGlobal', ('xyzzy', '$string:spam$')),
            ('startTag', ('p',
             [('tal:define', 'global xyzzy string:spam', 'tal')])),
            ('endScope', ()),
            rawtext('</p>'),
            ])

    def check_define_4(self):
        self._run_check("<p tal:define='x string:spam; y x'></p>", [
            ('setPosition', (1, 0)),
            ('beginScope', {'tal:define': 'x string:spam; y x'}),
            ('setLocal', ('x', '$string:spam$')),
            ('setLocal', ('y', '$x$')),
            ('startTag', ('p', [('tal:define', 'x string:spam; y x', 'tal')])),
            ('endScope', ()),
            rawtext('</p>'),
            ])

    def check_define_5(self):
        self._run_check("<p tal:define='x string:;;;;; y x'></p>", [
            ('setPosition', (1, 0)),
            ('beginScope', {'tal:define': 'x string:;;;;; y x'}),
            ('setLocal', ('x', '$string:;;$')),
            ('setLocal', ('y', '$x$')),
            ('startTag', ('p', [('tal:define', 'x string:;;;;; y x', 'tal')])),
            ('endScope', ()),
            rawtext('</p>'),
            ])

    def check_define_6(self):
        self._run_check(
            "<p tal:define='x string:spam; global y x; local z y'></p>", [
            ('setPosition', (1, 0)),
            ('beginScope',
             {'tal:define': 'x string:spam; global y x; local z y'}),
            ('setLocal', ('x', '$string:spam$')),
            ('setGlobal', ('y', '$x$')),
            ('setLocal', ('z', '$y$')),
            ('startTag', ('p',
             [('tal:define', 'x string:spam; global y x; local z y', 'tal')])),
            ('endScope', ()),
            rawtext('</p>'),
            ])

    def check_condition(self):
        self._run_check(
            "<p><span tal:condition='python:1'><b>foo</b></span></p>", [
            rawtext('<p>'),
            ('setPosition', (1, 3)),
            ('beginScope', {'tal:condition': 'python:1'}),
            ('condition', ('$python:1$',
             [('startTag', ('span', [('tal:condition', 'python:1', 'tal')])),
              rawtext('<b>foo</b></span>')])),
            ('endScope', ()),
            rawtext('</p>'),
            ])

    def check_content_1(self):
        self._run_check("<p tal:content='string:foo'>bar</p>", [
             ('setPosition', (1, 0)),
             ('beginScope', {'tal:content': 'string:foo'}),
             ('startTag', ('p', [('tal:content', 'string:foo', 'tal')])),
             ('insertText', ('$string:foo$', [rawtext('bar')])),
             ('endScope', ()),
             rawtext('</p>'),
             ])

    def check_content_2(self):
        self._run_check("<p tal:content='text string:foo'>bar</p>", [
             ('setPosition', (1, 0)),
             ('beginScope', {'tal:content': 'text string:foo'}),
             ('startTag', ('p', [('tal:content', 'text string:foo', 'tal')])),
             ('insertText', ('$string:foo$', [rawtext('bar')])),
             ('endScope', ()),
             rawtext('</p>'),
             ])

    def check_content_3(self):
        self._run_check("<p tal:content='structure string:<br>'>bar</p>", [
             ('setPosition', (1, 0)),
             ('beginScope', {'tal:content': 'structure string:<br>'}),
             ('startTag', ('p',
              [('tal:content', 'structure string:<br>', 'tal')])),
             ('insertStructure',
              ('$string:<br>$', {}, [rawtext('bar')])),
             ('endScope', ()),
             rawtext('</p>'),
             ])

    def check_replace_1(self):
        self._run_check("<p tal:replace='string:foo'>bar</p>", [
             ('setPosition', (1, 0)),
             ('beginScope', {'tal:replace': 'string:foo'}),
             ('insertText', ('$string:foo$',
              [('startTag', ('p', [('tal:replace', 'string:foo', 'tal')])),
               rawtext('bar</p>')])),
             ('endScope', ()),
             ])

    def check_replace_2(self):
        self._run_check("<p tal:replace='text string:foo'>bar</p>", [
             ('setPosition', (1, 0)),
             ('beginScope', {'tal:replace': 'text string:foo'}),
             ('insertText', ('$string:foo$',
              [('startTag', ('p',
                             [('tal:replace', 'text string:foo', 'tal')])),
               rawtext('bar</p>')])),
             ('endScope', ()),
             ])

    def check_replace_3(self):
        self._run_check("<p tal:replace='structure string:<br>'>bar</p>", [
             ('setPosition', (1, 0)),
             ('beginScope', {'tal:replace': 'structure string:<br>'}),
             ('insertStructure', ('$string:<br>$', {},
              [('startTag', ('p',
                [('tal:replace', 'structure string:<br>', 'tal')])),
               rawtext('bar</p>')])),
             ('endScope', ()),
             ])

    def check_repeat(self):
        self._run_check("<p tal:repeat='x python:(1,2,3)'>"
                        "<span tal:replace='x'>dummy</span></p>", [
             ('setPosition', (1, 0)),
             ('beginScope', {'tal:repeat': 'x python:(1,2,3)'}),
             ('loop', ('x', '$python:(1,2,3)$',
              [('startTag', ('p',
                             [('tal:repeat', 'x python:(1,2,3)', 'tal')])),
               ('setPosition', (1, 33)),
               ('beginScope', {'tal:replace': 'x'}),
               ('insertText', ('$x$',
                [('startTag', ('span', [('tal:replace', 'x', 'tal')])),
                 rawtext('dummy</span>')])),
               ('endScope', ()),
               rawtext('</p>')])),
             ('endScope', ()),
             ])

    def check_attributes_1(self):
        self._run_check("<a href='foo' name='bar' tal:attributes="
                        "'href string:http://www.zope.org; x string:y'>"
                        "link</a>", [
            ('setPosition', (1, 0)),
            ('beginScope',
             {'tal:attributes': 'href string:http://www.zope.org; x string:y',
              'name': 'bar', 'href': 'foo'}),
            ('startTag', ('a',
             [('href', 'foo', 'replace', '$string:http://www.zope.org$', 0, None),
              ('name', 'name="bar"'),
              ('tal:attributes',
               'href string:http://www.zope.org; x string:y', 'tal'),
              ('x', None, 'insert', '$string:y$', 0, None)])),
            ('endScope', ()),
            rawtext('link</a>'),
            ])

    def check_attributes_2(self):
        self._run_check("<p tal:replace='structure string:<img>' "
                        "tal:attributes='src string:foo.png'>duh</p>", [
            ('setPosition', (1, 0)),
            ('beginScope',
             {'tal:attributes': 'src string:foo.png',
              'tal:replace': 'structure string:<img>'}),
            ('insertStructure',
             ('$string:<img>$',
              {'src': ('$string:foo.png$', 0, None)},
              [('startTag', ('p',
                             [('tal:replace', 'structure string:<img>', 'tal'),
                              ('tal:attributes', 'src string:foo.png',
                               'tal')])),
               rawtext('duh</p>')])),
            ('endScope', ()),
            ])

    def check_on_error_1(self):
        self._run_check("<p tal:on-error='string:error' "
                        "tal:content='notHere'>okay</p>", [
            ('setPosition', (1, 0)),
            ('beginScope',
             {'tal:content': 'notHere', 'tal:on-error': 'string:error'}),
            ('onError',
             ([('startTag', ('p',
                [('tal:on-error', 'string:error', 'tal'),
                 ('tal:content', 'notHere', 'tal')])),
               ('insertText', ('$notHere$', [rawtext('okay')])),
               rawtext('</p>')],
              [('startTag', ('p',
                [('tal:on-error', 'string:error', 'tal'),
                 ('tal:content', 'notHere', 'tal')])),
               ('insertText', ('$string:error$', [])),
               rawtext('</p>')])),
            ('endScope', ()),
            ])

    def check_on_error_2(self):
        self._run_check("<p tal:on-error='string:error' "
                        "tal:replace='notHere'>okay</p>", [
            ('setPosition', (1, 0)),
            ('beginScope',
             {'tal:replace': 'notHere', 'tal:on-error': 'string:error'}),
            ('onError',
             ([('insertText', ('$notHere$',
                [('startTag', ('p',
                  [('tal:on-error', 'string:error', 'tal'),
                   ('tal:replace', 'notHere', 'tal')])),
                 rawtext('okay</p>')]))],
              [('startTag', ('p',
                [('tal:on-error', 'string:error', 'tal'),
                 ('tal:replace', 'notHere', 'tal')])),
               ('insertText', ('$string:error$', [])),
               rawtext('</p>')])),
            ('endScope', ()),
            ])

    def check_dup_attr(self):
        self._should_error("<img tal:condition='x' tal:condition='x'>")
        self._should_error("<img metal:define-macro='x' "
                           "metal:define-macro='x'>", METALError)

    def check_tal_errors(self):
        self._should_error("<p tal:define='x' />")
        self._should_error("<p tal:repeat='x' />")
        self._should_error("<p tal:foobar='x' />")
        self._should_error("<p tal:replace='x' tal:content='x' />")
        self._should_error("<p tal:replace='x'>")
        for tag in HTMLTALParser.EMPTY_HTML_TAGS:
            self._should_error("<%s tal:content='string:foo'>" % tag)

    def check_metal_errors(self):
        exc = METALError
        self._should_error(2*"<p metal:define-macro='x'>xxx</p>", exc)
        self._should_error("<html metal:use-macro='x'>" +
                           2*"<p metal:fill-slot='y' />" + "</html>", exc)
        self._should_error("<p metal:foobar='x' />", exc)
        self._should_error("<p metal:define-macro='x'>", exc)

    #
    #  I18N test cases
    #

    def check_i18n_attributes(self):
        self._run_check("<img alt='foo' i18n:attributes='alt'>", [
            ('setPosition', (1, 0)),
            ('beginScope', {'alt': 'foo', 'i18n:attributes': 'alt'}),
            ('startTag', ('img',
             [('alt', 'foo', 'replace', None, 1, None),
              ('i18n:attributes', 'alt', 'i18n')])),
            ('endScope', ()),
            ])
        self._run_check("<img alt='foo' i18n:attributes='alt foo ; bar'>", [
            ('setPosition', (1, 0)),
            ('beginScope', {'alt': 'foo', 'i18n:attributes': 'alt foo ; bar'}),
            ('startTag', ('img',
             [('alt', 'foo', 'replace', None, 1, 'foo'),
              ('i18n:attributes', 'alt foo ; bar', 'i18n'),
              ('bar', None, 'insert', None, 1, None)])),
            ('endScope', ()),
            ])
        self._should_error('''<input name="Delete"
            tal:attributes="name string:delete_button"
            i18n:attributes="name message-id">''')

    def test_i18n_name_bad_name(self):
        self._should_error("<span i18n:name='not a valid name' />")
        self._should_error("<span i18n:name='-bad-name' />")

    def test_i18n_attributes_repeated_attr(self):
        self._should_error("<a i18n:attributes='href; href' />")
        self._should_error("<a i18n:attributes='href; HREF' />")

    def check_i18n_translate(self):
        # input/test19.html
        self._run_check('''\
<span i18n:translate="">Replace this</span>
<span i18n:translate="msgid">This is a
translated string</span>
<span i18n:translate="">And another
translated string</span>
''', [
  ('setPosition', (1, 0)),
  ('beginScope', {'i18n:translate': ''}),
  ('startTag', ('span', [('i18n:translate', '', 'i18n')])),
  ('insertTranslation', ('', [('rawtextOffset', ('Replace this', 12))])),
  ('rawtextBeginScope',
   ('</span>\n', 0, (2, 0), 1, {'i18n:translate': 'msgid'})),
  ('startTag', ('span', [('i18n:translate', 'msgid', 'i18n')])),
  ('insertTranslation',
   ('msgid', [('rawtextColumn', ('This is a\ntranslated string', 17))])),
  ('rawtextBeginScope', ('</span>\n', 0, (4, 0), 1, {'i18n:translate': ''})),
  ('startTag', ('span', [('i18n:translate', '', 'i18n')])),
  ('insertTranslation',
   ('', [('rawtextColumn', ('And another\ntranslated string', 17))])),
  ('endScope', ()),
  ('rawtextColumn', ('</span>\n', 0))])

    def check_i18n_translate_with_nested_tal(self):
        self._run_check('''\
<span i18n:translate="">replaceable <p tal:replace="str:here">content</p></span>
''', [
  ('setPosition', (1, 0)),
  ('beginScope', {'i18n:translate': ''}),
  ('startTag', ('span', [('i18n:translate', '', 'i18n')])),
  ('insertTranslation',
   ('',
    [('rawtextOffset', ('replaceable ', 12)),
     ('setPosition', (1, 36)),
     ('beginScope', {'tal:replace': 'str:here'}),
     ('insertText',
      ('$str:here$',
       [('startTag', ('p', [('tal:replace', 'str:here', 'tal')])),
        ('rawtextOffset', ('content</p>', 11))])),
     ('endScope', ())])),
  ('endScope', ()),
  ('rawtextColumn', ('</span>\n', 0))
  ])

    def check_i18n_name(self):
        # input/test21.html
        self._run_check('''\
<span i18n:translate="">
  <span tal:replace="str:Lomax" i18n:name="name" /> was born in
  <span tal:replace="str:Antarctica" i18n:name="country" />.
</span>
''', [
  ('setPosition', (1, 0)),
  ('beginScope', {'i18n:translate': ''}),
  ('startTag', ('span', [('i18n:translate', '', 'i18n')])),
  ('insertTranslation',
   ('',
    [('rawtextBeginScope',
      ('\n  ',
       2,
       (2, 2),
       0,
       {'i18n:name': 'name', 'tal:replace': 'str:Lomax'})),
     ('i18nVariable',
      ('name',
       [('startEndTag',
         ('span',
          [('tal:replace', 'str:Lomax', 'tal'),
           ('i18n:name', 'name', 'i18n')]))],
       '$str:Lomax$',
       0)),
     ('rawtextBeginScope',
      (' was born in\n  ',
       2,
       (3, 2),
       1,
       {'i18n:name': 'country', 'tal:replace': 'str:Antarctica'})),
     ('i18nVariable',
      ('country',
       [('startEndTag',
         ('span',
          [('tal:replace', 'str:Antarctica', 'tal'),
           ('i18n:name', 'country', 'i18n')]))],
       '$str:Antarctica$',
       0)),
     ('endScope', ()),
     ('rawtextColumn', ('.\n', 0))])),
  ('endScope', ()),
  ('rawtextColumn', ('</span>\n', 0))
  ])

    def test_i18n_name_with_content(self):
        self._run_check('<div i18n:translate="">This is text for '
            '<span i18n:translate="" tal:content="bar" i18n:name="bar_name"/>.'
            '</div>', [
('setPosition', (1, 0)),
('beginScope', {'i18n:translate': ''}),
('startTag', ('div', [('i18n:translate', '', 'i18n')])),
('insertTranslation',
 ('',
  [('rawtextOffset', ('This is text for ', 17)),
   ('setPosition', (1, 40)),
   ('beginScope',
    {'tal:content': 'bar', 'i18n:name': 'bar_name', 'i18n:translate': ''}),
   ('i18nVariable',
       ('bar_name',
        [('startTag',
           ('span',
            [('i18n:translate', '', 'i18n'),
             ('tal:content', 'bar', 'tal'),
             ('i18n:name', 'bar_name', 'i18n')])),
         ('insertTranslation',
           ('',
             [('insertText', ('$bar$', []))])),
         ('rawtextOffset', ('</span>', 7))],
      None,
        0)),
   ('endScope', ()),
   ('rawtextOffset', ('.', 1))])),
('endScope', ()),
('rawtextOffset', ('</div>', 6)) 
  ])


    def check_i18n_name_implicit_value(self):
        # input/test22.html
        self._run_check('''\
<span i18n:translate="">
  <span i18n:name="name"><b>Jim</b></span> was born in
  <span i18n:name="country">the USA</span>.
</span>
''', [
  ('setPosition', (1, 0)),
  ('beginScope', {'i18n:translate': ''}),
  ('startTag', ('span', [('i18n:translate', '', 'i18n')])),
  ('insertTranslation',
   ('',
    [('rawtextBeginScope', ('\n  ', 2, (2, 2), 0, {'i18n:name': 'name'})),
     ('i18nVariable',
      ('name',
       [('rawtextOffset', ('<b>Jim</b>', 10))], None, 0)),
     ('rawtextBeginScope',
      (' was born in\n  ', 2, (3, 2), 1, {'i18n:name': 'country'})),
     ('i18nVariable',
      ('country',
       [('rawtextOffset', ('the USA', 7))], None, 0)),
     ('endScope', ()),
     ('rawtextColumn', ('.\n', 0))])),
  ('endScope', ()),
  ('rawtextColumn', ('</span>\n', 0))
  ])

    def check_i18n_context_domain(self):
        self._run_check("<span i18n:domain='mydomain'/>", [
            ('setPosition', (1, 0)),
            ('beginI18nContext', {'domain': 'mydomain',
                                  'source': None, 'target': None}),
            ('beginScope', {'i18n:domain': 'mydomain'}),
            ('startEndTag', ('span', [('i18n:domain', 'mydomain', 'i18n')])),
            ('endScope', ()),
            ('endI18nContext', ()),
            ])

    def check_i18n_context_source(self):
        self._run_check("<span i18n:source='en'/>", [
            ('setPosition', (1, 0)),
            ('beginI18nContext', {'source': 'en',
                                  'domain': 'default', 'target': None}),
            ('beginScope', {'i18n:source': 'en'}),
            ('startEndTag', ('span', [('i18n:source', 'en', 'i18n')])),
            ('endScope', ()),
            ('endI18nContext', ()),
            ])

    def check_i18n_context_source_target(self):
        self._run_check("<span i18n:source='en' i18n:target='ru'/>", [
            ('setPosition', (1, 0)),
            ('beginI18nContext', {'source': 'en', 'target': 'ru',
                                  'domain': 'default'}),
            ('beginScope', {'i18n:source': 'en', 'i18n:target': 'ru'}),
            ('startEndTag', ('span', [('i18n:source', 'en', 'i18n'),
                                      ('i18n:target', 'ru', 'i18n')])),
            ('endScope', ()),
            ('endI18nContext', ()),
            ])

    def check_i18n_context_in_define_slot(self):
        text = ("<div metal:use-macro='M' i18n:domain='mydomain'>"
                "<div metal:fill-slot='S'>spam</div>"
                "</div>")
        self._run_check(text, [
            ('setPosition', (1, 0)),
            ('useMacro',
             ('M', '$M$',
              {'S': [('startTag', ('div',
                                   [('metal:fill-slot', 'S', 'metal')])),
                     rawtext('spam</div>')]},
              [('beginI18nContext', {'domain': 'mydomain',
                                     'source': None, 'target': None}),
               ('beginScope',
                {'i18n:domain': 'mydomain', 'metal:use-macro': 'M'}),
               ('startTag', ('div', [('metal:use-macro', 'M', 'metal'),
                                     ('i18n:domain', 'mydomain', 'i18n')])),
               ('setPosition', (1, 48)),
               ('fillSlot', ('S',
                             [('startTag',
                               ('div', [('metal:fill-slot', 'S', 'metal')])),
                              rawtext('spam</div>')])),
               ('endScope', ()),
               rawtext('</div>'),
               ('endI18nContext', ())])),
            ])

    def check_i18n_data(self):
        # input/test23.html
        self._run_check('''\
<span i18n:data="here/currentTime"
      i18n:translate="timefmt">2:32 pm</span>
''', [
  ('setPosition', (1, 0)),
  ('beginScope',
   {'i18n:translate': 'timefmt', 'i18n:data': 'here/currentTime'}),
  ('startTag',
   ('span',
    [('i18n:data', 'here/currentTime', 'i18n'),
     ('i18n:translate', 'timefmt', 'i18n')])),
  ('insertTranslation',
   ('timefmt', [('rawtextOffset', ('2:32 pm', 7))], '$here/currentTime$')),
  ('endScope', ()),
  ('rawtextColumn', ('</span>\n', 0))
  ])

    def check_i18n_data_with_name(self):
        # input/test29.html
        self._run_check('''\
<div i18n:translate="">At the tone the time will be
<span i18n:data="here/currentTime"
      i18n:translate="timefmt"
      i18n:name="time">2:32 pm</span>... beep!</div>
''',
[('setPosition', (1, 0)),
 ('beginScope', {'i18n:translate': ''}),
 ('startTag', ('div', [('i18n:translate', '', 'i18n')])),
 ('insertTranslation',
  ('',
   [('rawtextBeginScope',
     ('At the tone the time will be\n',
      0,
      (2, 0),
      0,
      {'i18n:data': 'here/currentTime',
       'i18n:name': 'time',
       'i18n:translate': 'timefmt'})),
    ('insertTranslation',
     ('timefmt',
      [('startTag',
        ('span',
         [('i18n:data', 'here/currentTime', 'i18n'),
          ('i18n:translate', 'timefmt', 'i18n'),
          ('i18n:name', 'time', 'i18n')])),
       ('i18nVariable', ('time', [], None, 0))],
      '$here/currentTime$')),
    ('endScope', ()),
    ('rawtextOffset', ('... beep!', 9))])),
 ('endScope', ()),
 ('rawtextColumn', ('</div>\n', 0))]
)

    def check_i18n_explicit_msgid_with_name(self):
        # input/test26.html
        self._run_check('''\
<span i18n:translate="jobnum">
    Job #<span tal:replace="context/@@object_name"
               i18n:name="jobnum">NN</span></span>
''', [
  ('setPosition', (1, 0)),
  ('beginScope', {'i18n:translate': 'jobnum'}),
  ('startTag', ('span', [('i18n:translate', 'jobnum', 'i18n')])),
  ('insertTranslation',
   ('jobnum',
    [('rawtextBeginScope',
      ('\n    Job #',
       9,
       (2, 9),
       0,
       {'i18n:name': 'jobnum', 'tal:replace': 'context/@@object_name'})),
     ('i18nVariable',
      ('jobnum',
       [('startTag',
         ('span',
          [('tal:replace', 'context/@@object_name', 'tal'),
           ('i18n:name', 'jobnum', 'i18n')])),
        ('rawtextOffset', ('NN', 2)),
        ('rawtextOffset', ('</span>', 7))],
       '$context/@@object_name$',
       0)),
     ('endScope', ())])),
  ('endScope', ()),
  ('rawtextColumn', ('</span>\n', 0))
  ])

    def check_i18n_name_around_tal_content(self):
        # input/test28.html
        self._run_check('''\
<p i18n:translate="verify">Your contact email address is recorded as
    <span i18n:name="email">
    <a href="mailto:user@example.com"
       tal:content="request/submitter">user@host.com</a></span>
</p>
''', [
  ('setPosition', (1, 0)),
  ('beginScope', {'i18n:translate': 'verify'}),
  ('startTag', ('p', [('i18n:translate', 'verify', 'i18n')])),
  ('insertTranslation',
   ('verify',
    [('rawtextBeginScope',
      ('Your contact email address is recorded as\n    ',
       4,
       (2, 4),
       0,
       {'i18n:name': 'email'})),
     ('i18nVariable',
      ('email',
       [('rawtextBeginScope',
         ('\n    ',
          4,
          (3, 4),
          0,
          {'href': 'mailto:user@example.com',
           'tal:content': 'request/submitter'})),
        ('startTag',
         ('a',
          [('href', 'href="mailto:user@example.com"'),
           ('tal:content', 'request/submitter', 'tal')])),
        ('insertText',
         ('$request/submitter$',
          [('rawtextOffset', ('user@host.com', 13))])),
        ('endScope', ()),
        ('rawtextOffset', ('</a>', 4))],
       None,
       0)),
     ('endScope', ()),
     ('rawtextColumn', ('\n', 0))])),
  ('endScope', ()),
  ('rawtextColumn', ('</p>\n', 0))
  ])

    def check_i18n_name_with_tal_content(self):
        # input/test27.html
        self._run_check('''\
<p i18n:translate="verify">Your contact email address is recorded as
    <a href="mailto:user@example.com"
       tal:content="request/submitter"
       i18n:name="email">user@host.com</a>
</p>
''', [
  ('setPosition', (1, 0)),
  ('beginScope', {'i18n:translate': 'verify'}),
  ('startTag', ('p', [('i18n:translate', 'verify', 'i18n')])),
  ('insertTranslation',
   ('verify',
    [('rawtextBeginScope',
      ('Your contact email address is recorded as\n    ',
       4,
       (2, 4),
       0,
       {'href': 'mailto:user@example.com',
        'i18n:name': 'email',
        'tal:content': 'request/submitter'})),
     ('i18nVariable',
      ('email',
       [('startTag',
         ('a',
          [('href', 'href="mailto:user@example.com"'),
           ('tal:content', 'request/submitter', 'tal'),
           ('i18n:name', 'email', 'i18n')])),
        ('insertText',
         ('$request/submitter$',
          [('rawtextOffset', ('user@host.com', 13))])),
        ('rawtextOffset', ('</a>', 4))],
       None,
       0)),
     ('endScope', ()),
     ('rawtextColumn', ('\n', 0))])),
  ('endScope', ()),
  ('rawtextColumn', ('</p>\n', 0))
  ])


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(HTMLTALParserTestCases, "check_"))
    suite.addTest(unittest.makeSuite(METALGeneratorTestCases, "check_"))
    suite.addTest(unittest.makeSuite(TALGeneratorTestCases, "check_"))
    return suite


if __name__ == "__main__":
    errs = utils.run_suite(test_suite())
    sys.exit(errs and 1 or 0)
