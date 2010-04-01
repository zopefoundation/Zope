##############################################################################
#
# Copyright (c) 2006 Zope Foundation and Contributors.
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
"""Component tests

$Id$
"""
import unittest
from doctest import DocFileSuite
from Testing.ZopeTestCase import FunctionalDocFileSuite

__docformat__ = "reStructuredText"

def test_suite():
    return unittest.TestSuite([
        DocFileSuite('component.txt', package="Products.Five.component"),
        FunctionalDocFileSuite('makesite.txt',
                               package="Products.Five.component"),
        ])

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
