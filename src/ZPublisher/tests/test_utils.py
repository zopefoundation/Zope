##############################################################################
#
# Copyright (c) 2017 Zope Foundation and Contributors.
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

import unittest


class SafeUnicodeTests(unittest.TestCase):

    def _makeOne(self, value):
        from ZPublisher.utils import safe_unicode
        return safe_unicode(value)

    def test_ascii(self):
        self.assertEqual(self._makeOne('foo'), 'foo')
        self.assertEqual(self._makeOne(b'foo'), 'foo')

    def test_latin_1(self):
        self.assertEqual(self._makeOne(b'fo\xf6'), 'fo\ufffd')

    def test_unicode(self):
        self.assertEqual(self._makeOne('foö'), 'foö')

    def test_utf_8(self):
        self.assertEqual(self._makeOne('test\xc2\xae'), 'test\xc2\xae')
        self.assertEqual(self._makeOne(b'test\xc2\xae'), 'test\xae')


class NoUpdatePropertyManager:
    """PropertyManager without _updateProperty method.

    This is a simplified version of the original PropertyManager,
    with only the methods we need.
    """
    _properties = ()

    def _setPropValue(self, id, value):
        if type(value) == list:
            value = tuple(value)
        setattr(self, id, value)

    def _setProperty(self, id, value, type='string'):
        self._properties = self._properties + ({'id': id, 'type': type},)
        self._setPropValue(id, value)

    def hasProperty(self, id):
        for p in self._properties:
            if id == p['id']:
                return 1
        return 0

    def getProperty(self, id, d=None):
        if self.hasProperty(id):
            return getattr(self, id)
        return d

    def getPropertyType(self, id):
        for md in self._properties:
            if md['id'] == id:
                return md.get('type', 'string')
        return None

    def _propertyMap(self):
        return self._properties

    def propertyMap(self):
        return tuple(dict.copy() for dict in self._propertyMap())


class NoPropertiesManager(NoUpdatePropertyManager):
    """PropertyManager with _updateProperty method but without _properties."""
    _properties = None

    def _updateProperty(self, id, value):
        self._setPropValue(id, value)


class FixPropertiesTests(unittest.TestCase):

    def _makeOne(self):
        from OFS.PropertyManager import PropertyManager

        return PropertyManager()

    def test_lines(self):
        from ZPublisher.utils import fix_properties

        obj = self._makeOne()
        obj._setProperty("mixed", ["text and", b"bytes"], "lines")
        self.assertEqual(obj.getProperty("mixed"), ("text and", b"bytes"))
        self.assertEqual(obj.getPropertyType("mixed"), "lines")

        fix_properties(obj)
        self.assertEqual(obj.getProperty("mixed"), ("text and", "bytes"))
        self.assertEqual(obj.getPropertyType("mixed"), "lines")

    def test_ulines(self):
        from ZPublisher.utils import fix_properties

        obj = self._makeOne()
        obj._setProperty("mixed", ["text and", b"bytes"], "ulines")
        self.assertEqual(obj.getProperty("mixed"), ("text and", b"bytes"))
        self.assertEqual(obj.getPropertyType("mixed"), "ulines")

        fix_properties(obj)
        self.assertEqual(obj.getProperty("mixed"), ("text and", "bytes"))
        self.assertEqual(obj.getPropertyType("mixed"), "lines")

    def test_utokens(self):
        from ZPublisher.utils import fix_properties

        obj = self._makeOne()
        obj._setProperty("mixed", ["text", "and", b"bytes"], "utokens")
        self.assertEqual(obj.getProperty("mixed"), ("text", "and", b"bytes"))
        self.assertEqual(obj.getPropertyType("mixed"), "utokens")

        fix_properties(obj)
        self.assertEqual(obj.getProperty("mixed"), ("text", "and", "bytes"))
        self.assertEqual(obj.getPropertyType("mixed"), "tokens")

    def test_utext(self):
        from ZPublisher.utils import fix_properties

        obj = self._makeOne()
        obj._setProperty("prop1", "multiple\nlines", "utext")
        self.assertEqual(obj.getProperty("prop1"), "multiple\nlines")
        self.assertEqual(obj.getPropertyType("prop1"), "utext")

        fix_properties(obj)
        self.assertEqual(obj.getProperty("prop1"), "multiple\nlines")
        self.assertEqual(obj.getPropertyType("prop1"), "text")

    def test_ustring(self):
        from ZPublisher.utils import fix_properties

        obj = self._makeOne()
        obj._setProperty("prop1", "single line", "ustring")
        self.assertEqual(obj.getProperty("prop1"), "single line")
        self.assertEqual(obj.getPropertyType("prop1"), "ustring")

        fix_properties(obj)
        self.assertEqual(obj.getProperty("prop1"), "single line")
        self.assertEqual(obj.getPropertyType("prop1"), "string")

    def test_no_update(self):
        # Test that an object without _updateProperty method does not trip up
        # our code.
        from ZPublisher.utils import fix_properties

        obj = NoUpdatePropertyManager()
        obj._setProperty("mixed", ["text and", b"bytes"], "lines")
        self.assertEqual(obj.getProperty("mixed"), ("text and", b"bytes"))
        self.assertEqual(obj.getPropertyType("mixed"), "lines")

        # This should not raise an error.
        fix_properties(obj)
        # The properties should have remained the same.
        self.assertEqual(obj.getProperty("mixed"), ("text and", b"bytes"))
        self.assertEqual(obj.getPropertyType("mixed"), "lines")

    def test_no_properties(self):
        # Test that an object with a failing propertyMap method,
        # due to _properties=None, does not trip up our code.
        from ZPublisher.utils import fix_properties

        obj = NoPropertiesManager()
        # This should not raise an error.
        fix_properties(obj)
