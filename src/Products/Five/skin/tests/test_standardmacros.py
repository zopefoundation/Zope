##############################################################################
#
# Copyright (c) 2004, 2005 Zope Foundation and Contributors.
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
"""Test standard macros
"""

def test_standard_macros():
    """Test standard macros

      >>> uf = self.folder.acl_users
      >>> _ignored = uf._doAddUser('manager', 'r00t', ['Manager'], [])
      >>> self.login('manager')

      >>> from Products.Five.tests.testing import manage_addFiveTraversableFolder
      >>> manage_addFiveTraversableFolder(self.folder, 'testoid', 'Testoid')

      >>> import Products.Five.skin.tests
      >>> from Zope2.App import zcml
      >>> zcml.load_config('configure.zcml', package=Products.Five)
      >>> zcml.load_config('configure.zcml', package=Products.Five.skin.tests)    

    Test macro access through our flavour of StandardMacros.  First,
    when looking up a non-existing macro, we get a KeyError:

      >>> view = self.folder.unrestrictedTraverse('testoid/@@fivetest_macros')
      >>> view['non-existing-macro']
      Traceback (most recent call last):
      ...
      KeyError: 'non-existing-macro'

    Existing macros are accessible through index notation:

      >>> for macroname in ('birdmacro', 'dogmacro', 'flying', 'walking'):
      ...     view[macroname] is not None
      True
      True
      True
      True

    Aliases are resolve correctly:

      >>> view['flying'] is view['birdmacro']
      True
      >>> view['walking'] is view['dogmacro']
      True

    One can also access the macros through regular traversal:

      >>> base = 'testoid/@@fivetest_macros/%s'
      >>> for macro in ('birdmacro', 'dogmacro', 'flying', 'walking'):
      ...     view = self.folder.unrestrictedTraverse(base % macro)
      ...     view is not None
      True
      True
      True
      True

    Clean up:

      >>> from zope.component.testing import tearDown
      >>> tearDown()
    """

def test_suite():
    from Testing.ZopeTestCase import ZopeDocTestSuite
    return ZopeDocTestSuite()
