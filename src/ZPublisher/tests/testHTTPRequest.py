##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################

import sys
import unittest
import warnings
from contextlib import contextmanager
from io import BytesIO
from unittest.mock import patch
from urllib.parse import quote_plus

from AccessControl.tainted import TaintedString
from AccessControl.tainted import should_be_tainted
from zExceptions import NotFound
from zope.component import getGlobalSiteManager
from zope.component import provideAdapter
from zope.i18n.interfaces import IUserPreferredLanguages
from zope.i18n.interfaces.locales import ILocale
from zope.publisher.browser import BrowserLanguages
from zope.publisher.interfaces.http import IHTTPRequest
from zope.testing.cleanup import cleanUp
from ZPublisher.HTTPRequest import BadRequest
from ZPublisher.HTTPRequest import FileUpload
from ZPublisher.HTTPRequest import search_type
from ZPublisher.interfaces import IXmlrpcChecker
from ZPublisher.tests.testBaseRequest import TestRequestViewsBase
from ZPublisher.utils import basic_auth_encode
from ZPublisher.xmlrpc import is_xmlrpc_response


class RecordTests(unittest.TestCase):

    def _makeOne(self):
        from ZPublisher.HTTPRequest import record
        return record()

    def test_dict_methods(self):
        rec = self._makeOne()
        rec.a = 1
        self.assertEqual(rec['a'], 1)
        self.assertEqual(rec.get('a'), 1)
        self.assertEqual(list(rec.keys()), ['a'])
        self.assertEqual(list(rec.values()), [1])
        self.assertEqual(list(rec.items()), [('a', 1)])

    def test_dict_special_methods(self):
        rec = self._makeOne()
        rec.a = 1
        self.assertTrue('a' in rec)
        self.assertFalse('b' in rec)
        self.assertEqual(len(rec), 1)
        self.assertEqual(list(iter(rec)), ['a'])

    def test_copy(self):
        rec = self._makeOne()
        rec.a = 1
        rec.b = 'foo'
        new_rec = rec.copy()
        self.assertIsInstance(new_rec, dict)
        self.assertEqual(new_rec, {'a': 1, 'b': 'foo'})

    def test_eq(self):
        rec1 = self._makeOne()
        self.assertFalse(rec1, {})
        rec2 = self._makeOne()
        self.assertEqual(rec1, rec2)
        rec1.a = 1
        self.assertNotEqual(rec1, rec2)
        rec2.a = 1
        self.assertEqual(rec1, rec2)
        rec2.b = 'foo'
        self.assertNotEqual(rec1, rec2)

    def test__str__returns_native_string(self):
        rec = self._makeOne()
        rec.a = b'foo'
        rec.b = 8
        rec.c = 'bar'
        self.assertIsInstance(str(rec), str)

    def test_str(self):
        rec = self._makeOne()
        rec.a = 1
        self.assertEqual(str(rec), 'a: 1')

    def test_repr(self):
        rec = self._makeOne()
        rec.a = 1
        rec.b = 'foo'
        r = repr(rec)
        d = eval(r)
        self.assertEqual(d, rec.__dict__)


class HTTPRequestFactoryMixin:

    def tearDown(self):
        cleanUp()

    def _getTargetClass(self):
        from ZPublisher.HTTPRequest import HTTPRequest
        return HTTPRequest

    def _makePostEnviron(self, body=b'', multipart=True):
        environ = TEST_POST_ENVIRON.copy()
        environ["CONTENT_TYPE"] = \
            multipart and 'multipart/form-data; boundary=12345' \
            or 'application/x-www-form-urlencoded'
        environ['CONTENT_LENGTH'] = str(len(body))
        return environ

    def _makeOne(self, stdin=None, environ=None, response=None, clean=1):
        from ZPublisher.HTTPResponse import HTTPResponse
        if stdin is None:
            stdin = BytesIO()

        if environ is None:
            environ = {}

        if 'REQUEST_METHOD' not in environ:
            environ['REQUEST_METHOD'] = 'GET'

        if 'SERVER_NAME' not in environ:
            environ['SERVER_NAME'] = 'localhost'

        if 'SERVER_PORT' not in environ:
            environ['SERVER_PORT'] = '8080'

        if response is None:
            response = HTTPResponse(stdout=BytesIO())

        return self._getTargetClass()(stdin, environ, response, clean)


