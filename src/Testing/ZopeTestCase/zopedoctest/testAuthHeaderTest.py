##############################################################################
#
# Copyright (c) 2005 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Test for auth_header
"""

import unittest

from Testing.ZopeTestCase import TestCase
from Testing.ZopeTestCase import zopedoctest


auth_header = zopedoctest.functional.auth_header


class AuthHeaderTestCase(TestCase):

    def test_auth_encoded(self):
        header = 'Basic Z2xvYmFsbWdyOmdsb2JhbG1ncnB3'
        self.assertEqual(auth_header(header), header)

    def test_auth_non_encoded(self):
        header = 'Basic globalmgr:globalmgrpw'
        expected = 'Basic Z2xvYmFsbWdyOmdsb2JhbG1ncnB3'
        self.assertEqual(auth_header(header), expected)

    def test_auth_non_encoded_empty(self):
        header = 'Basic globalmgr:'
        expected = 'Basic Z2xvYmFsbWdyOg=='
        self.assertEqual(auth_header(header), expected)
        header = 'Basic :pass'
        expected = 'Basic OnBhc3M='
        self.assertEqual(auth_header(header), expected)

    def test_auth_non_encoded_colon(self):
        header = 'Basic globalmgr:pass:pass'
        expected = 'Basic Z2xvYmFsbWdyOnBhc3M6cGFzcw=='
        self.assertEqual(auth_header(header), expected)


def test_suite():
    return unittest.defaultTestLoader.loadTestsFromTestCase(AuthHeaderTestCase)
