# -*- encoding: utf-8 -*-
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

from six import PY2


class SafeUnicodeTests(unittest.TestCase):

    def _makeOne(self, value):
        from ZPublisher.utils import safe_unicode
        return safe_unicode(value)

    def test_ascii(self):
        self.assertEqual(self._makeOne('foo'), u'foo')
        self.assertEqual(self._makeOne(b'foo'), u'foo')

    def test_latin_1(self):
        self.assertEqual(self._makeOne(b'fo\xf6'), u'fo\ufffd')

    def test_unicode(self):
        self.assertEqual(self._makeOne(u'foö'), u'foö')

    def test_utf_8(self):
        if PY2:
            self.assertEqual(self._makeOne('test\xc2\xae'), u'test\xae')
        else:
            self.assertEqual(self._makeOne('test\xc2\xae'), u'test\xc2\xae')
        self.assertEqual(self._makeOne(b'test\xc2\xae'), u'test\xae')
