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
import unittest

class VersionTextTestCase(unittest.TestCase):

    def setUp(self):
        self._resetModuleGlobals()

    def tearDown(self):
        import os
        from App.version_txt import _version_file
        if _version_file is not None:
            os.unlink(_version_file)
        self._resetModuleGlobals()

    def _resetModuleGlobals(self):
        from App import version_txt
        version_txt._filename = 'version.txt'
        version_txt._version_file = None
        version_txt._version_string = None
        version_txt._zope_version = None

    def writeVersion(self, s):
        import os
        import tempfile
        from App import version_txt 
        assert version_txt._version_file is None
        f, version_txt._version_file = tempfile.mkstemp()
        os.write(f, s)
        os.close(f)

    def test_without_version_txt(self):
        from App import version_txt
        from App.version_txt import getZopeVersion
        version_txt._filename = ''
        self.assertEqual(getZopeVersion(), (-1, -1, -1, '', -1))

    def test_with_version_txt_final(self):
        from App.version_txt import getZopeVersion
        self.writeVersion("Zope 2.6.1 (source release, python 2.1, linux2)")
        self.assertEqual(getZopeVersion(), (2, 6, 1, '', -1))

    def test_with_version_txt_beta(self):
        from App.version_txt import getZopeVersion
        self.writeVersion("Zope 2.6.1b2 (source release, python 2.1, linux2)")
        self.assertEqual(getZopeVersion(), (2, 6, 1, 'b', 2))


def test_suite():
    return unittest.makeSuite(VersionTextTestCase)

if __name__ == "__main__":
    unittest.main(defaultTest="test_suite")
