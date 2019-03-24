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
"""Test AbsoluteURL
"""


def test_absoluteurl():
    """This tests the absolute url view (IAbsoluteURL or @@absolute_url),
    in particular the breadcrumb functionality.

    First we make some preparations:

      >>> import Products.Five
      >>> from Zope2.App import zcml
      >>> zcml.load_config("configure.zcml", Products.Five)
      >>> folder = self.folder  # NOQA: F821

      >>> from Products.Five.tests.testing import (
      ... manage_addFiveTraversableFolder)
      >>> manage_addFiveTraversableFolder(folder, 'testoid', 'Testoid')

    A simple traversal will yield us the @@absolute_url view:

      >>> view = folder.unrestrictedTraverse('testoid/@@absolute_url')
      >>> view()
      'http://nohost/test_folder_1_/testoid'

    IAbsoluteURL also defines a breadcrumbs() method that returns a
    simple Python structure:

      >>> for crumb in view.breadcrumbs():
      ...     info = list(crumb.items())
      ...     info.sort()
      ...     info
      [('name', ''), ('url', 'http://nohost')]
      [('name', 'test_folder_1_'), ('url', 'http://nohost/test_folder_1_')]
      [('name', 'testoid'), ('url', 'http://nohost/test_folder_1_/testoid')]

    This test assures and demonstrates that the absolute url stops
    traversing through an object's parents when it has reached the
    root object.

      >>> from zope.interface import alsoProvides, noLongerProvides
      >>> from OFS.interfaces import IApplication
      >>> alsoProvides(folder, IApplication)

      >>> for crumb in view.breadcrumbs():
      ...     info = list(crumb.items())
      ...     info.sort()
      ...     info
      [('name', 'test_folder_1_'), ('url', 'http://nohost/test_folder_1_')]
      [('name', 'testoid'), ('url', 'http://nohost/test_folder_1_/testoid')]

      >>> noLongerProvides(folder, IApplication)

    The absolute url view is obviously not affected by virtual hosting:

      >>> request = self.app.REQUEST  # NOQA: F821
      >>> request['PARENTS'] = [folder.test_folder_1_]
      >>> url = request.setServerURL(
      ...     protocol='http', hostname='foo.bar.com', port=80)
      >>> request.setVirtualRoot('')

      >>> for crumb in view.breadcrumbs():
      ...     info = list(crumb.items())
      ...     info.sort()
      ...     info
      [('name', 'test_folder_1_'), ('url', 'http://foo.bar.com')]
      [('name', 'testoid'), ('url', 'http://foo.bar.com/testoid')]


    Clean up:

      >>> from zope.component.testing import tearDown
      >>> tearDown()
    """


def test_suite():
    from Testing.ZopeTestCase import ZopeDocTestSuite
    return ZopeDocTestSuite()
