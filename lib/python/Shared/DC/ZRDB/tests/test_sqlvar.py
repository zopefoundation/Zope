##############################################################################
#
# Copyright (c) 2005 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
import unittest

from UserDict import UserDict

def _sql_quote(v):
    return '"%s"' % v

class FauxMultiDict(UserDict):

    def getitem(self, key, call):
        if key == 'sql_quote__':
            return _sql_quote

        v = self[key]
        if v is not None:
            if call and callable(v):
                v = v()
        return v

class SQLVarTests(unittest.TestCase):

    def _getTargetClass(self):
        from Shared.DC.ZRDB.sqlvar import SQLVar
        return SQLVar

    def _makeOne(self, *args, **kw):
        return self._getTargetClass()(*args, **kw)

    def test_constructor_no_type(self):
        from DocumentTemplate.DT_Util import ParseError
        self.assertRaises(ParseError, self._makeOne, 'foo')

    def test_constructor_invalid_type(self):
        from DocumentTemplate.DT_Util import ParseError
        self.assertRaises(ParseError, self._makeOne, 'foo type="nonesuch"')

    def test_constructor_valid_type(self):
        from DocumentTemplate.DT_Util import ParseError
        v = self._makeOne('foo type="string"')
        self.assertEqual(v.__name__, 'foo')
        self.assertEqual(v.expr, 'foo')
        self.assertEqual(v.args['type'], 'string')

    def test_render_name_returns_value(self):
        v = self._makeOne('foo type="string"')
        self.assertEqual(v.render(FauxMultiDict(foo='FOO')), '"FOO"')

    def test_render_name_missing_required_raises_ValueError(self):
        v = self._makeOne('foo type="string"')
        self.assertRaises(ValueError, v.render, FauxMultiDict())

    def test_render_name_missing_optional_returns_null(self):
        v = self._makeOne('foo type="string" optional')
        self.assertEqual(v.render(FauxMultiDict()), 'null')

    def test_render_expr_returns_value(self):
        v = self._makeOne('expr="foo" type="string"')
        self.assertEqual(v.render(FauxMultiDict(foo='FOO')), '"FOO"')

    def test_render_expr_missing_required_raises_NameError(self):
        v = self._makeOne('expr="foo" type="string"')
        self.assertRaises(NameError, v.render, FauxMultiDict())

    def test_render_expr_missing_optional_returns_null(self):
        v = self._makeOne('expr="foo" type="string" optional')
        self.assertEqual(v.render(FauxMultiDict()), 'null')

    def test_render_int_returns_int_without_quoting(self):
        v = self._makeOne('expr="foo" type="int"')
        self.assertEqual(v.render(FauxMultiDict(foo=42)), '42')

    def test_render_int_with_long_returns_value_without_L(self):
        v = self._makeOne('expr="foo" type="int"')
        self.assertEqual(v.render(FauxMultiDict(foo='42L')), '42')

    def test_render_int_required_invalid_raises_ValueError(self):
        v = self._makeOne('expr="foo" type="int"')
        self.assertRaises(ValueError, v.render, FauxMultiDict(foo=''))

    def test_render_int_optional_invalid_returns_null(self):
        v = self._makeOne('expr="foo" type="int" optional')
        self.assertEqual(v.render(FauxMultiDict(foo='')), 'null')

    def test_render_float_returns_float_without_quoting(self):
        v = self._makeOne('expr="foo" type="float"')
        self.assertEqual(v.render(FauxMultiDict(foo=3.1415)), '3.1415')

    def test_render_float_with_long_returns_value_without_L(self):
        v = self._makeOne('expr="foo" type="float"')
        self.assertEqual(v.render(FauxMultiDict(foo='42L')), '42')

    def test_render_float_required_invalid_raises_ValueError(self):
        v = self._makeOne('expr="foo" type="float"')
        self.assertRaises(ValueError, v.render, FauxMultiDict(foo=''))

    def test_render_float_optional_invalid_returns_null(self):
        v = self._makeOne('expr="foo" type="float" optional')
        self.assertEqual(v.render(FauxMultiDict(foo='')), 'null')

    def test_render_nb_required_with_blank_raises_ValueError(self):
        v = self._makeOne('expr="foo" type="nb"')
        self.assertRaises(ValueError, v.render, FauxMultiDict(foo=''))

    def test_render_nb_optional_with_blank_returns_null(self):
        v = self._makeOne('expr="foo" type="nb" optional')
        self.assertEqual(v.render(FauxMultiDict(foo='')), 'null')

    def test_render_name_with_none_returns_null(self):
        # Collector #556, patch from Dieter Maurer
        v = self._makeOne('foo type="string"')
        self.assertEqual(v.render(FauxMultiDict(foo=None)), 'null')

    def test_render_expr_with_none_returns_null(self):
        # Collector #556, patch from Dieter Maurer
        v = self._makeOne('expr="foo" type="string"')
        self.assertEqual(v.render(FauxMultiDict(foo=None)), 'null')

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(SQLVarTests))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
