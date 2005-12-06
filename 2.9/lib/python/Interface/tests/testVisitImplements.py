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
import unittest, sys

from Interface.Implements import visitImplements
from Interface import Interface
from Interface.Exceptions import BadImplements

class I1(Interface): pass
class I2(Interface): pass
class I3(Interface): pass

class Test(unittest.TestCase):

    def testSimpleImplements(self):
        data=[]
        visitImplements(I1, None, data.append)
        self.assertEqual(data, [I1])

    def testSimpleBadImplements(self):
        data=[]
        self.assertRaises(BadImplements,
                          visitImplements, unittest, None, data.append)

    def testComplexImplements(self):
        data=[]
        visitImplements((I1, (I2, I3)), None, data.append)
        data = map(lambda i: i.__name__, data)
        self.assertEqual(data, ['I1', 'I2', 'I3'])

    def testComplexBadImplements(self):
        data=[]
        self.assertRaises(BadImplements,
                          visitImplements, (I1, (I2, unittest)),
                          None, data.append)


def test_suite():
    loader=unittest.TestLoader()
    return loader.loadTestsFromTestCase(Test)

if __name__=='__main__':
    unittest.TextTestRunner().run(test_suite())
