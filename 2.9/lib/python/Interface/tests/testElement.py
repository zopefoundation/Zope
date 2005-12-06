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
from Interface._Element import Element

class ElementTests(unittest.TestCase):

    def test_taggedValues(self):
        """Test that we can update tagged values of more than one element
        """
        
        e1 = Element("foo")
        e2 = Element("bar")
        e1.setTaggedValue("x", 1)
        e2.setTaggedValue("x", 2)
        self.assertEqual(e1.getTaggedValue("x"), 1)
        self.assertEqual(e2.getTaggedValue("x"), 2)
        
def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(ElementTests))
    return suite

def test_suite():
    return unittest.makeSuite(ElementTests)

def main():
    unittest.TextTestRunner().run(test_suite())

if __name__=="__main__":
    main()
