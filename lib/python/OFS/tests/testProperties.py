##############################################################################
#
# Copyright (c) 2001, 2002 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################

import unittest


class TestPropertyManager(unittest.TestCase):
    """Property management tests."""

    def _makeOne(self, *args, **kw):
        from OFS.PropertyManager import PropertyManager

        return PropertyManager(*args, **kw)

    def test_z3interfaces(self):
        from OFS.interfaces import IPropertyManager
        from OFS.PropertyManager import PropertyManager
        from zope.interface.verify import verifyClass

        verifyClass(IPropertyManager, PropertyManager, 1)

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
