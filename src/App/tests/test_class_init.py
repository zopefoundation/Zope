##############################################################################
#
# Copyright (c) 2005 Zope Foundation and Contributors.
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
"""Tests class initialization.
"""

import unittest

import ExtensionClass
from AccessControl.class_init import InitializeClass


class TestInitializeClass(unittest.TestCase):

    def test_extension_class(self):
        # Test that InitializeClass works in specific corner cases.
        # Check when the class has an ExtensionClass as attribute.

        class AnotherClass(ExtensionClass.Base):
            _need__name__ = 1

        class C:
            foo = AnotherClass

        InitializeClass(C)
