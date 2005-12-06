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
"""Test AbsoluteURL

$Id: test_absoluteurl.py 14595 2005-07-12 21:26:12Z philikon $
"""
import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

def test_absoluteurl():
    """This tests the absolute url view (IAbsoluteURL or @@absolute_url),
    in particular the breadcrumb functionality.

    First we make some preparations:

      >>> import Products.Five
      >>> from Products.Five import zcml
      >>> zcml.load_config("configure.zcml", Products.Five)

      >>> from Products.Five.tests.testing import manage_addFiveTraversableFolder
      >>> manage_addFiveTraversableFolder(self.folder, 'testoid', 'Testoid')

    A simple traversal will yield us the @@absolute_url view:

      >>> view = self.folder.unrestrictedTraverse('testoid/@@absolute_url')
      >>> view()
      'http://nohost/test_folder_1_/testoid'

    IAbsoluteURL also defines a breadcrumbs() method that returns a
    simple Python structure:

      >>> for crumb in view.breadcrumbs():
      ...     info = crumb.items()
      ...     info.sort()
      ...     info
      [('name', ''), ('url', 'http://nohost')]
      [('name', 'test_folder_1_'), ('url', 'http://nohost/test_folder_1_')]
      [('name', 'testoid'), ('url', 'http://nohost/test_folder_1_/testoid')]

    This test assures and demonstrates that the absolute url stops
    traversing through an object's parents when it has reached the
    root object.  In Zope 3 this is marked with the IContainmentRoot
    interface:

      >>> from zope.interface import directlyProvides, providedBy
      >>> from zope.app.traversing.interfaces import IContainmentRoot
      >>> directlyProvides(self.folder, IContainmentRoot)

      >>> for crumb in view.breadcrumbs():
      ...     info = crumb.items()
      ...     info.sort()
      ...     info
      [('name', 'test_folder_1_'), ('url', 'http://nohost/test_folder_1_')]
      [('name', 'testoid'), ('url', 'http://nohost/test_folder_1_/testoid')]

      >>> directlyProvides(self.folder,
      ...                  providedBy(self.folder) - IContainmentRoot)

    The absolute url view is obviously not affected by virtual hosting:

      >>> request = self.app.REQUEST
      >>> request['PARENTS'] = [self.folder.test_folder_1_]
      >>> url = request.setServerURL(
      ...     protocol='http', hostname='foo.bar.com', port='80')
      >>> request.setVirtualRoot('')

      >>> for crumb in view.breadcrumbs():
      ...     info = crumb.items()
      ...     info.sort()
      ...     info
      [('name', 'test_folder_1_'), ('url', 'http://foo.bar.com')]
      [('name', 'testoid'), ('url', 'http://foo.bar.com/testoid')]


    Clean up:

      >>> from zope.app.testing.placelesssetup import tearDown
      >>> tearDown()
    """

def test_suite():
    from Testing.ZopeTestCase import ZopeDocTestSuite
    return ZopeDocTestSuite()

if __name__ == '__main__':
    framework()
