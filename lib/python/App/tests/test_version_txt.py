##############################################################################
#
# Copyright (c) 2003 Zope Corporation and Contributors.
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
"""Tests of the version number extraction.

$Id$
"""
import os
import unittest
import Zope2
import App.version_txt

class VersionTextTestCase(unittest.TestCase):

    def setUp(self):
        self.fn = os.path.join(os.path.dirname(Zope2.__file__), "version.txt")
        App.version_txt._test_reset()

    def tearDown(self):
        try:
            os.unlink(self.fn)
        except OSError:
            pass

    def writeVersion(self, s):
        f = open(self.fn, 'w')
        f.write(s)
        f.close()

    def test_without_version_txt(self):
        self.assertEqual(App.version_txt.getZopeVersion(),
                         (-1, -1, -1, '', -1))

    def test_with_version_txt_final(self):
        self.writeVersion("Zope 2.6.1 (source release, python 2.1, linux2)")
        self.assertEqual(App.version_txt.getZopeVersion(),
                         (2, 6, 1, '', -1))

    def test_with_version_txt_beta(self):
        self.writeVersion("Zope 2.6.1b2 (source release, python 2.1, linux2)")
        self.assertEqual(App.version_txt.getZopeVersion(),
                         (2, 6, 1, 'b', 2))


def test_suite():
    return unittest.makeSuite(VersionTextTestCase)

if __name__ == "__main__":
    unittest.main(defaultTest="test_suite")