class HTTPRequestTests(unittest.TestCase, HTTPRequestFactoryMixin):

    def _processInputs(self, inputs):
        # Have the inputs processed, and return a HTTPRequest object
        # holding the result.
        # inputs is expected to be a list of (key, value) tuples, no CGI
        # encoding is required.

        query_string = []
        add = query_string.append
        for key, val in inputs:
            add(f"{quote_plus(key)}={quote_plus(val)}")
        query_string = '&'.join(query_string)

        env = {'SERVER_NAME': 'testingharnas', 'SERVER_PORT': '80'}
        env['QUERY_STRING'] = query_string
        req = self._makeOne(environ=env)
        req.processInputs()
        self._noFormValuesInOther(req)
        return req

    def _noTaintedValues(self, req):
        self.assertFalse(list(req.taintedform.keys()))

    def _valueIsOrHoldsTainted(self, val):
        # Recursively searches a structure for a TaintedString and returns 1
        # when one is found.
        # Also raises an Assertion if a string which *should* have been
        # tainted is found, or when a tainted string is not deemed dangerous.
        from AccessControl.tainted import TaintedString
        from ZPublisher.HTTPRequest import record

        retval = 0

        if isinstance(val, TaintedString):
            self.assertTrue(
                should_be_tainted(val._value),
                "%r is not dangerous, no taint required." % val)
            retval = 1

        elif isinstance(val, record):
            for attr, value in list(val.__dict__.items()):
                rval = self._valueIsOrHoldsTainted(attr)
                if rval:
                    retval = 1
                rval = self._valueIsOrHoldsTainted(value)
                if rval:
                    retval = 1

        elif type(val) in (list, tuple):
            for entry in val:
                rval = self._valueIsOrHoldsTainted(entry)
                if rval:
                    retval = 1

        elif isinstance(val, str):
            self.assertFalse(
                should_be_tainted(val),
                "'%s' is dangerous and should have been tainted." % val)

        return retval

    def _noFormValuesInOther(self, req):
        for key in list(req.taintedform.keys()):
            self.assertFalse(
                key in req.other,
                'REQUEST.other should not hold tainted values at first!')

        for key in list(req.form.keys()):
            self.assertFalse(
                key in req.other,
                'REQUEST.other should not hold form values at first!')

    def _onlyTaintedformHoldsTaintedStrings(self, req):
        for key, val in list(req.taintedform.items()):
            self.assertTrue(
                self._valueIsOrHoldsTainted(key)
                or self._valueIsOrHoldsTainted(val),
                'Tainted form holds item %s that is not tainted' % key)

        for key, val in list(req.form.items()):
            if key in req.taintedform:
                continue
            self.assertFalse(
                self._valueIsOrHoldsTainted(key)
                or self._valueIsOrHoldsTainted(val),
                'Normal form holds item %s that is tainted' % key)

    def _taintedKeysAlsoInForm(self, req):
        for key in list(req.taintedform.keys()):
            self.assertTrue(
                key in req.form,
                "Found tainted %s not in form" % key)
            self.assertEqual(
                req.form[key], req.taintedform[key],
                "Key %s not correctly reproduced in tainted; expected %r, "
                "got %r" % (key, req.form[key], req.taintedform[key]))

    def test_webdav_source_port_available(self):
        req = self._makeOne()
        self.assertFalse(req.get('WEBDAV_SOURCE_PORT'))

        req = self._makeOne(environ={'WEBDAV_SOURCE_PORT': 1})
        self.assertTrue(req.get('WEBDAV_SOURCE_PORT'))

    def test_no_docstring_on_instance(self):
        env = {'SERVER_NAME': 'testingharnas', 'SERVER_PORT': '80'}
        req = self._makeOne(environ=env)
        self.assertTrue(req.__doc__ is None)

    def test___bobo_traverse___raises(self):
        env = {'SERVER_NAME': 'testingharnas', 'SERVER_PORT': '80'}
        req = self._makeOne(environ=env)
        self.assertRaises(KeyError, req.__bobo_traverse__, 'REQUEST')
        self.assertRaises(KeyError, req.__bobo_traverse__, 'BODY')
        self.assertRaises(KeyError, req.__bobo_traverse__, 'BODYFILE')
        self.assertRaises(KeyError, req.__bobo_traverse__, 'RESPONSE')

    def test_processInputs_wo_query_string(self):
        env = {'SERVER_NAME': 'testingharnas', 'SERVER_PORT': '80'}
        req = self._makeOne(environ=env)
        req.processInputs()
        self._noFormValuesInOther(req)
        self.assertEqual(req.form, {})

    def test_processInputs_wo_marshalling(self):
        inputs = (
            ('foo', 'bar'), ('spam', 'eggs'),
            ('number', '1'),
            ('spacey key', 'val'), ('key', 'spacey val'),
            ('multi', '1'), ('multi', '2'))
        req = self._processInputs(inputs)

        formkeys = list(req.form.keys())
        formkeys.sort()
        self.assertEqual(
            formkeys,
            ['foo', 'key', 'multi', 'number', 'spacey key', 'spam'])
        self.assertEqual(req['number'], '1')
        self.assertEqual(req['multi'], ['1', '2'])
        self.assertEqual(req['spacey key'], 'val')
        self.assertEqual(req['key'], 'spacey val')

        self._noTaintedValues(req)
        self._onlyTaintedformHoldsTaintedStrings(req)

    def test_processInputs_w_simple_marshalling(self):
        from DateTime.DateTime import DateTime
        inputs = (
            ('num:int', '42'), ('fract:float', '4.2'), ('bign:long', '45'),
            ('words:string', 'Some words'), ('2tokens:tokens', 'one two'),
            ('aday:date', '2002/07/23'),
            ('accountedfor:required', 'yes'),
            ('multiline:lines', 'one\ntwo'),
            ('morewords:text', 'one\ntwo\n'))
        req = self._processInputs(inputs)

        formkeys = list(req.form.keys())
        formkeys.sort()
        self.assertEqual(
            formkeys,
            ['2tokens', 'accountedfor', 'aday', 'bign',
             'fract', 'morewords', 'multiline', 'num', 'words'])

        self.assertEqual(req['2tokens'], ['one', 'two'])
        self.assertEqual(req['accountedfor'], 'yes')
        self.assertEqual(req['aday'], DateTime('2002/07/23'))
        self.assertEqual(req['bign'], 45)
        self.assertEqual(req['fract'], 4.2)
        self.assertEqual(req['morewords'], 'one\ntwo\n')
        self.assertEqual(req['multiline'], ['one', 'two'])
        self.assertEqual(req['num'], 42)
        self.assertEqual(req['words'], 'Some words')

        self._noTaintedValues(req)
        self._onlyTaintedformHoldsTaintedStrings(req)

    def test_processInputs_w_unicode_conversions(self):
        # This tests native strings.
        reg_char = '\xae'
        inputs = (('ustring:ustring:utf8', 'test' + reg_char),
                  ('utext:utext:utf8',
                   'test' + reg_char + '\ntest' + reg_char + '\n'),
                  ('utokens:utokens:utf8',
                   'test' + reg_char + ' test' + reg_char),
                  ('ulines:ulines:utf8',
                   'test' + reg_char + '\ntest' + reg_char),
                  ('nouconverter:string:utf8', 'test' + reg_char))
        # unicode converters will go away with Zope 6
        # ignore deprecation warning for test run
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            req = self._processInputs(inputs)

        formkeys = list(req.form.keys())
        formkeys.sort()
        self.assertEqual(
            formkeys,
            ['nouconverter', 'ulines', 'ustring', 'utext', 'utokens'])

        self.assertEqual(req['ustring'], 'test\u00AE')
        self.assertEqual(req['utext'], 'test\u00AE\ntest\u00AE\n')
        self.assertEqual(req['utokens'], ['test\u00AE', 'test\u00AE'])
        self.assertEqual(req['ulines'], ['test\u00AE', 'test\u00AE'])

        # expect a utf-8 encoded version
        self.assertEqual(req['nouconverter'], 'test' + reg_char)

        self._noTaintedValues(req)
        self._onlyTaintedformHoldsTaintedStrings(req)

    def test_processInputs_w_simple_containers(self):
        inputs = (
            ('oneitem:list', 'one'),
            ('alist:list', 'one'), ('alist:list', 'two'),
            ('oneitemtuple:tuple', 'one'),
            ('atuple:tuple', 'one'), ('atuple:tuple', 'two'),
            ('onerec.foo:record', 'foo'), ('onerec.bar:record', 'bar'),
            ('setrec.foo:records', 'foo'), ('setrec.bar:records', 'bar'),
            ('setrec.foo:records', 'spam'), ('setrec.bar:records', 'eggs'))
        req = self._processInputs(inputs)

        formkeys = list(req.form.keys())
        formkeys.sort()
        self.assertEqual(
            formkeys,
            ['alist', 'atuple', 'oneitem', 'oneitemtuple', 'onerec', 'setrec'])

        self.assertEqual(req['oneitem'], ['one'])
        self.assertEqual(req['oneitemtuple'], ('one',))
        self.assertEqual(req['alist'], ['one', 'two'])
        self.assertEqual(req['atuple'], ('one', 'two'))
        self.assertEqual(req['onerec'].foo, 'foo')
        self.assertEqual(req['onerec'].bar, 'bar')
        self.assertEqual(len(req['setrec']), 2)
        self.assertEqual(req['setrec'][0].foo, 'foo')
        self.assertEqual(req['setrec'][0].bar, 'bar')
        self.assertEqual(req['setrec'][1].foo, 'spam')
        self.assertEqual(req['setrec'][1].bar, 'eggs')

        self._noTaintedValues(req)
        self._onlyTaintedformHoldsTaintedStrings(req)

    def test_processInputs_w_marshalling_into_sequences(self):
        inputs = (
            ('ilist:int:list', '1'), ('ilist:int:list', '2'),
            ('ilist:list:int', '3'),
            ('ftuple:float:tuple', '1.0'), ('ftuple:float:tuple', '1.1'),
            ('ftuple:tuple:float', '1.2'),
            ('tlist:tokens:list', 'one two'), ('tlist:list:tokens', '3 4'))
        req = self._processInputs(inputs)

        formkeys = list(req.form.keys())
        formkeys.sort()
        self.assertEqual(formkeys, ['ftuple', 'ilist', 'tlist'])

        self.assertEqual(req['ilist'], [1, 2, 3])
        self.assertEqual(req['ftuple'], (1.0, 1.1, 1.2))
        self.assertEqual(req['tlist'], [['one', 'two'], ['3', '4']])

        self._noTaintedValues(req)
        self._onlyTaintedformHoldsTaintedStrings(req)

    def test_processInputs_w_records_w_sequences(self):
        inputs = (
            ('onerec.name:record', 'foo'),
            ('onerec.tokens:tokens:record', 'one two'),
            ('onerec.ints:int:record', '1'),
            ('onerec.ints:int:record', '2'),

            ('setrec.name:records', 'first'),
            ('setrec.ilist:list:int:records', '1'),
            ('setrec.ilist:list:int:records', '2'),
            ('setrec.ituple:tuple:int:records', '1'),
            ('setrec.ituple:tuple:int:records', '2'),
            ('setrec.name:records', 'second'),
            ('setrec.ilist:list:int:records', '1'),
            ('setrec.ilist:list:int:records', '2'),
            ('setrec.ituple:tuple:int:records', '1'),
            ('setrec.ituple:tuple:int:records', '2'))
        req = self._processInputs(inputs)

        formkeys = list(req.form.keys())
        formkeys.sort()
        self.assertEqual(formkeys, ['onerec', 'setrec'])

        self.assertEqual(req['onerec'].name, 'foo')
        self.assertEqual(req['onerec'].tokens, ['one', 'two'])
        # Implicit sequences and records don't mix.
        self.assertEqual(req['onerec'].ints, 2)

        self.assertEqual(len(req['setrec']), 2)
        self.assertEqual(req['setrec'][0].name, 'first')
        self.assertEqual(req['setrec'][1].name, 'second')

        for i in range(2):
            self.assertEqual(req['setrec'][i].ilist, [1, 2])
            self.assertEqual(req['setrec'][i].ituple, (1, 2))

        self._noTaintedValues(req)
        self._onlyTaintedformHoldsTaintedStrings(req)

    def test_processInputs_w_defaults(self):
        inputs = (
            ('foo:default:int', '5'),

            ('alist:int:default', '3'),
            ('alist:int:default', '4'),
            ('alist:int:default', '5'),
            ('alist:int', '1'),
            ('alist:int', '2'),

            ('explicitlist:int:list:default', '3'),
            ('explicitlist:int:list:default', '4'),
            ('explicitlist:int:list:default', '5'),
            ('explicitlist:int:list', '1'),
            ('explicitlist:int:list', '2'),

            ('bar.spam:record:default', 'eggs'),
            ('bar.foo:record:default', 'foo'),
            ('bar.foo:record', 'baz'),

            ('setrec.spam:records:default', 'eggs'),
            ('setrec.foo:records:default', 'foo'),
            ('setrec.foo:records', 'baz'),
            ('setrec.foo:records', 'ham'),
        )
        req = self._processInputs(inputs)

        formkeys = list(req.form.keys())
        formkeys.sort()
        self.assertEqual(
            formkeys, ['alist', 'bar', 'explicitlist', 'foo', 'setrec'])

        self.assertEqual(req['alist'], [1, 2, 3, 4, 5])
        self.assertEqual(req['explicitlist'], [1, 2, 3, 4, 5])

        self.assertEqual(req['foo'], 5)
        self.assertEqual(req['bar'].spam, 'eggs')
        self.assertEqual(req['bar'].foo, 'baz')

        self.assertEqual(len(req['setrec']), 2)
        self.assertEqual(req['setrec'][0].spam, 'eggs')
        self.assertEqual(req['setrec'][0].foo, 'baz')
        self.assertEqual(req['setrec'][1].spam, 'eggs')
        self.assertEqual(req['setrec'][1].foo, 'ham')

        self._noTaintedValues(req)
        self._onlyTaintedformHoldsTaintedStrings(req)

    def test_processInputs_wo_marshalling_w_Taints(self):
        inputs = (
            ('foo', 'bar'), ('spam', 'eggs'),
            ('number', '1'),
            ('tainted', '<tainted value>'),
            ('<tainted key>', 'value'),
            ('spacey key', 'val'), ('key', 'spacey val'),
            ('tinitmulti', '<1>'), ('tinitmulti', '2'),
            ('tdefermulti', '1'), ('tdefermulti', '<2>'),
            ('tallmulti', '<1>'), ('tallmulti', '<2>'))
        req = self._processInputs(inputs)

        taintedformkeys = list(req.taintedform.keys())
        taintedformkeys.sort()
        self.assertEqual(
            taintedformkeys,
            ['<tainted key>', 'tainted',
             'tallmulti', 'tdefermulti', 'tinitmulti'])

        self._taintedKeysAlsoInForm(req)
        self._onlyTaintedformHoldsTaintedStrings(req)

    def test_processInputs_w_simple_marshalling_w_taints(self):
        inputs = (
            ('<tnum>:int', '42'), ('<tfract>:float', '4.2'),
            ('<tbign>:long', '45'),
            ('twords:string', 'Some <words>'),
            ('t2tokens:tokens', 'one <two>'),
            ('<taday>:date', '2002/07/23'),
            ('taccountedfor:required', '<yes>'),
            ('tmultiline:lines', '<one\ntwo>'),
            ('tmorewords:text', '<one\ntwo>\n'))
        req = self._processInputs(inputs)

        taintedformkeys = list(req.taintedform.keys())
        taintedformkeys.sort()
        self.assertEqual(
            taintedformkeys,
            ['<taday>', '<tbign>', '<tfract>',
             '<tnum>', 't2tokens', 'taccountedfor', 'tmorewords', 'tmultiline',
             'twords'])

        self._taintedKeysAlsoInForm(req)
        self._onlyTaintedformHoldsTaintedStrings(req)

    def test_processInputs_w_unicode_w_taints(self):
        inputs = (
            ('tustring:ustring:utf8', '<test\xc2\xae>'),
            ('tutext:utext:utf8', '<test\xc2\xae>\n<test\xc2\xae\n>'),

            ('tinitutokens:utokens:utf8', '<test\xc2\xae> test\xc2\xae'),
            ('tinitulines:ulines:utf8', '<test\xc2\xae>\ntest\xc2\xae'),

            ('tdeferutokens:utokens:utf8', 'test\xc2\xae <test\xc2\xae>'),
            ('tdeferulines:ulines:utf8', 'test\xc2\xae\n<test\xc2\xae>'),

            ('tnouconverter:string:utf8', '<test\xc2\xae>'),
        )

        # unicode converters will go away with Zope 6
        # ignore deprecation warning for test run
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            req = self._processInputs(inputs)

        taintedformkeys = list(req.taintedform.keys())
        taintedformkeys.sort()
        self.assertEqual(
            taintedformkeys,
            ['tdeferulines', 'tdeferutokens',
             'tinitulines', 'tinitutokens', 'tnouconverter', 'tustring',
             'tutext'])

        self._taintedKeysAlsoInForm(req)
        self._onlyTaintedformHoldsTaintedStrings(req)

    def test_processInputs_w_simple_containers_w_taints(self):
        inputs = (
            ('toneitem:list', '<one>'),
            ('<tkeyoneitem>:list', 'one'),
            ('tinitalist:list', '<one>'), ('tinitalist:list', 'two'),
            ('tdeferalist:list', 'one'), ('tdeferalist:list', '<two>'),

            ('toneitemtuple:tuple', '<one>'),
            ('tinitatuple:tuple', '<one>'), ('tinitatuple:tuple', 'two'),
            ('tdeferatuple:tuple', 'one'), ('tdeferatuple:tuple', '<two>'),

            ('tinitonerec.foo:record', '<foo>'),
            ('tinitonerec.bar:record', 'bar'),
            ('tdeferonerec.foo:record', 'foo'),
            ('tdeferonerec.bar:record', '<bar>'),

            ('tinitinitsetrec.foo:records', '<foo>'),
            ('tinitinitsetrec.bar:records', 'bar'),
            ('tinitinitsetrec.foo:records', 'spam'),
            ('tinitinitsetrec.bar:records', 'eggs'),

            ('tinitdefersetrec.foo:records', 'foo'),
            ('tinitdefersetrec.bar:records', '<bar>'),
            ('tinitdefersetrec.foo:records', 'spam'),
            ('tinitdefersetrec.bar:records', 'eggs'),

            ('tdeferinitsetrec.foo:records', 'foo'),
            ('tdeferinitsetrec.bar:records', 'bar'),
            ('tdeferinitsetrec.foo:records', '<spam>'),
            ('tdeferinitsetrec.bar:records', 'eggs'),

            ('tdeferdefersetrec.foo:records', 'foo'),
            ('tdeferdefersetrec.bar:records', 'bar'),
            ('tdeferdefersetrec.foo:records', 'spam'),
            ('tdeferdefersetrec.bar:records', '<eggs>'))
        req = self._processInputs(inputs)

        taintedformkeys = list(req.taintedform.keys())
        taintedformkeys.sort()
        self.assertEqual(
            taintedformkeys,
            ['<tkeyoneitem>', 'tdeferalist',
             'tdeferatuple', 'tdeferdefersetrec', 'tdeferinitsetrec',
             'tdeferonerec', 'tinitalist', 'tinitatuple', 'tinitdefersetrec',
             'tinitinitsetrec', 'tinitonerec', 'toneitem', 'toneitemtuple'])

        self._taintedKeysAlsoInForm(req)
        self._onlyTaintedformHoldsTaintedStrings(req)

    def test_processInputs_w_records_w_sequences_tainted(self):
        inputs = (
            ('tinitonerec.tokens:tokens:record', '<one> two'),
            ('tdeferonerec.tokens:tokens:record', 'one <two>'),

            ('tinitsetrec.name:records', 'first'),
            ('tinitsetrec.ilist:list:records', '<1>'),
            ('tinitsetrec.ilist:list:records', '2'),
            ('tinitsetrec.ituple:tuple:int:records', '1'),
            ('tinitsetrec.ituple:tuple:int:records', '2'),
            ('tinitsetrec.name:records', 'second'),
            ('tinitsetrec.ilist:list:records', '1'),
            ('tinitsetrec.ilist:list:records', '2'),
            ('tinitsetrec.ituple:tuple:int:records', '1'),
            ('tinitsetrec.ituple:tuple:int:records', '2'),

            ('tdeferfirstsetrec.name:records', 'first'),
            ('tdeferfirstsetrec.ilist:list:records', '1'),
            ('tdeferfirstsetrec.ilist:list:records', '<2>'),
            ('tdeferfirstsetrec.ituple:tuple:int:records', '1'),
            ('tdeferfirstsetrec.ituple:tuple:int:records', '2'),
            ('tdeferfirstsetrec.name:records', 'second'),
            ('tdeferfirstsetrec.ilist:list:records', '1'),
            ('tdeferfirstsetrec.ilist:list:records', '2'),
            ('tdeferfirstsetrec.ituple:tuple:int:records', '1'),
            ('tdeferfirstsetrec.ituple:tuple:int:records', '2'),

            ('tdefersecondsetrec.name:records', 'first'),
            ('tdefersecondsetrec.ilist:list:records', '1'),
            ('tdefersecondsetrec.ilist:list:records', '2'),
            ('tdefersecondsetrec.ituple:tuple:int:records', '1'),
            ('tdefersecondsetrec.ituple:tuple:int:records', '2'),
            ('tdefersecondsetrec.name:records', 'second'),
            ('tdefersecondsetrec.ilist:list:records', '1'),
            ('tdefersecondsetrec.ilist:list:records', '<2>'),
            ('tdefersecondsetrec.ituple:tuple:int:records', '1'),
            ('tdefersecondsetrec.ituple:tuple:int:records', '2'),
        )
        req = self._processInputs(inputs)

        taintedformkeys = list(req.taintedform.keys())
        taintedformkeys.sort()
        self.assertEqual(
            taintedformkeys,
            ['tdeferfirstsetrec', 'tdeferonerec',
             'tdefersecondsetrec', 'tinitonerec', 'tinitsetrec'])

        self._taintedKeysAlsoInForm(req)
        self._onlyTaintedformHoldsTaintedStrings(req)

    def test_processInputs_w_defaults_w_taints(self):
        inputs = (
            ('tfoo:default', '<5>'),

            ('doesnnotapply:default', '<4>'),
            ('doesnnotapply', '4'),

            ('tinitlist:default', '3'),
            ('tinitlist:default', '4'),
            ('tinitlist:default', '5'),
            ('tinitlist', '<1>'),
            ('tinitlist', '2'),

            ('tdeferlist:default', '3'),
            ('tdeferlist:default', '<4>'),
            ('tdeferlist:default', '5'),
            ('tdeferlist', '1'),
            ('tdeferlist', '2'),

            ('tinitbar.spam:record:default', 'eggs'),
            ('tinitbar.foo:record:default', 'foo'),
            ('tinitbar.foo:record', '<baz>'),
            ('tdeferbar.spam:record:default', '<eggs>'),
            ('tdeferbar.foo:record:default', 'foo'),
            ('tdeferbar.foo:record', 'baz'),

            ('rdoesnotapply.spam:record:default', '<eggs>'),
            ('rdoesnotapply.spam:record', 'eggs'),

            ('tinitsetrec.spam:records:default', 'eggs'),
            ('tinitsetrec.foo:records:default', 'foo'),
            ('tinitsetrec.foo:records', '<baz>'),
            ('tinitsetrec.foo:records', 'ham'),

            ('tdefersetrec.spam:records:default', '<eggs>'),
            ('tdefersetrec.foo:records:default', 'foo'),
            ('tdefersetrec.foo:records', 'baz'),
            ('tdefersetrec.foo:records', 'ham'),

            ('srdoesnotapply.foo:records:default', '<eggs>'),
            ('srdoesnotapply.foo:records', 'baz'),
            ('srdoesnotapply.foo:records', 'ham'))
        req = self._processInputs(inputs)

        taintedformkeys = list(req.taintedform.keys())
        taintedformkeys.sort()
        self.assertEqual(
            taintedformkeys,
            ['tdeferbar', 'tdeferlist',
             'tdefersetrec', 'tfoo', 'tinitbar', 'tinitlist', 'tinitsetrec'])

        self._taintedKeysAlsoInForm(req)
        self._onlyTaintedformHoldsTaintedStrings(req)

    def test_processInputs_w_tainted_attribute_raises(self):
        input = ('taintedattr.here<be<taint:record', 'value',)

        self.assertRaises(ValueError, self._processInputs, input)

    def test_processInputs_w_tainted_values_cleans_exceptions(self):
        # Feed tainted garbage to the conversion methods, and any exception
        # returned should be HTML safe
        from DateTime.interfaces import SyntaxError
        from ZPublisher.Converters import type_converters
        for type, convert in list(type_converters.items()):
            try:
                # unicode converters will go away with Zope 6
                # ignore deprecation warning for test run
                with warnings.catch_warnings():
                    warnings.simplefilter('ignore')
                    convert('<html garbage>')
            except Exception as e:
                self.assertFalse(
                    '<' in e.args,
                    '%s converter does not quote unsafe value!' % type)
            except SyntaxError as e:
                self.assertFalse(
                    '<' in e,
                    '%s converter does not quote unsafe value!' % type)

    def test_processInputs_w_dotted_name_as_tuple(self):
        # Collector #500
        inputs = (
            ('name.:tuple', 'name with dot as tuple'),)
        req = self._processInputs(inputs)

        formkeys = list(req.form.keys())
        formkeys.sort()
        self.assertEqual(formkeys, ['name.'])

        self.assertEqual(req['name.'], ('name with dot as tuple',))

        self._noTaintedValues(req)
        self._onlyTaintedformHoldsTaintedStrings(req)

    def test_processInputs_w_cookie_parsing(self):
        env = {'SERVER_NAME': 'testingharnas', 'SERVER_PORT': '80'}

        env['HTTP_COOKIE'] = 'foo=bar; baz=gee'
        req = self._makeOne(environ=env)
        self.assertEqual(req.cookies['foo'], 'bar')
        self.assertEqual(req.cookies['baz'], 'gee')

        env['HTTP_COOKIE'] = 'foo=bar; baz="gee, like, e=mc^2"'
        req = self._makeOne(environ=env)
        self.assertEqual(req.cookies['foo'], 'bar')
        self.assertEqual(req.cookies['baz'], 'gee, like, e=mc^2')

        # Collector #1498: empty cookies
        env['HTTP_COOKIE'] = 'foo=bar; hmm; baz=gee'
        req = self._makeOne(environ=env)
        self.assertEqual(req.cookies['foo'], 'bar')
        self.assertEqual(req.cookies['hmm'], '')
        self.assertEqual(req.cookies['baz'], 'gee')

        # Unquoted multi-space cookies
        env['HTTP_COOKIE'] = 'single=cookie data; ' \
                             'quoted="cookie data with unquoted spaces"; ' \
                             'multi=cookie data with unquoted spaces; ' \
                             'multi2=cookie data with unquoted spaces'
        req = self._makeOne(environ=env)
        self.assertEqual(req.cookies['single'], 'cookie data')
        self.assertEqual(req.cookies['quoted'],
                         'cookie data with unquoted spaces')
        self.assertEqual(req.cookies['multi'],
                         'cookie data with unquoted spaces')
        self.assertEqual(req.cookies['multi2'],
                         'cookie data with unquoted spaces')

    def test_processInputs_xmlrpc(self):
        TEST_METHOD_CALL = (
            b'<?xml version="1.0"?>'
            b'<methodCall><methodName>test</methodName></methodCall>'
        )
        environ = self._makePostEnviron(body=TEST_METHOD_CALL)
        environ['CONTENT_TYPE'] = 'text/xml'
        req = self._makeOne(stdin=BytesIO(TEST_METHOD_CALL), environ=environ)
        req.processInputs()
        self.assertEqual(req.PATH_INFO, '/test')
        self.assertEqual(req.args, ())

    def test_processInputs_xmlrpc_query_string(self):
        TEST_METHOD_CALL = (
            b'<?xml version="1.0"?>'
            b'<methodCall><methodName>test</methodName></methodCall>'
        )
        environ = self._makePostEnviron(body=TEST_METHOD_CALL)
        environ['CONTENT_TYPE'] = 'text/xml'
        environ['QUERY_STRING'] = 'x=1'
        req = self._makeOne(stdin=BytesIO(TEST_METHOD_CALL), environ=environ)
        req.processInputs()
        self.assertEqual(req.PATH_INFO, '/test')
        self.assertEqual(req.args, ())
        self.assertEqual(req.form["x"], '1')

    def test_processInputs_xmlrpc_method(self):
        TEST_METHOD_CALL = (
            b'<?xml version="1.0"?>'
            b'<methodCall><methodName>test</methodName></methodCall>'
        )
        environ = self._makePostEnviron(body=TEST_METHOD_CALL)
        environ['CONTENT_TYPE'] = 'text/xml'
        environ['QUERY_STRING'] = ':method=method'
        req = self._makeOne(stdin=BytesIO(TEST_METHOD_CALL), environ=environ)
        with self.assertRaises(BadRequest):
            req.processInputs()

    def test_processInputs_SOAP(self):
        # ZPublisher does not really have SOAP support
        # all it does is put the body into ``SOAPXML``
        body = b'soap'
        environ = TEST_POST_ENVIRON.copy()
        environ['HTTP_SOAPACTION'] = "soapaction"
        req = self._makeOne(stdin=BytesIO(body), environ=environ)
        req.processInputs()
        self.assertEqual(req.SOAPXML, body)

    def test_processInputs_SOAP_query_string(self):
        # ZPublisher does not really have SOAP support
        # all it does is put the body into ``SOAPXML``
        body = b'soap'
        environ = TEST_POST_ENVIRON.copy()
        environ['QUERY_STRING'] = 'x=1'
        environ['HTTP_SOAPACTION'] = "soapaction"
        req = self._makeOne(stdin=BytesIO(body), environ=environ)
        req.processInputs()
        self.assertEqual(req.SOAPXML, body)
        self.assertEqual(req.form["x"], '1')

    def test_processInputs_w_urlencoded_and_qs(self):
        body = b'foo=1'
        environ = {
            'CONTENT_TYPE': 'application/x-www-form-urlencoded',
            'CONTENT_LENGTH': len(body),
            'QUERY_STRING': 'bar=2',
            'REQUEST_METHOD': 'POST',
        }
        req = self._makeOne(stdin=BytesIO(body), environ=environ)
        req.processInputs()
        self.assertEqual(req.form['foo'], '1')
        self.assertEqual(req.form['bar'], '2')

    def test_close_removes_stdin_references(self):
        # Verifies that all references to the input stream go away on
        # request.close().  Otherwise a tempfile may stick around.
        s = BytesIO(TEST_FILE_DATA)
        start_count = sys.getrefcount(s)

        environ = self._makePostEnviron(body=TEST_FILE_DATA)
        req = self._makeOne(stdin=s, environ=environ)
        req.processInputs()
        self.assertNotEqual(start_count, sys.getrefcount(s))  # Precondition
        req.close()
        self.assertEqual(start_count, sys.getrefcount(s))  # The test

    def test_processInputs_w_large_input_gets_tempfile(self):
        # checks fileupload object supports the filename
        s = BytesIO(TEST_LARGEFILE_DATA)

        environ = self._makePostEnviron(body=TEST_LARGEFILE_DATA)
        req = self._makeOne(stdin=s, environ=environ)
        req.processInputs()
        f = req.form.get('largefile')
        self.assertTrue(f.name)
        self.assertEqual(4006, len(f.file.read()))
        f.file.close()

    def test_processInputs_with_file_upload_gets_iterator(self):
        # checks fileupload object supports the iterator protocol
        # collector entry 1837
        s = BytesIO(TEST_FILE_DATA)

        environ = self._makePostEnviron(body=TEST_FILE_DATA)
        req = self._makeOne(stdin=s, environ=environ)
        req.processInputs()
        f = req.form.get('smallfile')
        self.assertEqual(list(f), [b'test\n'])
        f.seek(0)
        self.assertEqual(next(f), b'test\n')

    def test_processInputs_BODY(self):
        s = BytesIO(b"body")
        environ = TEST_POST_ENVIRON.copy()
        environ["CONTENT_TYPE"] = "text/plain"
        req = self._makeOne(stdin=s, environ=environ)
        req.processInputs()
        self.assertEqual(req["BODY"], b"body")
        self.assertIs(req["BODYFILE"], s)

    def test_processInputs_BODY_unseekable(self):
        s = _Unseekable(BytesIO(b"body"))
        environ = TEST_POST_ENVIRON.copy()
        environ["CONTENT_TYPE"] = "text/plain"
        req = self._makeOne(stdin=s, environ=environ)
        req.processInputs()
        self.assertEqual(req["BODY"], b"body")
        self.assertIs(req["BODYFILE"], s)

    def test_processInputs_seekable_form_data(self):
        s = BytesIO(TEST_FILE_DATA)
        environ = self._makePostEnviron(body=TEST_FILE_DATA)
        req = self._makeOne(stdin=s, environ=environ)
        req.processInputs()
        f = req.form.get('smallfile')
        self.assertEqual(list(f), [b'test\n'])
        self.assertEqual(req["BODY"], TEST_FILE_DATA)
        self.assertEqual(req["BODYFILE"].read(), TEST_FILE_DATA)

    def test_processInputs_unseekable_form_data(self):
        s = _Unseekable(BytesIO(TEST_FILE_DATA))
        environ = self._makePostEnviron(body=TEST_FILE_DATA)
        req = self._makeOne(stdin=s, environ=environ)
        req.processInputs()
        f = req.form.get('smallfile')
        self.assertEqual(list(f), [b'test\n'])
        # we cannot access ``BODY`` in this case
        # as the underlying file has been read
        with self.assertRaises(KeyError):
            req["BODY"]

    def test_processInputs_unspecified_file(self):
        s = BytesIO(TEST_FILE_DATA_UNSPECIFIED)
        environ = self._makePostEnviron(body=TEST_FILE_DATA_UNSPECIFIED)
        req = self._makeOne(stdin=s, environ=environ)
        req.processInputs()
        f = req.form.get('smallfile')
        self.assertEqual(f.filename, "")
        self.assertEqual(list(f), [])

    def test__authUserPW_simple(self):
        user_id = 'user'
        password = 'password'
        auth_header = basic_auth_encode(user_id, password)

        environ = {'HTTP_AUTHORIZATION': auth_header}
        request = self._makeOne(environ=environ)

        user_id_x, password_x = request._authUserPW()

        self.assertEqual(user_id_x, user_id)
        self.assertEqual(password_x, password)

    def test__authUserPW_with_embedded_colon(self):
        user_id = 'user'
        password = 'embedded:colon'
        auth_header = basic_auth_encode(user_id, password)

        environ = {'HTTP_AUTHORIZATION': auth_header}
        request = self._makeOne(environ=environ)

        user_id_x, password_x = request._authUserPW()

        self.assertEqual(user_id_x, user_id)
        self.assertEqual(password_x, password)

    def test__authUserPW_non_ascii(self):
        user_id = 'usèr'
        password = 'pàssword'
        auth_header = basic_auth_encode(user_id, password)

        environ = {'HTTP_AUTHORIZATION': auth_header}
        request = self._makeOne(environ=environ)

        user_id_x, password_x = request._authUserPW()

        self.assertEqual(user_id_x, user_id)
        self.assertEqual(password_x, password)

    def test_debug_not_in_qs_still_gets_attr(self):
        from zope.publisher.base import DebugFlags

        # when accessing request.debug we will see the DebugFlags instance
        request = self._makeOne()
        self.assertIsInstance(request.debug, DebugFlags)
        # It won't be available through dictonary lookup, though
        self.assertTrue(request.get('debug') is None)

    def test_debug_in_qs_gets_form_var(self):
        env = {'QUERY_STRING': 'debug=1'}

        # request.debug will actually yield a 'debug' form variable
        # if it exists
        request = self._makeOne(environ=env)
        request.processInputs()
        self.assertEqual(request.debug, '1')
        self.assertEqual(request.get('debug'), '1')
        self.assertEqual(request['debug'], '1')

        # we can still override request.debug with a form variable or directly

    def test_debug_override_via_form_other(self):
        request = self._makeOne()
        request.processInputs()
        request.form['debug'] = '1'
        self.assertEqual(request.debug, '1')
        request['debug'] = '2'
        self.assertEqual(request.debug, '2')

    def test_locale_property_accessor(self):
        from ZPublisher.HTTPRequest import _marker

        provideAdapter(BrowserLanguages, [IHTTPRequest],
                       IUserPreferredLanguages)

        env = {'HTTP_ACCEPT_LANGUAGE': 'en'}
        request = self._makeOne(environ=env)

        # before accessing request.locale for the first time, request._locale
        # is still a marker
        self.assertTrue(request._locale is _marker)

        # when accessing request.locale we will see an ILocale
        self.assertTrue(ILocale.providedBy(request.locale))

        # and request._locale has been set
        self.assertTrue(request._locale is request.locale)

        # It won't be available through dictonary lookup, though
        self.assertTrue(request.get('locale') is None)

    def test_locale_in_qs(self):
        provideAdapter(BrowserLanguages, [IHTTPRequest],
                       IUserPreferredLanguages)

        # request.locale will actually yield a 'locale' form variable
        # if it exists
        env = {'HTTP_ACCEPT_LANGUAGE': 'en', 'QUERY_STRING': 'locale=1'}
        request = self._makeOne(environ=env)
        request.processInputs()

        self.assertEqual(request.locale, '1')
        self.assertEqual(request.get('locale'), '1')
        self.assertEqual(request['locale'], '1')

    def test_locale_property_override_via_form_other(self):
        provideAdapter(BrowserLanguages, [IHTTPRequest],
                       IUserPreferredLanguages)
        env = {'HTTP_ACCEPT_LANGUAGE': 'en'}

        # we can still override request.locale with a form variable
        request = self._makeOne(environ=env)
        request.processInputs()

        self.assertTrue(ILocale.providedBy(request.locale))

        request.form['locale'] = '1'
        self.assertEqual(request.locale, '1')

        request['locale'] = '2'
        self.assertEqual(request.locale, '2')

    def test_locale_semantics(self):
        provideAdapter(BrowserLanguages, [IHTTPRequest],
                       IUserPreferredLanguages)
        env_ = {'HTTP_ACCEPT_LANGUAGE': 'en'}

        # we should also test the correct semantics of the locale
        for httplang in ('it', 'it-ch', 'it-CH', 'IT', 'IT-CH', 'IT-ch'):
            env = env_.copy()
            env['HTTP_ACCEPT_LANGUAGE'] = httplang
            request = self._makeOne(environ=env)
            locale = request.locale
            self.assertTrue(ILocale.providedBy(locale))
            parts = httplang.split('-')
            lang = parts.pop(0).lower()
            territory = variant = None
            if parts:
                territory = parts.pop(0).upper()
            if parts:
                variant = parts.pop(0).upper()
            self.assertEqual(locale.id.language, lang)
            self.assertEqual(locale.id.territory, territory)
            self.assertEqual(locale.id.variant, variant)

    def test_locale_fallback(self):
        provideAdapter(BrowserLanguages, [IHTTPRequest],
                       IUserPreferredLanguages)

        env = {'HTTP_ACCEPT_LANGUAGE': 'xx'}

        # Now test for non-existant locale fallback
        request = self._makeOne(environ=env)
        locale = request.locale

        self.assertTrue(ILocale.providedBy(locale))
        self.assertTrue(locale.id.language is None)
        self.assertTrue(locale.id.territory is None)
        self.assertTrue(locale.id.variant is None)

    def test_method_GET(self):
        env = {'REQUEST_METHOD': 'GET'}
        request = self._makeOne(environ=env)
        self.assertEqual(request.method, 'GET')

    def test_method_POST(self):
        env = {'REQUEST_METHOD': 'POST'}
        request = self._makeOne(environ=env)
        self.assertEqual(request.method, 'POST')

    def test_getClientAddr_wo_trusted_proxy(self):
        env = {'REMOTE_ADDR': '127.0.0.1',
               'HTTP_X_FORWARDED_FOR': '10.1.20.30, 192.168.1.100'}
        request = self._makeOne(environ=env)
        self.assertEqual(request.getClientAddr(), '127.0.0.1')

    def test_getClientAddr_one_trusted_proxy(self):
        from ZPublisher.HTTPRequest import trusted_proxies
        env = {'REMOTE_ADDR': '127.0.0.1',
               'HTTP_X_FORWARDED_FOR': '10.1.20.30, 192.168.1.100'}

        orig = trusted_proxies[:]
        try:
            trusted_proxies.append('127.0.0.1')
            request = self._makeOne(environ=env)
            self.assertEqual(request.getClientAddr(), '192.168.1.100')
        finally:
            trusted_proxies[:] = orig

    def test_getClientAddr_trusted_proxy_last(self):
        from ZPublisher.HTTPRequest import trusted_proxies
        env = {'REMOTE_ADDR': '192.168.1.100',
               'HTTP_X_FORWARDED_FOR': '10.1.20.30, 192.168.1.100'}

        orig = trusted_proxies[:]
        try:
            trusted_proxies.append('192.168.1.100')
            request = self._makeOne(environ=env)
            self.assertEqual(request.getClientAddr(), '10.1.20.30')
        finally:
            trusted_proxies[:] = orig

    def test_getClientAddr_trusted_proxy_no_REMOTE_ADDR(self):
        from ZPublisher.HTTPRequest import trusted_proxies
        env = {'HTTP_X_FORWARDED_FOR': '10.1.20.30, 192.168.1.100'}

        orig = trusted_proxies[:]
        try:
            trusted_proxies.append('192.168.1.100')
            request = self._makeOne(environ=env)
            self.assertEqual(request.getClientAddr(), '')
        finally:
            trusted_proxies[:] = orig

    def test_getHeader_exact(self):
        environ = self._makePostEnviron()
        request = self._makeOne(environ=environ)
        self.assertEqual(request.getHeader('content-type'),
                         'multipart/form-data; boundary=12345')

    def test_getHeader_case_insensitive(self):
        environ = self._makePostEnviron()
        request = self._makeOne(environ=environ)
        self.assertEqual(request.getHeader('Content-Type'),
                         'multipart/form-data; boundary=12345')

    def test_getHeader_underscore_is_dash(self):
        environ = self._makePostEnviron()
        request = self._makeOne(environ=environ)
        self.assertEqual(request.getHeader('content_type'),
                         'multipart/form-data; boundary=12345')

    def test_getHeader_literal_turns_off_case_normalization(self):
        environ = self._makePostEnviron()
        request = self._makeOne(environ=environ)
        self.assertEqual(request.getHeader('Content-Type', literal=True), None)

    def test_getHeader_nonesuch(self):
        environ = self._makePostEnviron()
        request = self._makeOne(environ=environ)
        self.assertEqual(request.getHeader('none-such'), None)

    def test_getHeader_nonesuch_with_default(self):
        environ = self._makePostEnviron()
        request = self._makeOne(environ=environ)
        self.assertEqual(request.getHeader('Not-existant', default='Whatever'),
                         'Whatever')

    def test_clone_updates_method_to_GET(self):
        request = self._makeOne(environ={'REQUEST_METHOD': 'POST'})
        request['PARENTS'] = [object()]
        clone = request.clone()
        self.assertEqual(clone.method, 'GET')

    def test_clone_keeps_preserves__auth(self):
        request = self._makeOne()
        request['PARENTS'] = [object()]
        request._auth = 'foobar'
        clone = request.clone()
        self.assertEqual(clone._auth, 'foobar')

    def test_clone_doesnt_re_clean_environ(self):
        request = self._makeOne()
        request.environ['HTTP_CGI_AUTHORIZATION'] = 'lalalala'
        request['PARENTS'] = [object()]
        clone = request.clone()
        self.assertEqual(clone.environ['HTTP_CGI_AUTHORIZATION'], 'lalalala')

    def test_clone_keeps_only_last_PARENT(self):
        PARENTS = [object(), object()]
        request = self._makeOne()
        request['PARENTS'] = PARENTS
        clone = request.clone()
        self.assertEqual(clone['PARENTS'], PARENTS[1:])

    def test_clone_preserves_response_class(self):
        class DummyResponse:
            pass
        environ = self._makePostEnviron()
        request = self._makeOne(None, environ, DummyResponse())
        request['PARENTS'] = [object()]
        clone = request.clone()
        self.assertIsInstance(clone.response, DummyResponse)

    def test_clone_preserves_request_subclass(self):
        class SubRequest(self._getTargetClass()):
            pass
        environ = self._makePostEnviron()
        request = SubRequest(None, environ, None)
        request['PARENTS'] = [object()]
        clone = request.clone()
        self.assertIsInstance(clone, SubRequest)

    def test_clone_preserves_direct_interfaces(self):
        from zope.interface import Interface
        from zope.interface import directlyProvides

        class IFoo(Interface):
            pass
        request = self._makeOne()
        request['PARENTS'] = [object()]
        directlyProvides(request, IFoo)
        clone = request.clone()
        self.assertTrue(IFoo.providedBy(clone))

    def test_resolve_url_doesnt_send_endrequestevent(self):
        # The following imports are necessary:
        #  They happen implicitely in `request.resolve_url`
        #  They creates `zope.schema` events
        # Doing them here avoids those unrelated events
        import OFS.PropertyManager  # noqa: F401
        import OFS.SimpleItem  # noqa: F401
        #
        import zope.event
        events = []
        zope.event.subscribers.append(events.append)
        request = self._makeOne()
        request['PARENTS'] = [object()]
        try:
            request.resolve_url(request.script + '/')
        finally:
            zope.event.subscribers.remove(events.append)
        self.assertFalse(
            len(events),
            "HTTPRequest.resolve_url should not emit events")

    def test_resolve_url_errorhandling(self):
        # Check that resolve_url really raises the same error
        # it received from ZPublisher.BaseRequest.traverse
        request = self._makeOne()
        request['PARENTS'] = [object()]
        self.assertRaises(
            NotFound, request.resolve_url, request.script + '/does_not_exist')

    def test_parses_json_cookies(self):
        # https://bugs.launchpad.net/zope2/+bug/563229
        # reports cookies in the wild with embedded double quotes (e.g,
        # JSON-encoded data structures.
        env = {
            'SERVER_NAME': 'testingharnas',
            'SERVER_PORT': '80',
            'HTTP_COOKIE': 'json={"intkey":123,"stringkey":"blah"}; '
                           'anothercookie=boring; baz'
        }
        req = self._makeOne(environ=env)
        self.assertEqual(req.cookies['json'],
                         '{"intkey":123,"stringkey":"blah"}')
        self.assertEqual(req.cookies['anothercookie'], 'boring')

    def test_getVirtualRoot(self):
        # https://bugs.launchpad.net/zope2/+bug/193122
        req = self._makeOne()

        req._script = []
        self.assertEqual(req.getVirtualRoot(), '')

        req._script = ['foo', 'bar']
        self.assertEqual(req.getVirtualRoot(), '/foo/bar')

    def test__str__returns_native_string(self):
        r = self._makeOne()
        self.assertIsInstance(str(r), str)

    def test___str____password_field(self):
        # It obscures password fields.
        req = self._makeOne()
        req.form['passwd'] = 'secret'

        self.assertNotIn('secret', str(req))
        self.assertIn('password obscured', str(req))

    def test_text__password_field(self):
        # It obscures password fields.
        req = self._makeOne()
        req.form['passwd'] = 'secret'

        self.assertNotIn('secret', req.text())
        self.assertIn('password obscured', req.text())

    _xmlrpc_call = b"""<?xml version="1.0"?>
    <methodCall>
      <methodName>examples.getStateName</methodName>
      <params>
         <param>
            <value><i4>41</i4></value>
            </param>
         </params>
      </methodCall>
    """

    def test_processInputs_xmlrpc_with_args(self):
        req = self._makeOne(
            stdin=BytesIO(self._xmlrpc_call),
            environ=dict(REQUEST_METHOD="POST", CONTENT_TYPE="text/xml"))
        req.processInputs()
        self.assertTrue(is_xmlrpc_response(req.response))
        self.assertEqual(req.args, (41,))
        self.assertEqual(req.other["PATH_INFO"], "/examples/getStateName")

    def test_processInputs_xmlrpc_controlled_allowed(self):
        req = self._makeOne(
            stdin=BytesIO(self._xmlrpc_call),
            environ=dict(REQUEST_METHOD="POST", CONTENT_TYPE="text/xml"))
        with self._xmlrpc_control(lambda request: True):
            req.processInputs()
        self.assertTrue(is_xmlrpc_response(req.response))

    def test_processInputs_xmlrpc_controlled_disallowed(self):
        req = self._makeOne(
            environ=dict(REQUEST_METHOD="POST", CONTENT_TYPE="text/xml"))
        with self._xmlrpc_control(lambda request: False):
            req.processInputs()
        self.assertFalse(is_xmlrpc_response(req.response))

    @contextmanager
    def _xmlrpc_control(self, allow):
        gsm = getGlobalSiteManager()
        gsm.registerUtility(allow, IXmlrpcChecker)
        yield
        gsm.unregisterUtility(allow, IXmlrpcChecker)

    def test_url_scheme(self):
        # The default is http
        env = {'SERVER_NAME': 'myhost', 'SERVER_PORT': 80}
        req = self._makeOne(environ=env)
        self.assertEqual(req['SERVER_URL'], 'http://myhost')

        # If we bang a SERVER_URL into the environment it is retained
        env = {'SERVER_URL': 'https://anotherserver:8443'}
        req = self._makeOne(environ=env)
        self.assertEqual(req['SERVER_URL'], 'https://anotherserver:8443')

        # Now go through the various environment values that signal
        # a request uses the https URL scheme
        for val in ('on', 'ON', '1'):
            env = {'SERVER_NAME': 'myhost', 'SERVER_PORT': 443, 'HTTPS': val}
            req = self._makeOne(environ=env)
            self.assertEqual(req['SERVER_URL'], 'https://myhost')

        env = {'SERVER_NAME': 'myhost', 'SERVER_PORT': 443,
               'SERVER_PORT_SECURE': 1}
        req = self._makeOne(environ=env)
        self.assertEqual(req['SERVER_URL'], 'https://myhost')

        env = {'SERVER_NAME': 'myhost', 'SERVER_PORT': 443,
               'REQUEST_SCHEME': 'HTTPS'}
        req = self._makeOne(environ=env)
        self.assertEqual(req['SERVER_URL'], 'https://myhost')

        env = {'SERVER_NAME': 'myhost', 'SERVER_PORT': 443,
               'wsgi.url_scheme': 'https'}
        req = self._makeOne(environ=env)
        self.assertEqual(req['SERVER_URL'], 'https://myhost')

    def test_form_urlencoded(self):
        body = b"a=1"
        env = self._makePostEnviron(body, False)
        req = self._makeOne(stdin=BytesIO(body), environ=env)
        req.processInputs()
        self.assertEqual(req.form["a"], "1")
        req = self._makeOne(stdin=BytesIO(body), environ=env)
        with patch("ZPublisher.HTTPRequest.FORM_MEMORY_LIMIT", 1):
            with self.assertRaises(BadRequest):
                req.processInputs()

    def test_bytes_converter(self):
        val = "äöü".encode("latin-1")
        body = b"a:bytes:latin-1=" + val
        env = self._makePostEnviron(body, False)
        req = self._makeOne(stdin=BytesIO(body), environ=env)
        req.processInputs()
        self.assertEqual(req.form["a"], val)

    def test_get_with_body_and_query_string_ignores_body(self):
        req_factory = self._getTargetClass()
        req = req_factory(
            BytesIO(b"foo"),
            {
                "SERVER_NAME": "localhost",
                "SERVER_PORT": "8080",
                "REQUEST_METHOD": "GET",
                "QUERY_STRING": "bar"
            },
            None,
        )
        req.processInputs()
        self.assertDictEqual(req.form, {"bar": ""})

    def test_put_with_body_and_query_string(self):
        req_factory = self._getTargetClass()
        req = req_factory(
            BytesIO(b"foo"),
            {
                "SERVER_NAME": "localhost",
                "SERVER_PORT": "8080",
                "REQUEST_METHOD": "PUT",
                "QUERY_STRING": "bar=bar"
            },
            None,
        )
        req.processInputs()
        self.assertEqual(req.BODY, b"foo")
        self.assertEqual(req.form["bar"], "bar")

    def test_issue_1095(self):
        body = TEST_ISSUE_1095_DATA
        env = self._makePostEnviron(body)
        req = self._makeOne(BytesIO(body), env)
        req.processInputs()
        r = req["r"]
        self.assertEqual(len(r), 2)
        self.assertIsInstance(r[0].x, FileUpload)
        self.assertIsInstance(r[1].x, str)
        r = req.taintedform["r"]
        self.assertIsInstance(r[0].x, FileUpload)
        self.assertIsInstance(r[1].x, TaintedString)

    def test_field_charset(self):
        body = TEST_FIELD_CHARSET_DATA
        env = self._makePostEnviron(body)
        env["QUERY_STRING"] = "y=" + quote_plus("äöü")
        req = self._makeOne(BytesIO(body), env)
        req.processInputs()
        self.assertEqual(req["x"], "äöü")
        self.assertEqual(req["y"], "äöü")

    def test_form_charset(self):
        body = ("x=" + quote_plus("äöü", encoding="latin-1")).encode("ASCII")
        env = self._makePostEnviron(body)
        env["CONTENT_TYPE"] = \
            "application/x-www-form-urlencoded; charset=latin-1"
        env["QUERY_STRING"] = "y=" + quote_plus("äöü")
        req = self._makeOne(BytesIO(body), env)
        req.processInputs()
        self.assertEqual(req["x"], "äöü")
        self.assertEqual(req["y"], "äöü")


