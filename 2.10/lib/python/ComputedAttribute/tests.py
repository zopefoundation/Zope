##############################################################################
#
# Copyright (c) 2003 Zope Corporation and Contributors.
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
"""Computed Attributes

Computed attributes work much like properties:

>>> import math
>>> class Point(Base):
...    def __init__(self, x, y):
...        self.x, self.y = x, y
...    length = ComputedAttribute(lambda self: math.sqrt(self.x**2+self.y**2))

>>> p = Point(3, 4)
>>> "%.1f" % p.length
'5.0'

Except that you can also use computed attributes with instances:

>>> p.angle = ComputedAttribute(lambda self: math.atan(self.y*1.0/self.x))
>>> "%.2f" % p.angle
'0.93'

$Id$
"""

def test_wrapper_support():
    """Wrapper support

    To support acquisition wrappers, computed attributes have a level.
    The computation is only done when the level is zero. Retrieving a
    computed attribute with a level > 0 returns a computed attribute
    with a decremented level.

    >>> class X(Base):
    ...     pass

    >>> x = X()
    >>> x.n = 1
    >>> x.n2 = ComputedAttribute(lambda self: self.n*2)
    >>> x.n2
    2
    >>> x.n2.__class__.__name__
    'int'

    >>> x.n2 = ComputedAttribute(lambda self: self.n*2, 2)
    >>> x.n2.__class__.__name__
    'ComputedAttribute'
    >>> x.n2 = x.n2
    >>> x.n2.__class__.__name__
    'ComputedAttribute'
    >>> x.n2 = x.n2
    >>> x.n2.__class__.__name__
    'int'
    
    """

import unittest
from zope.testing.doctest import DocTestSuite
from ExtensionClass import Base
from ComputedAttribute import ComputedAttribute

def test_suite():
    return unittest.TestSuite((DocTestSuite(),))

if __name__ == '__main__': unittest.main()
