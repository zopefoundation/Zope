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
"""XXX short summary goes here.

$Id$
"""
import unittest
from zope.testing.doctest import DocTestSuite

def test_xxx():
    """
    >>> from ExtensionClass import Base
    >>> from MethodObject import Method

    >>> class foo(Method):
    ...     def __call__(self, ob, *args, **kw):
    ...         print 'called', ob, args, kw

    >>> class bar(Base):
    ...     def __repr__(self):
    ...         return "bar()"
    ...     hi = foo()

    >>> x = bar()
    >>> hi = x.hi
    >>> hi(1,2,3,name='spam')
    called bar() (1, 2, 3) {'name': 'spam'}
    
    """

def test_suite():
    return unittest.TestSuite((
        DocTestSuite(),
        ))

if __name__ == '__main__': unittest.main()
