# -*- coding: ISO-8859-1 -*-
##############################################################################
#
# Copyright (c) 2001 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
"""Tests for TALInterpreter."""

import sys

from TAL.tests import utils
import unittest

from StringIO import StringIO

from TAL.TALDefs import METALError, I18NError
from TAL.HTMLTALParser import HTMLTALParser
from TAL.TALInterpreter import TALInterpreter
from TAL.DummyEngine import DummyEngine, DummyTranslationService
from TAL.TALInterpreter import interpolate


class TestCaseBase(unittest.TestCase):

    def _compile(self, source):
        parser = HTMLTALParser()
        parser.parseString(source)
        program, macros = parser.getCode()
        return program, macros


class MacroErrorsTestCase(TestCaseBase):

    def setUp(self):
        dummy, macros = self._compile('<p metal:define-macro="M">Booh</p>')
        self.macro = macros['M']
        self.engine = DummyEngine(macros)
        program, dummy = self._compile('<p metal:use-macro="M">Bah</p>')
        self.interpreter = TALInterpreter(program, {}, self.engine)

    def tearDown(self):
        try:
            self.interpreter()
        except METALError:
            pass
        else:
            self.fail("Expected METALError")

    def check_mode_error(self):
        self.macro[1] = ("mode", "duh")

    def check_version_error(self):
        self.macro[0] = ("version", "duh")


class I18NCornerTestCase(TestCaseBase):

    def setUp(self):
        self.engine = DummyEngine()
        self.engine.setLocal('bar', 'BaRvAlUe')

    def _check(self, program, expected):
        result = StringIO()
        self.interpreter = TALInterpreter(program, {}, self.engine,
                                          stream=result)
        self.interpreter()
        self.assertEqual(expected, result.getvalue())

    def test_content_with_messageid_and_i18nname_and_i18ntranslate(self):
        # Let's tell the user this is incredibly silly!
        self.assertRaises(
            I18NError, self._compile,
            '<span i18n:translate="" tal:content="bar" i18n:name="bar_name"/>')

    def test_content_with_plaintext_and_i18nname_and_i18ntranslate(self):
        # Let's tell the user this is incredibly silly!
        self.assertRaises(
            I18NError, self._compile,
            '<span i18n:translate="" i18n:name="color_name">green</span>')

    def test_translate_static_text_as_dynamic(self):
        program, macros = self._compile(
            '<div i18n:translate="">This is text for '
            '<span i18n:translate="" tal:content="bar" i18n:name="bar_name"/>.'
            '</div>')
        self._check(program,
                    '<div>THIS IS TEXT FOR <span>BARVALUE</span>.</div>\n')

    def test_translate_static_text_as_dynamic_from_bytecode(self):
        program =  [('version', '1.5'),
 ('mode', 'html'),
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
]
        self._check(program,
                    '<div>THIS IS TEXT FOR <span>BARVALUE</span>.</div>\n')

    def test_for_correct_msgids(self):

        class CollectingTranslationService(DummyTranslationService):
            data = []

            def translate(self, domain, msgid, mapping=None,
                          context=None, target_language=None, default=None):
                self.data.append(msgid)
                return DummyTranslationService.translate(
                    self,
                    domain, msgid, mapping, context, target_language, default)

        xlatsvc = CollectingTranslationService()
        self.engine.translationService = xlatsvc
        result = StringIO()
        program, macros = self._compile(
            '<div i18n:translate="">This is text for '
            '<span i18n:translate="" tal:content="bar" '
            'i18n:name="bar_name"/>.</div>')
        self.interpreter = TALInterpreter(program, {}, self.engine,
                                          stream=result)
        self.interpreter()
        self.assert_('BaRvAlUe' in xlatsvc.data)
        self.assert_('This is text for ${bar_name}.' in
                     xlatsvc.data)
        self.assertEqual(
            '<div>THIS IS TEXT FOR <span>BARVALUE</span>.</div>\n',
            result.getvalue())


class I18NErrorsTestCase(TestCaseBase):

    def _check(self, src, msg):
        try:
            self._compile(src)
        except I18NError:
            pass
        else:
            self.fail(msg)

    def test_id_with_replace(self):
        self._check('<p i18n:id="foo" tal:replace="string:splat"></p>',
                    "expected i18n:id with tal:replace to be denied")

    def test_missing_values(self):
        self._check('<p i18n:attributes=""></p>',
                    "missing i18n:attributes value not caught")
        self._check('<p i18n:data=""></p>',
                    "missing i18n:data value not caught")
        self._check('<p i18n:id=""></p>',
                    "missing i18n:id value not caught")

    def test_id_with_attributes(self):
        self._check('''<input name="Delete"
                       tal:attributes="name string:delete_button"
                       i18n:attributes="name message-id">''',
            "expected attribute being both part of tal:attributes" +
            " and having a msgid in i18n:attributes to be denied")

