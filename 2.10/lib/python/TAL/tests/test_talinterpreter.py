# -*- coding: ISO-8859-1 -*-
##############################################################################
#
# Copyright (c) 2001, 2002 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Tests for TALInterpreter.

$Id$
"""
import sys
import unittest

from StringIO import StringIO

# BBB 2005/05/01 -- to be changed after 12 months
# ignore deprecation warnings on import for now
import warnings
showwarning = warnings.showwarning
warnings.showwarning = lambda *a, **k: None
# this old import should remain here until the TAL package is
# completely removed, so that API backward compatibility is properly
# tested
from TAL.TALDefs import METALError, I18NError
from TAL.HTMLTALParser import HTMLTALParser
from TAL.TALParser import TALParser
from TAL.TALInterpreter import TALInterpreter
from TAL.DummyEngine import DummyEngine, DummyTranslationService
from TAL.TALInterpreter import interpolate
# restore warning machinery
warnings.showwarning = showwarning


from TAL.tests import utils
from zope.i18nmessageid import Message

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

    def test_mode_error(self):
        self.macro[1] = ("mode", "duh")

    def test_version_error(self):
        self.macro[0] = ("version", "duh")


class I18NCornerTestCase(TestCaseBase):

    def setUp(self):
        self.engine = DummyEngine()
        self.engine.setLocal('foo', Message('FoOvAlUe', 'default'))
        self.engine.setLocal('bar', 'BaRvAlUe')
        self.engine.setLocal('raw', ' \tRaW\n ')
        self.engine.setLocal('noxlt', Message("don't translate me"))

    def _check(self, program, expected):
        result = StringIO()
        self.interpreter = TALInterpreter(program, {}, self.engine,
                                          stream=result)
        self.interpreter()
        self.assertEqual(expected, result.getvalue())

    def test_simple_messageid_translate(self):
        # This test is mainly here to make sure our DummyEngine works
        # correctly.
        program, macros = self._compile('<span tal:content="foo"/>')
        self._check(program, '<span>FOOVALUE</span>\n')

        program, macros = self._compile('<span tal:replace="foo"/>')
        self._check(program, 'FOOVALUE\n')

    def test_replace_with_messageid_and_i18nname(self):
        program, macros = self._compile(
            '<div i18n:translate="" >'
            '<span tal:replace="foo" i18n:name="foo_name"/>'
            '</div>')
        self._check(program, '<div>FOOVALUE</div>\n')

    def test_pythonexpr_replace_with_messageid_and_i18nname(self):
        program, macros = self._compile(
            '<div i18n:translate="" >'
            '<span tal:replace="python: foo" i18n:name="foo_name"/>'
            '</div>')
        self._check(program, '<div>FOOVALUE</div>\n')

    def test_structure_replace_with_messageid_and_i18nname(self):
        program, macros = self._compile(
            '<div i18n:translate="" >'
            '<span tal:replace="structure foo" i18n:name="foo_name"'
            '      i18n:translate=""/>'
            '</div>')
        self._check(program, '<div>FOOVALUE</div>\n')

    def test_complex_replace_with_messageid_and_i18nname(self):
        program, macros = self._compile(
            '<div i18n:translate="" >'
            '<em i18n:name="foo_name" tal:omit-tag="">'
            '<span tal:replace="foo"/>'
            '</em>'
            '</div>')
        self._check(program, '<div>FOOVALUE</div>\n')

    def test_content_with_messageid_and_i18nname(self):
        program, macros = self._compile(
            '<div i18n:translate="" >'
            '<span tal:content="foo" i18n:name="foo_name"/>'
            '</div>')
        self._check(program, '<div><span>FOOVALUE</span></div>\n')

    def test_content_with_messageid_and_i18nname_and_i18ntranslate(self):
        # Let's tell the user this is incredibly silly!
        self.assertRaises(
            I18NError, self._compile,
            '<span i18n:translate="" tal:content="foo" i18n:name="foo_name"/>')

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
        program =  [('version', '1.6'),
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
        self.engine.translationDomain.clearMsgids()
        result = StringIO()
        program, macros = self._compile(
            '<div i18n:translate="">This is text for '
            '<span i18n:translate="" tal:content="bar" '
            'i18n:name="bar_name"/>.</div>')
        self.interpreter = TALInterpreter(program, {}, self.engine,
                                          stream=result)
        self.interpreter()
        msgids = self.engine.translationDomain.getMsgids('default')
        msgids.sort()
        self.assertEqual(2, len(msgids))
        self.assertEqual('BaRvAlUe', msgids[0][0])
        self.assertEqual('This is text for ${bar_name}.', msgids[1][0])
        self.assertEqual({'bar_name': '<span>BARVALUE</span>'}, msgids[1][1])
        self.assertEqual(
            '<div>THIS IS TEXT FOR <span>BARVALUE</span>.</div>\n',
            result.getvalue())

    def test_for_raw_msgids(self):
        # Test for Issue 314: i18n:translate removes line breaks from
        # <pre>...</pre> contents
        # HTML mode
        self.engine.translationDomain.clearMsgids()
        result = StringIO()
        program, macros = self._compile(
            '<div i18n:translate=""> This is text\n'
            ' \tfor\n div. </div>'
            '<pre i18n:translate=""> This is text\n'
            ' <b>\tfor</b>\n pre. </pre>')
        self.interpreter = TALInterpreter(program, {}, self.engine,
                                          stream=result)
        self.interpreter()
        msgids = self.engine.translationDomain.getMsgids('default')
        msgids.sort()
        self.assertEqual(2, len(msgids))
        self.assertEqual(' This is text\n <b>\tfor</b>\n pre. ', msgids[0][0])
        self.assertEqual('This is text for div.', msgids[1][0])
        self.assertEqual(
            '<div>THIS IS TEXT FOR DIV.</div>'
            '<pre> THIS IS TEXT\n <B>\tFOR</B>\n PRE. </pre>\n',
            result.getvalue())

        # XML mode
        self.engine.translationDomain.clearMsgids()
        result = StringIO()
        parser = TALParser()
        parser.parseString(
            '<?xml version="1.0"?>\n'
            '<pre xmlns:i18n="http://xml.zope.org/namespaces/i18n"'
            ' i18n:translate=""> This is text\n'
            ' <b>\tfor</b>\n barvalue. </pre>')
        program, macros = parser.getCode()
        self.interpreter = TALInterpreter(program, {}, self.engine,
                                          stream=result)
        self.interpreter()
        msgids = self.engine.translationDomain.getMsgids('default')
        msgids.sort()
        self.assertEqual(1, len(msgids))
        self.assertEqual('This is text <b> for</b> barvalue.', msgids[0][0])
        self.assertEqual(
            '<?xml version="1.0"?>\n'
            '<pre>THIS IS TEXT <B> FOR</B> BARVALUE.</pre>\n',
            result.getvalue())

    def test_raw_msgids_and_i18ntranslate_i18nname(self):
        self.engine.translationDomain.clearMsgids()
        result = StringIO()
        program, macros = self._compile(
            '<div i18n:translate=""> This is text\n \tfor\n'
            '<pre tal:content="raw" i18n:name="raw"'
            ' i18n:translate=""></pre>.</div>')
        self.interpreter = TALInterpreter(program, {}, self.engine,
                                          stream=result)
        self.interpreter()
        msgids = self.engine.translationDomain.getMsgids('default')
        msgids.sort()
        self.assertEqual(2, len(msgids))
        self.assertEqual(' \tRaW\n ', msgids[0][0])
        self.assertEqual('This is text for ${raw}.', msgids[1][0])
        self.assertEqual({'raw': '<pre> \tRAW\n </pre>'}, msgids[1][1])
        self.assertEqual(
            u'<div>THIS IS TEXT FOR <pre> \tRAW\n </pre>.</div>\n',
            result.getvalue())

    def test_for_handling_unicode_vars(self):
        # Make sure that non-ASCII Unicode is substituted correctly.
        # http://collector.zope.org/Zope3-dev/264
        program, macros = self._compile(
            "<div i18n:translate='' tal:define='bar python:unichr(0xC0)'>"
            "Foo <span tal:replace='bar' i18n:name='bar' /></div>")
        self._check(program, u"<div>FOO \u00C0</div>\n")

    def test_for_untranslated_messageid_simple(self):
        program, macros = self._compile('<span tal:content="noxlt"/>')
        self._check(program, "<span>don't translate me</span>\n")
        
    def test_for_untranslated_messageid_i18nname(self):
        program, macros = self._compile(
            '<div i18n:translate="" >'
            '<span tal:replace="python: noxlt" i18n:name="foo_name"/>'
            '</div>')
        self._check(program, "<div>don't translate me</div>\n")


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

    def test_attribute_wrapping(self):
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

    def test_unicode_content(self):
        INPUT = """<p tal:content="python:u'déjà-vu'">para</p>"""
        EXPECTED = u"""<p>déjà-vu</p>""" "\n"
        self.compare(INPUT, EXPECTED)

    def test_unicode_structure(self):
        INPUT = """<p tal:replace="structure python:u'déjà-vu'">para</p>"""
        EXPECTED = u"""déjà-vu""" "\n"
        self.compare(INPUT, EXPECTED)

    def test_i18n_replace_number(self):
        INPUT = """
        <p i18n:translate="foo ${bar}">
        <span tal:replace="python:123" i18n:name="bar">para</span>
        </p>"""
        EXPECTED = u"""
        <p>FOO 123</p>""" "\n"
        self.compare(INPUT, EXPECTED)

    def test_entities(self):
        INPUT = ('<img tal:define="foo nothing" '
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

    def test_syntax_ok(self):
        text = "foo ${bar_0MAN} $baz_zz bee"
        mapping = {'bar_0MAN': 'fish', 'baz_zz': 'moo'}
        expected = "foo fish moo bee"
        self.assertEqual(interpolate(text, mapping), expected)

    def test_syntax_bad(self):
        text = "foo $_bar_man} $ ${baz bee"
        mapping = {'_bar_man': 'fish', 'baz': 'moo'}
        expected = text
        self.assertEqual(interpolate(text, mapping), expected)

    def test_missing(self):
        text = "foo ${bar} ${baz}"
        mapping = {'bar': 'fish'}
        expected = "foo fish ${baz}"
        self.assertEqual(interpolate(text, mapping), expected)

    def test_redundant(self):
        text = "foo ${bar}"
        mapping = {'bar': 'fish', 'baz': 'moo'}
        expected = "foo fish"
        self.assertEqual(interpolate(text, mapping), expected)

    def test_numeric(self):
        text = "foo ${bar}"
        mapping = {'bar': 123}
        expected = "foo 123"
        self.assertEqual(interpolate(text, mapping), expected)

    def test_unicode(self):
        text = u"foo ${bar}"
        mapping = {u'bar': u'baz'}
        expected = u"foo baz"
        self.assertEqual(interpolate(text, mapping), expected)

    # this test just tests sick behaviour, we'll disable it
    #def test_unicode_mixed_unknown_encoding(self):
    #    # This test assumes that sys.getdefaultencoding is ascii...
    #    text = u"foo ${bar}"
    #    mapping = {u'bar': 'd\xe9j\xe0'}
    #    expected = u"foo d\\xe9j\\xe0"
    #    self.assertEqual(interpolate(text, mapping), expected)

def test_suite():
    suite = unittest.makeSuite(I18NErrorsTestCase)
    suite.addTest(unittest.makeSuite(MacroErrorsTestCase))
    suite.addTest(unittest.makeSuite(OutputPresentationTestCase))
    suite.addTest(unittest.makeSuite(I18NCornerTestCase))
    suite.addTest(unittest.makeSuite(InterpolateTestCase))

    return suite

if __name__ == "__main__":
    errs = utils.run_suite(test_suite())
    sys.exit(errs and 1 or 0)
