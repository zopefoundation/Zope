##############################################################################
#
# Copyright (c) 2003 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Tests of the content_types extension mechanism.

$Id$
"""

import mimetypes
import os.path
import sys
import unittest

from OFS import content_types

try:
    __file__
except NameError:
    __file__ = os.path.realpath(sys.argv[0])

here = os.path.dirname(os.path.abspath(__file__))
MIME_TYPES_1 = os.path.join(here, "mime.types-1")
MIME_TYPES_2 = MIME_TYPES_1[:-1] + "2"


class ContentTypesTestCase(unittest.TestCase):

    def setUp(self):
        self._old_state = mimetypes.__dict__.copy()

    def tearDown(self):
        mimetypes.__dict__.update(self._old_state)

    def check_types_count(self, delta):
        self.assertEqual(len(mimetypes.types_map),
                         len(self._old_state["types_map"]) + delta)

    def test_add_one_file(self):
        ntypes = len(mimetypes.types_map)
        content_types.add_files([MIME_TYPES_1])
        ctype, encoding = content_types.guess_content_type("foo.ztmt-1")
        self.assert_(encoding is None)
        self.assertEqual(ctype, "text/x-vnd.zope.test-mime-type-1")
        ctype, encoding = content_types.guess_content_type("foo.ztmt-1.gz")
        self.assertEqual(encoding, "gzip")
        self.assertEqual(ctype, "text/x-vnd.zope.test-mime-type-1")
        self.check_types_count(1)

    def test_add_two_files(self):
        ntypes = len(mimetypes.types_map)
        content_types.add_files([MIME_TYPES_1, MIME_TYPES_2])
        ctype, encoding = content_types.guess_content_type("foo.ztmt-1")
        self.assert_(encoding is None)
        self.assertEqual(ctype, "text/x-vnd.zope.test-mime-type-1")
        ctype, encoding = content_types.guess_content_type("foo.ztmt-2")
        self.assert_(encoding is None)
        self.assertEqual(ctype, "text/x-vnd.zope.test-mime-type-2")
        self.check_types_count(2)


def test_suite():
    return unittest.makeSuite(ContentTypesTestCase)

if __name__ == '__main__':
    unittest.main()