class OutputPresentationTestCase(TestCaseBase):

    def check_attribute_wrapping(self):
        # To make sure the attribute-wrapping code is invoked, we have to
        # include at least one TAL/METAL attribute to avoid having the start
        # tag optimized into a rawtext instruction.
        INPUT = r"""
        <html this='element' has='a' lot='of' attributes=', so' the='output'
              needs='to' be='line' wrapped='.' tal:define='foo nothing'>
        </html>"""
        EXPECTED = r'''
        <html this="element" has="a" lot="of"
              attributes=", so" the="output" needs="to"
              be="line" wrapped=".">
        </html>''' "\n"
        self.compare(INPUT, EXPECTED)

    def check_unicode_content(self):
        INPUT = """<p tal:content="python:u'déjà-vu'">para</p>"""
        EXPECTED = u"""<p>déjà-vu</p>""" "\n"
        self.compare(INPUT, EXPECTED)

    def check_unicode_structure(self):
        INPUT = """<p tal:replace="structure python:u'déjà-vu'">para</p>"""
        EXPECTED = u"""déjà-vu""" "\n"
        self.compare(INPUT, EXPECTED)

    def check_i18n_replace_number(self):
        INPUT = """
        <p i18n:translate="foo ${bar}">
        <span tal:replace="python:123" i18n:name="bar">para</span>
        </p>"""
        EXPECTED = u"""
        <p>FOO 123</p>""" "\n"
        self.compare(INPUT, EXPECTED)

    def check_entities(self):
        INPUT = ('<img tal:attributes="alt default" '
                 'alt="&a; &#1; &#x0a; &a &#45 &; &#0a; <>" />')
        EXPECTED = ('<img alt="&a; &#1; &#x0a; '
                    '&amp;a &amp;#45 &amp;; &amp;#0a; &lt;&gt;" />\n')
        self.compare(INPUT, EXPECTED)
        
    def compare(self, INPUT, EXPECTED):
        program, macros = self._compile(INPUT)
        sio = StringIO()
        interp = TALInterpreter(program, {}, DummyEngine(), sio, wrap=60)
        interp()
        self.assertEqual(sio.getvalue(), EXPECTED)

class InterpolateTestCase(TestCaseBase):
    def check_syntax_ok(self):
        text = "foo ${bar_0MAN} $baz_zz bee"
        mapping = {'bar_0MAN': 'fish', 'baz_zz': 'moo'}
        expected = "foo fish moo bee"
        self.assertEqual(interpolate(text, mapping), expected)

    def check_syntax_bad(self):
        text = "foo $_bar_man} $ ${baz bee"
        mapping = {'_bar_man': 'fish', 'baz': 'moo'}
        expected = text
        self.assertEqual(interpolate(text, mapping), expected)

    def check_missing(self):
        text = "foo ${bar} ${baz}"
        mapping = {'bar': 'fish'}
        expected = "foo fish ${baz}"
        self.assertEqual(interpolate(text, mapping), expected)

    def check_redundant(self):
        text = "foo ${bar}"
        mapping = {'bar': 'fish', 'baz': 'moo'}
        expected = "foo fish"
        self.assertEqual(interpolate(text, mapping), expected)

    def check_numeric(self):
        text = "foo ${bar}"
        mapping = {'bar': 123}
        expected = "foo 123"
        self.assertEqual(interpolate(text, mapping), expected)

    def check_unicode(self):
        text = u"foo ${bar}"
        mapping = {u'bar': u'baz'}
        expected = u"foo baz"
        self.assertEqual(interpolate(text, mapping), expected)

    def check_unicode_mixed_unknown_encoding(self):
        # This test assumes that sys.getdefaultencoding is ascii...
        text = u"foo ${bar}"
        mapping = {u'bar': 'd\xe9j\xe0'}
        expected = u"foo d\\xe9j\\xe0"
        self.assertEqual(interpolate(text, mapping), expected)

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(MacroErrorsTestCase, "check_"))
    suite.addTest(unittest.makeSuite(OutputPresentationTestCase, "check_"))
    suite.addTest(unittest.makeSuite(InterpolateTestCase, "check_"))
    suite.addTest(unittest.makeSuite(I18NCornerTestCase))
    return suite


if __name__ == "__main__":
    errs = utils.run_suite(test_suite())
    sys.exit(errs and 1 or 0)
