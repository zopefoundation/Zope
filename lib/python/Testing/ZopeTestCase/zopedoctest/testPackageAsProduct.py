##############################################################################
#
# Copyright (c) 2005 Zope Corporation and Contributors. All Rights Reserved.
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

$Id$
"""

import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from unittest import TestSuite
from Testing.ZopeTestCase import FunctionalDocTestSuite
from Products.Five import zcml
from zope.testing import cleanup


def testInstallPackage():
    """
    Test if installPackage works.

      >>> from Testing import ZopeTestCase
      >>> from Products.Five import zcml
      >>> import sys, Products

    Rig sys.path so testpackage can be imported

      >>> saved = sys.path[:]
      >>> sys.path.append(ZopeTestCase.__path__[0])

    Register testpackage

      >>> config = '''
      ... <configure
      ...     xmlns:five="http://namespaces.zope.org/five">
      ...   <five:registerPackage
      ...     package="testpackage"
      ...     initialize="testpackage.initialize"
      ...     />
      ... </configure>'''

      >>> ZopeTestCase.hasPackage('testpackage')
      False
      >>> zcml.load_string(config)
      >>> ZopeTestCase.hasPackage('testpackage')
      True

    Not yet installed

      >>> app = ZopeTestCase.app()
      >>> 'testpackage' in app.Control_Panel.Products.objectIds()
      False
      >>> ZopeTestCase.close(app)

    Install it

      >>> ZopeTestCase.installPackage('testpackage', quiet=True)
      testpackage.initialize called

    Now it shows up in Control_Panel

      >>> app = ZopeTestCase.app()
      >>> 'testpackage' in app.Control_Panel.Products.objectIds()
      True
      >>> ZopeTestCase.close(app)

    Clean up

      >>> import testpackage
      >>> Products._registered_packages.remove(testpackage)
      >>> sys.path[:] = saved
    """


def setUp(self):
    cleanup.cleanUp()
    zcml._initialized = False
    zcml.load_site()

def tearDown(self):
    cleanup.cleanUp()
    zcml._initialized = False


def test_suite():
    return TestSuite((
        # Must use functional because installPackage commits
        FunctionalDocTestSuite(setUp=setUp, tearDown=tearDown),
    ))

if __name__ == '__main__':
    framework()

