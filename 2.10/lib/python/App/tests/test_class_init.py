##############################################################################
#
# Copyright (c) 2005 Zope Corporation and Contributors.
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

import ExtensionClass
from App.class_init import default__class_init__ as InitializeClass


def test_InitializeClass():
    """Test that InitializeClass (default__class_init__)
    works in specific corner cases.

    Check when the class has an ExtensionClass as attribute.

    >>> class AnotherClass(ExtensionClass.Base):
    ...     _need__name__ = 1

    >>> class C:
    ...     foo = AnotherClass

    >>> InitializeClass(C)
    """

from zope.testing.doctest import DocTestSuite
import unittest

def test_suite():
    return unittest.TestSuite((
        DocTestSuite(),
        ))

if __name__ == '__main__':
    unittest.main()
