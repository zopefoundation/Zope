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
