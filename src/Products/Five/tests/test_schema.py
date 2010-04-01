##############################################################################
#
# Copyright (c) 2006 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
""" Unit tests for Products.Five.schema module.

$Id: tests.py 71093 2006-11-07 13:54:29Z yuppie $
"""
import unittest
from zope.testing.cleanup import CleanUp

class Zope2VocabularyRegistryTests(unittest.TestCase, CleanUp):

    def _getTargetClass(self):
        from Products.Five.schema import Zope2VocabularyRegistry
        return Zope2VocabularyRegistry

    def _makeOne(self):
        return self._getTargetClass()()

    def test_class_conforms_to_IVocabularyRegistry(self):
        from zope.interface.verify import verifyClass
        from zope.schema.interfaces import IVocabularyRegistry
        verifyClass(IVocabularyRegistry, self._getTargetClass())

    def test_instance_conforms_to_IVocabularyRegistry(self):
        from zope.interface.verify import verifyObject
        from zope.schema.interfaces import IVocabularyRegistry
        verifyObject(IVocabularyRegistry, self._makeOne())

    def test_get_miss_raises_LookupError(self):
        registry = self._makeOne()
        context = object()
        self.assertRaises(LookupError, registry.get, context, 'nonesuch')

    def test_get_hit_finds_registered_IVocabularyFactory(self):
        from zope.component import provideUtility
        from zope.schema.interfaces import IVocabularyFactory
        _marker = object()
        def _factory(context):
            return _marker
        provideUtility(_factory, IVocabularyFactory, 'foundit')
        registry = self._makeOne()
        context = object()
        found = registry.get(context, 'foundit')
        self.failUnless(found is _marker)

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(Zope2VocabularyRegistryTests),
    ))
