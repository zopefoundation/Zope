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
"""Tests for installPackage
"""

import sys
from unittest import TestSuite

from Testing import ZopeTestCase
from Testing.ZopeTestCase import ZopeLite
from Testing.ZopeTestCase import ZopeDocTestSuite
from Zope2.App import zcml
from zope.testing import cleanup


def testInstallPackage():
    """
    Test if installPackage works.

      >>> from Testing import ZopeTestCase
      >>> from Zope2.App import zcml

    Register testpackage

      >>> ZopeTestCase.hasPackage('testpackage')
      False

      >>> config = '''
      ... <configure
      ...     xmlns:five="http://namespaces.zope.org/five">
      ...   <five:registerPackage
      ...     package="testpackage"
      ...     initialize="testpackage.initialize"
      ...     />
      ... </configure>'''
      >>> zcml.load_string(config)

    The package is registered now

      >>> ZopeTestCase.hasPackage('testpackage')
      True

    Install it

      >>> ZopeTestCase.installPackage('testpackage', quiet=True)
      testpackage.initialize called

    hasPackage still returns True

      >>> ZopeTestCase.hasPackage('testpackage')
      True

    A package is only installed once, subsequent calls to installPackage
    are ignored:

      >>> ZopeTestCase.installPackage('testpackage', quiet=True)
    """


class TestClass(ZopeTestCase.FunctionalTestCase):

    def afterSetUp(self):
        cleanup.cleanUp()
        zcml.load_site(force=True)

        self.saved = sys.path[:]
        sys.path.append(ZopeTestCase.__path__[0])

    def afterClear(self):
        cleanup.cleanUp()
        sys.path[:] = self.saved


def test_suite():
    if ZopeLite.active:
        return TestSuite((
            ZopeDocTestSuite(test_class=TestClass),
        ))
    else:
        return TestSuite()
