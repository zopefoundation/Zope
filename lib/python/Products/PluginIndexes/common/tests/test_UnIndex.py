##############################################################################
#
# Copyright (c) 2002 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
#############################################################################
""" Tests for common UnIndex features.

$Id$
"""
import unittest

class UnIndexTests(unittest.TestCase):

    def _getTargetClass(self):
        from Products.PluginIndexes.common.UnIndex import UnIndex
        return UnIndex

    def _makeOne(self, *args, **kw):
        return self._getTargetClass()(*args, **kw)

    def _makeConflicted(self):
        from ZODB.POSException import ConflictError
        class Conflicted:
            def __str__(self):
                return 'Conflicted'
            __repr__ = __str__
            def __getattr__(self, id, default=object()):
                raise ConflictError, 'testing'
        return Conflicted()

    def test_empty(self):
        unindex = self._makeOne(id='empty')
        self.assertEqual(unindex.indexed_attrs, ['empty'])

    def test_removeForwardIndexEntry_with_ConflictError(self):
        from ZODB.POSException import ConflictError
        unindex = self._makeOne(id='conflicted')
        unindex._index['conflicts'] = self._makeConflicted()
        self.assertRaises(ConflictError, unindex.removeForwardIndexEntry,
                          'conflicts', 42)

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(UnIndexTests))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
