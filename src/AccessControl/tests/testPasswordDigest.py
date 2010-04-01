##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
"""Test of AuthEncoding
"""

__rcs_id__='$Id$'
__version__='$Revision: 1.5 $'[11:-2]

import os, sys, unittest

from AccessControl import AuthEncoding
import unittest


class PasswordDigestTests (unittest.TestCase):

    def testGoodPassword(self):
        pw = 'good_password'
        assert len(AuthEncoding.listSchemes()) > 0  # At least one must exist!
        for id in AuthEncoding.listSchemes():
            enc = AuthEncoding.pw_encrypt(pw, id)
            assert enc != pw
            assert AuthEncoding.pw_validate(enc, pw)
            assert AuthEncoding.is_encrypted(enc)
            assert not AuthEncoding.is_encrypted(pw)

    def testBadPasword(self):
        pw = 'OK_pa55w0rd \n'
        for id in AuthEncoding.listSchemes():
            enc = AuthEncoding.pw_encrypt(pw, id)
            assert enc != pw
            assert not AuthEncoding.pw_validate(enc, 'xxx')
            assert not AuthEncoding.pw_validate(enc, enc)
            if id != 'CRYPT':
                # crypt truncates passwords and would fail this test.
                assert not AuthEncoding.pw_validate(enc, pw[:-1])
            assert not AuthEncoding.pw_validate(enc, pw[1:])
            assert AuthEncoding.pw_validate(enc, pw)

    def testShortPassword(self):
        pw = '1'
        for id in AuthEncoding.listSchemes():
            enc = AuthEncoding.pw_encrypt(pw, id)
            assert enc != pw
            assert AuthEncoding.pw_validate(enc, pw)
            assert not AuthEncoding.pw_validate(enc, enc)
            assert not AuthEncoding.pw_validate(enc, 'xxx')

    def testLongPassword(self):
        pw = 'Pw' * 2000
        for id in AuthEncoding.listSchemes():
            enc = AuthEncoding.pw_encrypt(pw, id)
            assert enc != pw
            assert AuthEncoding.pw_validate(enc, pw)
            assert not AuthEncoding.pw_validate(enc, enc)
            assert not AuthEncoding.pw_validate(enc, 'xxx')
            if id != 'CRYPT':
                # crypt truncates passwords and would fail these tests.
                assert not AuthEncoding.pw_validate(enc, pw[:-2])
                assert not AuthEncoding.pw_validate(enc, pw[2:])

    def testBlankPassword(self):
        pw = ''
        for id in AuthEncoding.listSchemes():
            enc = AuthEncoding.pw_encrypt(pw, id)
            assert enc != pw
            assert AuthEncoding.pw_validate(enc, pw)
            assert not AuthEncoding.pw_validate(enc, enc)
            assert not AuthEncoding.pw_validate(enc, 'xxx')

    def testUnencryptedPassword(self):
        # Sanity check
        pw = 'my-password'
        assert AuthEncoding.pw_validate(pw, pw)


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest( unittest.makeSuite( PasswordDigestTests ) )
    return suite

def main():
    unittest.TextTestRunner().run(test_suite())

if __name__ == '__main__':
    main()
