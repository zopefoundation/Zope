##############################################################################
#
# Copyright (c) 2010 Zope Foundation and Contributors.
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
"""Unit tests for unauthorized module.

$Id$
"""

import unittest
from zope.interface.verify import verifyClass

_MESSAGE = "You are not allowed to access '%s' in this context"


class UnauthorizedTests(unittest.TestCase):

    def _getTargetClass(self):
        from zExceptions.unauthorized import Unauthorized

        return Unauthorized

    def _makeOne(self, *args, **kw):
        return self._getTargetClass()(*args, **kw)

    def test_interfaces(self):
        from zope.security.interfaces import IUnauthorized

        verifyClass(IUnauthorized, self._getTargetClass())

    def test_empty(self):
        exc = self._makeOne()

        self.assertEqual(exc.name, None)
        self.assertEqual(exc.message, None)
        self.assertEqual(exc.value, None)
        self.assertEqual(exc.needed, None)

        self.assertEqual(str(exc), str(repr(exc)))
        self.assertEqual(unicode(exc), unicode(repr(exc)))

    def test_ascii_message(self):
        arg = 'ERROR MESSAGE'
        exc = self._makeOne(arg)

        self.assertEqual(exc.name, None)
        self.assertEqual(exc.message, arg)
        self.assertEqual(exc.value, None)
        self.assertEqual(exc.needed, None)

        self.assertEqual(str(exc), arg)
        self.assertEqual(unicode(exc), arg.decode('ascii'))

    def test_encoded_message(self):
        arg = u'ERROR MESSAGE \u03A9'.encode('utf-8')
        exc = self._makeOne(arg)

        self.assertEqual(exc.name, None)
        self.assertEqual(exc.message, arg)
        self.assertEqual(exc.value, None)
        self.assertEqual(exc.needed, None)

        self.assertEqual(str(exc), arg)
        self.assertRaises(UnicodeDecodeError, unicode, exc)

    def test_unicode_message(self):
        arg = u'ERROR MESSAGE \u03A9'
        exc = self._makeOne(arg)

        self.assertEqual(exc.name, None)
        self.assertEqual(exc.message, arg)
        self.assertEqual(exc.value, None)
        self.assertEqual(exc.needed, None)

        self.assertRaises(UnicodeEncodeError, str, exc)
        self.assertEqual(unicode(exc), arg)

    def test_ascii_name(self):
        arg = 'ERROR_NAME'
        exc = self._makeOne(arg)

        self.assertEqual(exc.name, arg)
        self.assertEqual(exc.message, None)
        self.assertEqual(exc.value, None)
        self.assertEqual(exc.needed, None)

        self.assertEqual(str(exc), _MESSAGE % arg)
        self.assertEqual(unicode(exc), _MESSAGE % arg.decode('ascii'))

    def test_encoded_name(self):
        arg = u'ERROR_NAME_\u03A9'.encode('utf-8')
        exc = self._makeOne(arg)

        self.assertEqual(exc.name, arg)
        self.assertEqual(exc.message, None)
        self.assertEqual(exc.value, None)
        self.assertEqual(exc.needed, None)

        self.assertEqual(str(exc), _MESSAGE % arg)
        self.assertRaises(UnicodeDecodeError, unicode, exc)

    def test_unicode_name(self):
        arg = u'ERROR_NAME_\u03A9'
        exc = self._makeOne(arg)

        self.assertEqual(exc.name, arg)
        self.assertEqual(exc.message, None)
        self.assertEqual(exc.value, None)
        self.assertEqual(exc.needed, None)

        self.assertRaises(UnicodeEncodeError, str, exc)
        self.assertEqual(unicode(exc), _MESSAGE % arg)


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(UnauthorizedTests))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
