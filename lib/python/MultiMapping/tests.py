##############################################################################
#
# Copyright (c) 2003 Zope Corporation and Contributors.
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
"""Multi-mapping tests

>>> from MultiMapping import *

>>> def sortprint(L):
...     L.sort()
...     print L

>>> m=MultiMapping()

>>> m.push({'spam':1, 'eggs':2})

>>> print m['spam']
1
>>> print m['eggs']
2

>>> m.push({'spam':3})

>>> print m['spam']
3
>>> print m['eggs']
2

>>> sortprint(m.pop().items())
[('spam', 3)]

>>> sortprint(m.pop().items())
[('eggs', 2), ('spam', 1)]

>>> try:
...     print m.pop()
...     raise "That\'s odd", "This last pop should have failed!"
... except: # I should probably raise a specific error in this case.
...     pass

$Id$
"""
import unittest
from zope.testing.doctest import DocTestSuite

def test_suite():
    return unittest.TestSuite((
        DocTestSuite(),
        ))

if __name__ == '__main__': unittest.main()
