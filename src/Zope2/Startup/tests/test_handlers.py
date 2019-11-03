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


class TestNameToIPs(unittest.TestCase):

    def _callFUT(self, host):
        from Zope2.Startup.handlers import _name_to_ips
        return _name_to_ips(host)

    def test_ip4(self):
        self.assertEqual(self._callFUT('127.0.0.1'), ['127.0.0.1'])
        self.assertEqual(self._callFUT('8.8.8.8'), ['8.8.8.8'])

    def test_ip6(self):
        self.assertEqual(self._callFUT('::1'), ['::1'])
        self.assertEqual(self._callFUT(
            '0000:0000:0000:0000:0000:0abc:0007:0def'), ['::abc:7:def'])

    def test_hostname(self):
        hosts = self._callFUT('localhost')
        self.assertTrue(hosts == ['127.0.0.1'] or hosts == ['::1'], hosts)

    def test_encoding(self):
        self.assertEqual(self._callFUT(
            b'0000:0000:0000:0000:0000:0abc:0007:0def'), ['::abc:7:def'])
        self.assertEqual(self._callFUT(
            '0000:0000:0000:0000:0000:0abc:0007:0def'), ['::abc:7:def'])
