##############################################################################
#
# Copyright (c) 2005 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
""" Unit tests for Z2 -> Z3 bridge utilities.

$Id:$
"""
import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

import unittest

#------------------------------------------------------------------------------
# Running these tests
# ===================
#
# I (Tres) can't figure out your testing framework.  These tests run
# in a "normal" Z27 + Z3 + Five instance home via the following:
#
#   $ bin/zopectl run Products/Five/tests/test_bridge.py
#------------------------------------------------------------------------------

from Interface import Interface as Z2_Interface
from Interface import Attribute as Z2_Attribute

from zope.interface import Interface as Z3_Interface
from zope.interface import Attribute as Z3_Attribute
from zope.interface import Attribute as Z3_Method

class BridgeTests(unittest.TestCase):

    def test_fromZ2Interface_invalid(self):

        from Products.Five.bridge import fromZ2Interface

        self.assertRaises(ValueError, fromZ2Interface, None)
        self.assertRaises(ValueError, fromZ2Interface, object())

        class IZ3_NotAllowed(Z3_Interface):
            pass

        self.assertRaises(ValueError, fromZ2Interface, IZ3_NotAllowed)

    def test_fromZ2Interface_empty(self):

        from Products.Five.bridge import fromZ2Interface

        class IEmpty(Z2_Interface):
            pass

        converted = fromZ2Interface(IEmpty)

        self.failUnless(Z3_Interface.isEqualOrExtendedBy(converted))
        self.assertEqual(len(converted.names()), 0)

    def test_fromZ2Interface_attributes(self):

        from Products.Five.bridge import fromZ2Interface

        class IAttributes(Z2_Interface):
            one = Z2_Attribute('one', 'One attribute')
            another = Z2_Attribute('another', 'Another attribute')

        converted = fromZ2Interface(IAttributes)

        self.failUnless(Z3_Interface.isEqualOrExtendedBy(converted))
        self.assertEqual(len(converted.names()), 2)
        self.failUnless('one' in converted.names())
        self.failUnless('another' in converted.names())

        one = converted.getDescriptionFor('one')
        self.failUnless(isinstance(one, Z3_Attribute))
        self.assertEqual(one.getName(), 'one')
        self.assertEqual(one.getDoc(), 'One attribute')

        another = converted.getDescriptionFor('another')
        self.failUnless(isinstance(another, Z3_Attribute))
        self.assertEqual(another.getName(), 'another')
        self.assertEqual(another.getDoc(), 'Another attribute')

    def test_fromZ2Interface_methods(self):

        from Products.Five.bridge import fromZ2Interface

        class IMethods(Z2_Interface):

            def one():
                """One method."""

            def another(arg1, arg2):
                """Another method, taking arguments."""

        converted = fromZ2Interface(IMethods)

        self.failUnless(Z3_Interface.isEqualOrExtendedBy(converted))
        self.assertEqual(len(converted.names()), 2)
        self.failUnless('one' in converted.names())
        self.failUnless('another' in converted.names())

        one = converted.getDescriptionFor('one')
        self.failUnless(isinstance(one, Z3_Method))
        self.assertEqual(one.getName(), 'one')
        self.assertEqual(one.getDoc(), 'One method.')

        another = converted.getDescriptionFor('another')
        self.failUnless(isinstance(another, Z3_Method))
        self.assertEqual(another.getName(), 'another')
        self.assertEqual(another.getDoc(), 'Another method, taking arguments.')

def test_suite():

    return unittest.defaultTestLoader.loadTestsFromTestCase( BridgeTests )

if __name__ == '__main__':
    framework()