class TestHTTPRequestZope3Views(TestRequestViewsBase):

    def _makeOne(self, root):
        from zope.interface import directlyProvides
        from zope.publisher.browser import IDefaultBrowserLayer
        request = HTTPRequestFactoryMixin()._makeOne()
        request['PARENTS'] = [root]
        # The request needs to implement the proper interface
        directlyProvides(request, IDefaultBrowserLayer)
        return request

    def test_no_traversal_of_view_request_attribute(self):
        # make sure views don't accidentally publish the 'request' attribute
        root, _ = self._makeRootAndFolder()

        # make sure the view itself is traversable:
        view = self._makeOne(root).traverse('folder/@@meth')
        from ZPublisher.HTTPRequest import HTTPRequest
        self.assertEqual(view.request.__class__, HTTPRequest,)

        # but not the request:
        self.assertRaises(
            NotFound,
            self._makeOne(root).traverse, 'folder/@@meth/request'
        )


class TestSearchType(unittest.TestCase):
    """Test `ZPublisher.HTTPRequest.search_type`

    see "https://github.com/zopefoundation/Zope/pull/512"
    """
    def check(self, val, expect):
        mo = search_type(val)
        if expect is None:
            self.assertIsNone(mo)
        else:
            self.assertIsNotNone(mo)
            self.assertEqual(mo.group(), expect)

    def test_image_control(self):
        self.check("abc.x", ".x")
        self.check("abc.y", ".y")
        self.check("abc.xy", None)

    def test_type(self):
        self.check("abc:int", ":int")

    def test_leftmost(self):
        self.check("abc:int:record", ":record")

    def test_special(self):
        self.check("abc:a-_0b", ":a-_0b")


