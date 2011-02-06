##############################################################################
#
# Copyright (c) 2007 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Unit tests for util module.

$Id$
"""

import unittest

from ZPublisher.HTTPRequest import record as Record


class parseIndexRequestTests(unittest.TestCase):

    def _getTargetClass(self):
        from Products.PluginIndexes.common.util import parseIndexRequest

        return parseIndexRequest

    def _makeOne(self, *args, **kw):
        return self._getTargetClass()(*args, **kw)

    def test_get_record(self):
        record = Record()
        record.query = 'foo'
        record.level = 0
        record.operator = 'and'
        request = {'path': record}
        parser = self._makeOne(request, 'path', ('query','level','operator'))
        self.assertEqual(parser.get('keys'), ['foo'])
        self.assertEqual(parser.get('level'), 0)
        self.assertEqual(parser.get('operator'), 'and')

    def test_get_dict(self):
        request = {'path': {'query': 'foo', 'level': 0, 'operator': 'and'}}
        parser = self._makeOne(request, 'path', ('query','level','operator'))
        self.assertEqual(parser.get('keys'), ['foo'])
        self.assertEqual(parser.get('level'), 0)
        self.assertEqual(parser.get('operator'), 'and')

    def test_get_string(self):
        request = {'path': 'foo', 'path_level': 0, 'path_operator': 'and'}
        parser = self._makeOne(request, 'path', ('query','level','operator'))
        self.assertEqual(parser.get('keys'), ['foo'])
        self.assertEqual(parser.get('level'), 0)
        self.assertEqual(parser.get('operator'), 'and')


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(parseIndexRequestTests))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
