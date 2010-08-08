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
    """Property management tests."""

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

    def testLinesPropertyIsTuple( self ):
        inst = self._makeOne()

        inst._setProperty('prop', ['xxx', 'yyy'], 'lines')
        self.assertTrue(type(inst.getProperty('prop')) == type(()))
        self.assertTrue(type(inst.prop) == type(()))

        inst._setPropValue('prop', ['xxx', 'yyy'])
        self.assertTrue(type(inst.getProperty('prop')) == type(()))
        self.assertTrue(type(inst.prop) == type(()))

        inst._updateProperty('prop', ['xxx', 'yyy'])
        self.assertTrue(type(inst.getProperty('prop')) == type(()))
        self.assertTrue(type(inst.prop) == type(()))

        inst.manage_addProperty('prop2', ['xxx', 'yyy'], 'lines')
        self.assertTrue(type(inst.getProperty('prop2')) == type(()))
        self.assertTrue(type(inst.prop2) == type(()))

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
        self.assertTrue(type(inst.getProperty('prop')) == type(()))
        self.assertTrue(type(inst.prop) == type(()))

        inst._updateProperty('prop', ['xxx', 'yyy'])
        self.assertTrue(type(inst.getProperty('prop')) == type(()))
        self.assertTrue(type(inst.prop) == type(()))

        inst.manage_addProperty('prop2', ['xxx', 'yyy'], 'lines')
        self.assertTrue(type(inst.getProperty('prop2')) == type(()))
        self.assertTrue(type(inst.prop2) == type(()))

    def test_dav__propstat_nullns(self):
        # Tests 15 (propnullns) and 16 (propget) from the props suite
        # of litmus version 10.5 (http://www.webdav.org/neon/litmus/)
        # expose a bug in Zope propertysheet access via DAV.  If a
        # proppatch command sets a property with a null xmlns,
        # e.g. with a PROPPATCH body like:
        #
        # <?xml version="1.0" encoding="utf-8" ?>
        # <propertyupdate xmlns="DAV:">
        # <set>
        # <prop>
        # <nonamespace xmlns="">randomvalue</nonamespace>
        # </prop>
        # </set>
        # </propertyupdate>
        #
        # When we set properties in the null namespace, Zope turns
        # around and creates (or finds) a propertysheet with the
        # xml_namespace of None and sets the value on it.  The
        # response to a subsequent PROPFIND for the resource will fail
        # because the XML generated by dav__propstat included a bogus
        # namespace declaration (xmlns="None").
        #
        inst = self._makeOne('foo')

        inst._md = {'xmlns':None}
        resultd = {}
        inst._setProperty('foo', 'bar')
        inst.dav__propstat('foo', resultd)
        self.assertEqual(len(resultd['200 OK']), 1)
        self.assertEqual(resultd['200 OK'][0], '<foo xmlns="">bar</foo>\n')

    def test_dav__propstat_notnullns(self):
        # see test_dav__propstat_nullns
        inst = self._makeOne('foo')

        inst._md = {'xmlns':'http://www.example.com/props'}
        resultd = {}
        inst._setProperty('foo', 'bar')
        inst.dav__propstat('foo', resultd)
        self.assertEqual(len(resultd['200 OK']), 1)
        self.assertEqual(resultd['200 OK'][0],
                         '<n:foo xmlns:n="http://www.example.com/props">bar'
                         '</n:foo>\n')

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(TestPropertyManager),
        unittest.makeSuite(TestPropertySheet),
        ))
