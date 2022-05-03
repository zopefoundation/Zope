##############################################################################
#
# Copyright (c) 2004 Zope Foundation and Contributors.
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
"""Tests for the recreated `getZopeVersion`."""

import unittest

from pkg_resources import get_distribution

from App.version_txt import getZopeVersion


class Test(unittest.TestCase):
    def test_major(self):
        self.assertEqual(
            getZopeVersion().major,
            int(get_distribution("Zope").version.split(".")[0]))

    def test_types(self):
        zv = getZopeVersion()
        for i in (0, 1, 4):
            self.assertIsInstance(zv[i], int, str(i))
        self.assertIsInstance(zv[3], str, '3')

    def test__parse_version_data(self):
        from App.version_txt import _parse_version_data

        parsed = _parse_version_data('5')
        self.assertEqual(parsed.major, 5)
        self.assertEqual(parsed.minor, 0)
        self.assertEqual(parsed.micro, 0)
        self.assertEqual(parsed.status, '')
        self.assertEqual(parsed.release, -1)

        parsed = _parse_version_data('5a2')
        self.assertEqual(parsed.major, 5)
        self.assertEqual(parsed.minor, 0)
        self.assertEqual(parsed.micro, '0a2')
        self.assertEqual(parsed.status, '')
        self.assertEqual(parsed.release, -1)

        parsed = _parse_version_data('5a2.dev0')
        self.assertEqual(parsed.major, 5)
        self.assertEqual(parsed.minor, 0)
        self.assertEqual(parsed.micro, '0a2')
        self.assertEqual(parsed.status, 'dev')
        self.assertEqual(parsed.release, 0)

        parsed = _parse_version_data('5.dev0')
        self.assertEqual(parsed.major, 5)
        self.assertEqual(parsed.minor, 0)
        self.assertEqual(parsed.micro, 0)
        self.assertEqual(parsed.status, 'dev')
        self.assertEqual(parsed.release, 0)

        parsed = _parse_version_data('5.1')
        self.assertEqual(parsed.major, 5)
        self.assertEqual(parsed.minor, 1)
        self.assertEqual(parsed.micro, 0)
        self.assertEqual(parsed.status, '')
        self.assertEqual(parsed.release, -1)

        parsed = _parse_version_data('5.1a2.dev0')
        self.assertEqual(parsed.major, 5)
        self.assertEqual(parsed.minor, 1)
        self.assertEqual(parsed.micro, '0a2')
        self.assertEqual(parsed.status, 'dev')
        self.assertEqual(parsed.release, 0)

        parsed = _parse_version_data('5.1.2')
        self.assertEqual(parsed.major, 5)
        self.assertEqual(parsed.minor, 1)
        self.assertEqual(parsed.micro, 2)
        self.assertEqual(parsed.status, '')
        self.assertEqual(parsed.release, -1)

        parsed = _parse_version_data('5.1.3.dev0')
        self.assertEqual(parsed.major, 5)
        self.assertEqual(parsed.minor, 1)
        self.assertEqual(parsed.micro, 3)
        self.assertEqual(parsed.status, 'dev')
        self.assertEqual(parsed.release, 0)

        parsed = _parse_version_data('5.1.3a1.dev0')
        self.assertEqual(parsed.major, 5)
        self.assertEqual(parsed.minor, 1)
        self.assertEqual(parsed.micro, '3a1')
        self.assertEqual(parsed.status, 'dev')
        self.assertEqual(parsed.release, 0)
