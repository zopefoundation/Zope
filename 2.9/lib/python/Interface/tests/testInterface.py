##############################################################################
#
# Copyright (c) 2001, 2002 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################

import unittest
import Interface
from unitfixtures import *  # hehehe
from Interface.Exceptions import BrokenImplementation
from Interface.Implements import instancesOfObjectImplements
from Interface.Implements import objectImplements
from Interface import Interface
from Interface.Attribute import Attribute

class InterfaceTests(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def testClassImplements(self):
        assert IC.isImplementedByInstancesOf(C)

        assert I1.isImplementedByInstancesOf(A)
        assert I1.isImplementedByInstancesOf(B)
        assert not I1.isImplementedByInstancesOf(C)
        assert I1.isImplementedByInstancesOf(D)
        assert I1.isImplementedByInstancesOf(E)

        assert not I2.isImplementedByInstancesOf(A)
        assert I2.isImplementedByInstancesOf(B)
        assert not I2.isImplementedByInstancesOf(C)
        assert not I2.isImplementedByInstancesOf(D)
        assert not I2.isImplementedByInstancesOf(E)

    def testUtil(self):
        f = instancesOfObjectImplements
        assert IC in f(C)
        assert I1 in f(A)
        assert not I1 in f(C)
        assert I2 in f(B)
        assert not I2 in f(C)

        f = objectImplements
        assert IC in f(C())
        assert I1 in f(A())
        assert not I1 in f(C())
        assert I2 in f(B())
        assert not I2 in f(C())


    def testObjectImplements(self):
        assert IC.isImplementedBy(C())

        assert I1.isImplementedBy(A())
        assert I1.isImplementedBy(B())
        assert not I1.isImplementedBy(C())
        assert I1.isImplementedBy(D())
        assert I1.isImplementedBy(E())

        assert not I2.isImplementedBy(A())
        assert I2.isImplementedBy(B())
        assert not I2.isImplementedBy(C())
        assert not I2.isImplementedBy(D())
        assert not I2.isImplementedBy(E())

    def testDeferredClass(self):
        a = A()
        self.assertRaises(BrokenImplementation, a.ma)


    def testInterfaceExtendsInterface(self):
        assert BazInterface.extends(BobInterface)
        assert BazInterface.extends(BarInterface)
        assert BazInterface.extends(FunInterface)
        assert not BobInterface.extends(FunInterface)
        assert not BobInterface.extends(BarInterface)
        assert BarInterface.extends(FunInterface)
        assert not BarInterface.extends(BazInterface)

    def testVerifyImplementation(self):
        from Interface.Verify import verifyClass
        assert verifyClass(FooInterface, Foo)
        assert Interface.isImplementedBy(I1)

    def test_names(self):
        names = list(_I2.names()); names.sort()
        self.assertEqual(names, ['f21', 'f22', 'f23'])
        names = list(_I2.names(1)); names.sort()
        self.assertEqual(names, ['a1', 'f11', 'f12', 'f21', 'f22', 'f23'])

    def test_namesAndDescriptions(self):
        names = [nd[0] for nd in _I2.namesAndDescriptions()]; names.sort()
        self.assertEqual(names, ['f21', 'f22', 'f23'])
        names = [nd[0] for nd in _I2.namesAndDescriptions(1)]; names.sort()
        self.assertEqual(names, ['a1', 'f11', 'f12', 'f21', 'f22', 'f23'])

        for name, d in _I2.namesAndDescriptions(1):
            self.assertEqual(name, d.__name__)

    def test_getDescriptionFor(self):
        self.assertEqual(_I2.getDescriptionFor('f11').__name__, 'f11')
        self.assertEqual(_I2.getDescriptionFor('f22').__name__, 'f22')
        self.assertEqual(_I2.queryDescriptionFor('f33', self), self)
        self.assertRaises(KeyError, _I2.getDescriptionFor, 'f33')

    def testAttr(self):
        description = _I2.getDescriptionFor('a1')
        self.assertEqual(description.__name__, 'a1')
        self.assertEqual(description.__doc__, 'This is an attribute')


class _I1(Interface):

    a1 = Attribute("This is an attribute")

    def f11(): pass
    def f12(): pass

class __I1(_I1): pass
class ___I1(__I1): pass

class _I2(___I1):
    def f21(): pass
    def f22(): pass
    def f23(): pass

def test_suite():
    return unittest.makeSuite(InterfaceTests)

def main():
    unittest.TextTestRunner().run(test_suite())

if __name__=="__main__":
    main()
