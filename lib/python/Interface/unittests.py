
#   usage from lib/python:
#
#   python unittest.py Interface.unittests.suite

import unittest
import Interface
from unitfixtures import *  # hehehe

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

    def testClassImplements(self):
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
        self.assertRaises(Interface.BrokenImplementation, a.ma)


    def testInterfaceExtendsInterface(self):
        assert BazInterface.extends(BobInterface)
        assert BazInterface.extends(BarInterface)
        assert BazInterface.extends(FunInterface)
        assert not BobInterface.extends(FunInterface)
        assert not BobInterface.extends(BarInterface)
        assert BarInterface.extends(FunInterface)
        assert not BarInterface.extends(BazInterface)

    def testVerifyImplementation(self):
        assert Interface.verify_class_implementation(FooInterface, Foo)
        assert Interface.verify_class_implementation(Interface.InterfaceInterface, I1)
    

def suite():
    return unittest.makeSuite(InterfaceTests)




