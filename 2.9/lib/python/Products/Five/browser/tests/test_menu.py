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
"""Test browser menus

$Id: test_menu.py 14595 2005-07-12 21:26:12Z philikon $
"""
import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

def test_menu():
    """
    Test menus

    Before we can start we need to set up a few things.  For menu
    configuration, we have to start a new interaction:

      >>> import Products.Five.browser.tests
      >>> from Products.Five import zcml
      >>> zcml.load_config("meta.zcml", Products.Five)
      >>> zcml.load_config("permissions.zcml", Products.Five)
      >>> zcml.load_config('menu.zcml', package=Products.Five.browser.tests)

      >>> from Products.Five.security import newInteraction
      >>> newInteraction()

    Now for some actual testing... Let's look up the menu we registered:

      >>> from Products.Five.traversable import FakeRequest
      >>> from zope.app.publication.browser import setDefaultSkin
      >>> from zope.app.publisher.browser.menu import getMenu

      >>> request = FakeRequest()
      >>> setDefaultSkin(request)
      >>> menu = getMenu('testmenu', self.folder, request)

    It should have 

      >>> len(menu)
      4

    Sort menu items by title so we get a stable testable result:

      >>> menu.sort(lambda x, y: cmp(x['title'], y['title']))
      >>> from pprint import pprint
      >>> pprint(menu[0])
      {'action': u'@@cockatiel_menu_public.html',
       'description': u'',
       'extra': None,
       'icon': None,
       'selected': u'',
       'submenu': None,
       'title': u'Page in a menu (public)'}

      >>> pprint(menu[1])
      {'action': u'seagull.html',
       'description': u'This is a test menu item',
       'extra': None,
       'icon': None,
       'selected': u'',
       'submenu': None,
       'title': u'Test Menu Item'}

      >>> pprint(menu[2])
      {'action': u'parakeet.html',
       'description': u'This is a test menu item',
       'extra': None,
       'icon': None,
       'selected': u'',
       'submenu': None,
       'title': u'Test Menu Item 2'}

      >>> pprint(menu[3])
      {'action': u'falcon.html',
       'description': u'This is a test menu item',
       'extra': None,
       'icon': None,
       'selected': u'',
       'submenu': None,
       'title': u'Test Menu Item 3'}

    Let's create a manager user account and log in.

      >>> uf = self.folder.acl_users
      >>> uf._doAddUser('manager', 'r00t', ['Manager'], [])
      >>> self.login('manager')
      >>> newInteraction()

      >>> menu = getMenu('testmenu', self.folder, request)

    We should get the protected menu items now:

      >>> len(menu)
      7

      >>> menu.sort(lambda x, y: cmp(x['title'], y['title']))
      >>> pprint(menu[0])
      {'action': u'@@cockatiel_menu_protected.html',
       'description': u'',
       'extra': None,
       'icon': None,
       'selected': u'',
       'submenu': None,
       'title': u'Page in a menu (protected)'}

      >>> pprint(menu[1])
      {'action': u'@@cockatiel_menu_public.html',
       'description': u'',
       'extra': None,
       'icon': None,
       'selected': u'',
       'submenu': None,
       'title': u'Page in a menu (public)'}

      >>> pprint(menu[2])
      {'action': u'seagull.html',
       'description': u'This is a protected test menu item',
       'extra': None,
       'icon': None,
       'selected': u'',
       'submenu': None,
       'title': u'Protected Test Menu Item'}

      >>> pprint(menu[3])
      {'action': u'falcon.html',
       'description': u'This is a protected test menu item',
       'extra': None,
       'icon': None,
       'selected': u'',
       'submenu': None,
       'title': u'Protected Test Menu Item 2'}

      >>> pprint(menu[4])
      {'action': u'seagull.html',
       'description': u'This is a test menu item',
       'extra': None,
       'icon': None,
       'selected': u'',
       'submenu': None,
       'title': u'Test Menu Item'}

      >>> pprint(menu[5])
      {'action': u'parakeet.html',
       'description': u'This is a test menu item',
       'extra': None,
       'icon': None,
       'selected': u'', 
       'submenu': None,
       'title': u'Test Menu Item 2'}

      >>> pprint(menu[6])
      {'action': u'falcon.html',
       'description': u'This is a test menu item',
       'extra': None,
       'icon': None,
       'selected': u'',
       'submenu': None,
       'title': u'Test Menu Item 3'}


    Clean up:

      >>> from zope.app.testing.placelesssetup import tearDown
      >>> tearDown()
    """

def test_suite():
    from Testing.ZopeTestCase import ZopeDocTestSuite
    return ZopeDocTestSuite()

if __name__ == '__main__':
    framework()
