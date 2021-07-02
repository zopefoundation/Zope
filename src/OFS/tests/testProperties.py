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

    def test_updateProperty_transforms(self):
        pm = self._makeOne()
        pm._setProperty('test_lines', [], type='lines')

        pm._updateProperty('test_lines', 'foo\nbar')
        self.assertEqual(pm.getProperty('test_lines'), ('foo', 'bar'))

        pm._updateProperty('test_lines', b'bar\nbaz')
        self.assertEqual(pm.getProperty('test_lines'), ('bar', 'baz'))


class TestPropertySheets(unittest.TestCase):

    def _makePropSheet(self, *args, **kw):
        from OFS.PropertySheets import PropertySheet
        return PropertySheet(*args, **kw)

    def _makeFolder(self):
        from OFS.Folder import Folder
        fldr = Folder('testfolder')
        return fldr

    def test_get(self):
        parent = self._makeFolder()
        pss = parent.propertysheets
        sheet_w_name = self._makePropSheet(id='test1')
        sheet_w_xml = self._makePropSheet(id='foobar',
                                          md={'xmlns': 'test2'})
        parent.__propsets__ += (sheet_w_name, sheet_w_xml)

        self.assertIsNone(pss.get('unknown'))
        self.assertEqual(pss.get('unknown', default='moep'), 'moep')
        self.assertEqual(pss.get('test1').getId(), 'test1')
        self.assertEqual(pss.get('test2').getId(), 'foobar')


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

    def test_updateProperty_transforms(self):
        ps = self._makeOne('foo')
        ps._setProperty('test_lines', [], type='lines')

        ps._updateProperty('test_lines', 'foo\nbar')
        self.assertEqual(ps.getProperty('test_lines'), ('foo', 'bar'))

        ps._updateProperty('test_lines', b'bar\nbaz')
        self.assertEqual(ps.getProperty('test_lines'), ('bar', 'baz'))
