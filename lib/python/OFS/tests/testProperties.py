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

import os, sys, unittest
from OFS.PropertyManager import PropertyManager
from OFS.PropertySheets import PropertySheet


class TestObject(PropertyManager):
    pass


class TestProperties( unittest.TestCase ):
    """Property management tests."""

    def testLinesPropertyIsTuple( self ):
        inst = TestObject()

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


    def testPropertySheetLinesPropertyIsTuple(self):
        inst = PropertySheet('foo')

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
    suite = unittest.TestSuite()
    suite.addTest( unittest.makeSuite( TestProperties ) )
    return suite

def main():
    unittest.main(defaultTest='test_suite')

if __name__ == '__main__':
    main()
