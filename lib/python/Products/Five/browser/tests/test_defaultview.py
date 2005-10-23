##############################################################################
#
# Copyright (c) 2004, 2005 Zope Corporation and Contributors.
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
"""Test Default View functionality

$Id: test_defaultview.py 14595 2005-07-12 21:26:12Z philikon $
"""
import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

def test_default_view():
    """
    Test default view functionality

    Let's register a couple of default views and make our stub classes
    default viewable:

      >>> import Products.Five.browser.tests
      >>> from Products.Five import zcml
      >>> zcml.load_config("configure.zcml", Products.Five)
      >>> zcml.load_config('defaultview.zcml', Products.Five.browser.tests)

    Now let's add a couple of stub objects:

      >>> from Products.Five.testing.simplecontent import manage_addSimpleContent
      >>> from Products.Five.testing.simplecontent import manage_addCallableSimpleContent
      >>> from Products.Five.testing.simplecontent import manage_addIndexSimpleContent

      >>> manage_addSimpleContent(self.folder, 'testoid', 'Testoid')
      >>> manage_addCallableSimpleContent(self.folder, 'testcall', 'TestCall')
      >>> manage_addIndexSimpleContent(self.folder, 'testindex', 'TestIndex')

    As a last act of preparation, we create a manager login:

      >>> uf = self.folder.acl_users
      >>> uf._doAddUser('manager', 'r00t', ['Manager'], [])

    Test a simple default view:

      >>> print http(r'''
      ... GET /test_folder_1_/testoid HTTP/1.1
      ... Authorization: Basic manager:r00t
      ... ''')
      HTTP/1.1 200 OK
      ...
      The eagle has landed

    This tests whether an existing ``index_html`` method is still
    supported and called:

      >>> print http(r'''
      ... GET /test_folder_1_/testindex HTTP/1.1
      ... ''')
      HTTP/1.1 200 OK
      ...
      Default index_html called

    Disabled __call__ overriding for now.  Causese more trouble than it
    fixes.  Thus, no test here:

      #>>> print http(r'''
      #... GET /test_folder_1_/testcall HTTP/1.1
      #... ''')
      #HTTP/1.1 200 OK
      #...
      #Default __call__ called


    Clean up:

      >>> from zope.app.tests.placelesssetup import tearDown
      >>> tearDown()
    """

def test_suite():
    from Testing.ZopeTestCase import FunctionalDocTestSuite
    return FunctionalDocTestSuite()

if __name__ == '__main__':
    framework()
