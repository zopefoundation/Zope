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
"""Test browser pages

$Id: test_pages.py 18840 2005-10-23 09:47:10Z philikon $
"""
import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

def test_ViewAcquisitionWrapping():
    """
      >>> import Products.Five.browser.tests
      >>> from Products.Five import zcml
      >>> zcml.load_config("configure.zcml", Products.Five)
      >>> zcml.load_config('pages.zcml', package=Products.Five.browser.tests)

      >>> from Products.Five.tests.testing.simplecontent import manage_addSimpleContent
      >>> manage_addSimpleContent(self.folder, 'testoid', 'Testoid')
      >>> uf = self.folder.acl_users
      >>> uf._doAddUser('manager', 'r00t', ['Manager'], [])
      >>> self.login('manager')

      >>> view = self.folder.unrestrictedTraverse('testoid/eagle.txt')
      >>> view is not None
      True
      >>> from Products.Five.browser.tests.pages import SimpleView
      >>> isinstance(view, SimpleView)
      True
      >>> view()
      'The eagle has landed'

    This sucks, but we know it

      >>> from Acquisition import aq_parent, aq_base
      >>> aq_parent(view.context) is view
      True

    This is the right way to get the context parent

      >>> view.context.aq_inner.aq_parent is not view
      True
      >>> view.context.aq_inner.aq_parent is self.folder
      True

    Clean up:

      >>> from zope.app.testing.placelesssetup import tearDown
      >>> tearDown()
    """

def test_suite():
    import unittest
    from Testing.ZopeTestCase import installProduct, ZopeDocTestSuite
    from Testing.ZopeTestCase import ZopeDocFileSuite
    from Testing.ZopeTestCase import FunctionalDocFileSuite
    installProduct('PythonScripts')  # for Five.tests.testing.restricted
    return unittest.TestSuite((
        ZopeDocTestSuite(),
        ZopeDocFileSuite('pages.txt', package='Products.Five.browser.tests'),
        FunctionalDocFileSuite('pages_ftest.txt',
                               package='Products.Five.browser.tests')
        ))
    return suite

if __name__ == '__main__':
    framework()
