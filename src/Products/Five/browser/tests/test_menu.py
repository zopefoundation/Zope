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
"""Test browser menus
"""


def test_menu():
    """
    Test menus

    Before we can start we need to set up a few things.  For menu
    configuration, we have to start a new interaction:

      >>> import AccessControl
      >>> import Products.Five.browser.tests
      >>> from Zope2.App import zcml
      >>> zcml.load_config("meta.zcml", Products.Five)
      >>> zcml.load_config("permissions.zcml", AccessControl)
      >>> zcml.load_config('menu.zcml', package=Products.Five.browser.tests)

      >>> from AccessControl.security import newInteraction
      >>> newInteraction()

    Now for some actual testing... Let's look up the menu we registered:

      >>> from zope.publisher.browser import TestRequest
      >>> from zope.browsermenu.menu import getMenu

      >>> request = TestRequest()
      >>> folder = self.folder  # NOQA: F821
      >>> menu = getMenu('testmenu', folder, request)

    It should have

      >>> len(menu)
      4

    Sort menu items by title so we get a stable testable result:

      >>> from operator import itemgetter
      >>> menu.sort(key=itemgetter('title'))
      >>> menu[0] == {
      ...     'action': '@@cockatiel_menu_public.html',
      ...     'description': u'',
      ...     'extra': None,
      ...     'icon': None,
      ...     'selected': u'',
      ...     'submenu': None,
      ...     'title': u'Page in a menu (public)'}
      True

      >>> menu[1] == {
      ...     'action': u'seagull.html',
      ...     'description': u'This is a test menu item',
      ...     'extra': None,
      ...     'icon': None,
      ...     'selected': u'',
      ...     'submenu': None,
      ...     'title': u'Test Menu Item'}
      True

      >>> menu[2] == {
      ...     'action': u'parakeet.html',
      ...     'description': u'This is a test menu item',
      ...     'extra': None,
      ...     'icon': None,
      ...     'selected': u'',
      ...     'submenu': None,
      ...     'title': u'Test Menu Item 2'}
      True

      >>> menu[3] == {
      ...     'action': u'falcon.html',
      ...     'description': u'This is a test menu item',
      ...     'extra': None,
      ...     'icon': None,
      ...     'selected': u'',
      ...     'submenu': None,
      ...     'title': u'Test Menu Item 3'}
      True

    Let's create a manager user account and log in.

      >>> uf = folder.acl_users
      >>> _ignored = uf._doAddUser('manager', 'r00t', ['Manager'], [])
      >>> self.login('manager')  # NOQA: F821
      >>> newInteraction()

      >>> menu = getMenu('testmenu', folder, request)

    We should get the protected menu items now:

      >>> len(menu)
      7

      >>> menu.sort(key=itemgetter('title'))
      >>> menu[0] == {
      ...     'action': '@@cockatiel_menu_protected.html',
      ...     'description': u'',
      ...     'extra': None,
      ...     'icon': None,
      ...     'selected': u'',
      ...     'submenu': None,
      ...     'title': u'Page in a menu (protected)'}
      True

      >>> menu[1] == {
      ...     'action': '@@cockatiel_menu_public.html',
      ...     'description': u'',
      ...     'extra': None,
      ...     'icon': None,
      ...     'selected': u'',
      ...     'submenu': None,
      ...     'title': u'Page in a menu (public)'}
      True

      >>> menu[2] == {
      ...     'action': u'seagull.html',
      ...     'description': u'This is a protected test menu item',
      ...     'extra': None,
      ...     'icon': None,
      ...     'selected': u'',
      ...     'submenu': None,
      ...     'title': u'Protected Test Menu Item'}
      True

      >>> menu[3] == {
      ...     'action': u'falcon.html',
      ...     'description': u'This is a protected test menu item',
      ...     'extra': None,
      ...     'icon': None,
      ...     'selected': u'',
      ...     'submenu': None,
      ...     'title': u'Protected Test Menu Item 2'}
      True

      >>> menu[4] == {
      ...     'action': u'seagull.html',
      ...     'description': u'This is a test menu item',
      ...     'extra': None,
      ...     'icon': None,
      ...     'selected': u'',
      ...     'submenu': None,
      ...     'title': u'Test Menu Item'}
      True

      >>> menu[5] == {
      ...     'action': u'parakeet.html',
      ...     'description': u'This is a test menu item',
      ...     'extra': None,
      ...     'icon': None,
      ...     'selected': u'',
      ...     'submenu': None,
      ...     'title': u'Test Menu Item 2'}
      True

      >>> menu[6] == {
      ...     'action': u'falcon.html',
      ...     'description': u'This is a test menu item',
      ...     'extra': None,
      ...     'icon': None,
      ...     'selected': u'',
      ...     'submenu': None,
      ...     'title': u'Test Menu Item 3'}
      True


    Clean up:

      >>> from zope.component.testing import tearDown
      >>> tearDown()
    """


def test_suite():
    from Testing.ZopeTestCase import ZopeDocTestSuite
    return ZopeDocTestSuite()
