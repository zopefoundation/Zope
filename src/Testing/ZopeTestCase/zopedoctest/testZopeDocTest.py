##############################################################################
#
# Copyright (c) 2005 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Example Zope doctest
"""

from unittest import TestSuite
from Testing.ZopeTestCase import ZopeDocTestSuite
from Testing.ZopeTestCase import ZopeDocFileSuite


def setUp(self):
    '''This method will run after the test_class' setUp.

    >>> 'object' in folder.objectIds()
    True

    >>> foo
    1
    '''
    self.folder.manage_addFolder('object', '')
    self.globs['foo'] = 1


def test_suite():
    return TestSuite((
        ZopeDocTestSuite(setUp=setUp),
        ZopeDocFileSuite('ZopeDocTest.txt', setUp=setUp),
    ))