class _Unseekable:
    """Auxiliary class emulating an unseekable file like object"""
    def __init__(self, file):
        for m in ("read", "readline", "close", "__del__"):
            setattr(self, m, getattr(file, m))


TEST_POST_ENVIRON = {
    'CONTENT_LENGTH': None,
    'REQUEST_METHOD': 'POST',
    'SERVER_NAME': 'localhost',
    'SERVER_PORT': '80',
}

TEST_FILE_DATA = b'''
--12345
Content-Disposition: form-data; name="smallfile"; filename="smallfile"
Content-Type: application/octet-stream

test

--12345--
'''

TEST_FILE_DATA_UNSPECIFIED = b'''
--12345
Content-Disposition: form-data; name="smallfile"; filename=""
Content-Type: application/octet-stream

--12345--
'''

TEST_LARGEFILE_DATA = b'''
--12345
Content-Disposition: form-data; name="largefile"; filename="largefile"
Content-Type: application/octet-stream

test %s

--12345--
''' % (b'test' * 1000)

TEST_ISSUE_1095_DATA = b'''
--12345
Content-Disposition: form-data; name="r.x:records"; filename="fn"
Content-Type: application/octet-stream

test

--12345
Content-Disposition: form-data; name="r.x:records"
Content-Type: text/html

<body>abc</body>

--12345--
'''

TEST_FIELD_CHARSET_DATA = b'''
--12345
Content-Disposition: form-data; name="x"
Content-Type: text/plain; charset=latin-1

%s
--12345--
''' % 'äöü'.encode("latin-1")
