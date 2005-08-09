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
"""

Revision information:
$Id$
"""
from __future__ import nested_scopes


from Interface import Interface
from Interface.Verify import verifyClass, verifyObject
from Interface.Exceptions import DoesNotImplement, BrokenImplementation
from Interface.Exceptions import BrokenMethodImplementation

import unittest, sys

class Test(unittest.TestCase):

    def testNotImplemented(self):

        class C: pass

        class I(Interface): pass

        self.assertRaises(DoesNotImplement, verifyClass, I, C)

        C.__implements__=I

        verifyClass(I, C)

    def testMissingAttr(self):

        class I(Interface):
            def f(): pass

        class C:

            __implements__=I

        self.assertRaises(BrokenImplementation, verifyClass, I, C)

        C.f=lambda self: None

        verifyClass(I, C)

    def testMissingAttr_with_Extended_Interface(self):
       
        class II(Interface):
            def f():
                pass

        class I(II):
            pass

        class C:

            __implements__=I

        self.assertRaises(BrokenImplementation, verifyClass, I, C)

        C.f=lambda self: None

        verifyClass(I, C)

    def testWrongArgs(self):

        class I(Interface):
            def f(a): pass

        class C:

            def f(self, b): pass

            __implements__=I

        # We no longer require names to match.
        #self.assertRaises(BrokenMethodImplementation, verifyClass, I, C)

        C.f=lambda self, a: None

        verifyClass(I, C)

        C.f=lambda self, **kw: None

        self.assertRaises(BrokenMethodImplementation, verifyClass, I, C)

        C.f=lambda self, a, *args: None

        verifyClass(I, C)

        C.f=lambda self, a, *args, **kw: None

        verifyClass(I, C)

        C.f=lambda self, *args: None

        verifyClass(I, C)

    def testExtraArgs(self):

        class I(Interface):
            def f(a): pass

        class C:

            def f(self, a, b): pass

            __implements__=I

        self.assertRaises(BrokenMethodImplementation, verifyClass, I, C)

        C.f=lambda self, a: None

        verifyClass(I, C)

        C.f=lambda self, a, b=None: None

        verifyClass(I, C)

    def testNoVar(self):

        class I(Interface):
            def f(a, *args): pass

        class C:

            def f(self, a): pass

            __implements__=I

        self.assertRaises(BrokenMethodImplementation, verifyClass, I, C)

        C.f=lambda self, a, *foo: None

        verifyClass(I, C)

    def testNoKW(self):

        class I(Interface):
            def f(a, **args): pass

        class C:

            def f(self, a): pass

            __implements__=I

        self.assertRaises(BrokenMethodImplementation, verifyClass, I, C)

        C.f=lambda self, a, **foo: None

        verifyClass(I, C)

    def testModule(self):

        from Interface.tests.IFoo import IFoo
        from Interface.tests import dummy

        verifyObject(IFoo, dummy)



def test_suite():
    loader=unittest.TestLoader()
    return loader.loadTestsFromTestCase(Test)

if __name__=='__main__':
    unittest.TextTestRunner().run(test_suite())
