##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
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
"""

import unittest


class TestPropertyManager(unittest.TestCase):

    def _getTargetClass(self):
        from OFS.PropertyManager import PropertyManager
        return PropertyManager

    def _makeOne(self, *args, **kw):
        return self._getTargetClass()(*args, **kw)

    def test_interfaces(self):
        from OFS.interfaces import IPropertyManager
        from OFS.PropertyManager import PropertyManager
        from zope.interface.verify import verifyClass

        verifyClass(IPropertyManager, PropertyManager)

    def testLinesPropertyIsTuple(self):
        inst = self._makeOne()

        inst._setProperty('prop', ['xxx', 'yyy'], 'lines')
        self.assertIsInstance(inst.getProperty('prop'), tuple)
        self.assertIsInstance(inst.prop, tuple)

        inst._setPropValue('prop', ['xxx', 'yyy'])
        self.assertIsInstance(inst.getProperty('prop'), tuple)
        self.assertIsInstance(inst.prop, tuple)

        inst._updateProperty('prop', ['xxx', 'yyy'])
        self.assertIsInstance(inst.getProperty('prop'), tuple)
        self.assertIsInstance(inst.prop, tuple)

        inst.manage_addProperty('prop2', ['xxx', 'yyy'], 'lines')
        self.assertIsInstance(inst.getProperty('prop2'), tuple)
        self.assertIsInstance(inst.prop2, tuple)

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

    def _makeOne(self, *args, **kw):
        from OFS.PropertySheets import PropertySheet
        return PropertySheet(*args, **kw)

    def testPropertySheetLinesPropertyIsTuple(self):
        inst = self._makeOne('foo')

        inst._setProperty('prop', ['xxx', 'yyy'], 'lines')
        self.assertIsInstance(inst.getProperty('prop'), tuple)
        self.assertIsInstance(inst.prop, tuple)

        inst._updateProperty('prop', ['xxx', 'yyy'])
        self.assertIsInstance(inst.getProperty('prop'), tuple)
        self.assertIsInstance(inst.prop, tuple)

        inst.manage_addProperty('prop2', ['xxx', 'yyy'], 'lines')
        self.assertIsInstance(inst.getProperty('prop2'), tuple)
        self.assertIsInstance(inst.prop2, tuple)
