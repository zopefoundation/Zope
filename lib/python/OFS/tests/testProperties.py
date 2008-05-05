##############################################################################
#
# Copyright (c) 2002 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Properties unit tests.

$Id$
"""

import unittest


class TestPropertyManager(unittest.TestCase):
    """Property management tests."""

    def _getTargetClass(self):
        from OFS.PropertyManager import PropertyManager
        return PropertyManager

    def _makeOne(self, *args, **kw):
        return self._getTargetClass()(*args, **kw)

    def test_z3interfaces(self):
        from OFS.interfaces import IPropertyManager
        from OFS.PropertyManager import PropertyManager
        from zope.interface.verify import verifyClass

        verifyClass(IPropertyManager, PropertyManager)

    def testLinesPropertyIsTuple( self ):
        inst = self._makeOne()

        inst._setProperty('prop', ['xxx', 'yyy'], 'lines')
        self.failUnless(type(inst.getProperty('prop')) == type(()))
        self.failUnless(type(inst.prop) == type(()))

        inst._setPropValue('prop', ['xxx', 'yyy'])
        self.failUnless(type(inst.getProperty('prop')) == type(()))
        self.failUnless(type(inst.prop) == type(()))

        inst._updateProperty('prop', ['xxx', 'yyy'])
        self.failUnless(type(inst.getProperty('prop')) == type(()))
        self.failUnless(type(inst.prop) == type(()))

        inst.manage_addProperty('prop2', ['xxx', 'yyy'], 'lines')
        self.failUnless(type(inst.getProperty('prop2')) == type(()))
        self.failUnless(type(inst.prop2) == type(()))

    def test_propertyLabel_no_label_falls_back_to_id(self):
        class NoLabel(self._getTargetClass()):
            _properties = (
                {'id': 'no_label', 'type': 'string'},
            )
        inst = NoLabel()
        self.assertEqual(inst.propertyLabel('no_label'), 'no_label')

    def test_propertyLabel_with_label(self):
        class WithLabel(self._getTargetClass()):
            _properties = (
                {'id': 'with_label', 'type': 'string', 'label': 'With Label'},
            )
        inst = WithLabel()
        self.assertEqual(inst.propertyLabel('with_label'), 'With Label')

    def test_propertyDescription_no_description_falls_back_to_id(self):
        class NoDescription(self._getTargetClass()):
            _properties = (
                {'id': 'no_description', 'type': 'string'},
            )
        inst = NoDescription()
        self.assertEqual(inst.propertyDescription('no_description'), '')

    def test_propertyDescription_with_description(self):
        class WithDescription(self._getTargetClass()):
            _properties = (
                {'id': 'with_description', 'type': 'string',
                 'description': 'With Description'},
            )
        inst = WithDescription()
        self.assertEqual(inst.propertyDescription('with_description'),
                         'With Description')


class TestPropertySheet(unittest.TestCase):
    """Property management tests."""

    def _makeOne(self, *args, **kw):
        from OFS.PropertySheets import PropertySheet

        return PropertySheet(*args, **kw)

    def testPropertySheetLinesPropertyIsTuple(self):
        inst = self._makeOne('foo')

        inst._setProperty('prop', ['xxx', 'yyy'], 'lines')
        self.failUnless(type(inst.getProperty('prop')) == type(()))
        self.failUnless(type(inst.prop) == type(()))

        inst._updateProperty('prop', ['xxx', 'yyy'])
        self.failUnless(type(inst.getProperty('prop')) == type(()))
        self.failUnless(type(inst.prop) == type(()))

        inst.manage_addProperty('prop2', ['xxx', 'yyy'], 'lines')
        self.failUnless(type(inst.getProperty('prop2')) == type(()))
        self.failUnless(type(inst.prop2) == type(()))


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(TestPropertyManager),
        unittest.makeSuite(TestPropertySheet),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
