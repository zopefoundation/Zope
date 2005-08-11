##############################################################################
#
# Copyright (c) 2001 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""ustr unit tests.

$Id$
"""

import unittest

from DocumentTemplate.ustr import ustr


class force_str:
    # A class whose string representation is not always a plain string:
    def __init__(self,s):
        self.s = s
    def __str__(self):
        return self.s


class Foo(str):

    pass


class Bar(unicode):

    pass


class UnicodeTests(unittest.TestCase):

    def testPlain(self):
        a = ustr('hello')
        assert a=='hello', `a`
        a = ustr(force_str('hello'))
        assert a=='hello', `a`
        a = ustr(chr(200))
        assert a==chr(200), `a`
        a = ustr(force_str(chr(200)))
        assert a==chr(200), `a`
        a = ustr(22)
        assert a=='22', `a`
        a = ustr([1,2,3])
        assert a=='[1, 2, 3]', `a`

    def testUnicode(self):
        a = ustr(u'hello')
        assert a=='hello', `a`
        a = ustr(force_str(u'hello'))
        assert a=='hello', `a`
        a = ustr(unichr(200))
        assert a==unichr(200), `a`
        a = ustr(force_str(unichr(200)))
        assert a==unichr(200), `a`

    def testExceptions(self):
        a = ustr(ValueError(unichr(200)))
        assert a==unichr(200), `a`

    def testCustomStrings(self):
        a = ustr(Foo('foo'))
        self.failUnlessEqual(type(a), Foo)
        a = ustr(Bar('bar'))
        self.failUnlessEqual(type(a), Bar)


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest( unittest.makeSuite( UnicodeTests ) )
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
