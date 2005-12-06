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
"""Test Five-traversable classes

$Id: test_traversable.py 17580 2005-09-15 16:05:47Z philikon $
"""
import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

def test_traversable():
    """
    Test the behaviour of Five-traversable classes.

      >>> import Products.Five
      >>> from Products.Five import zcml
      >>> zcml.load_config("configure.zcml", Products.Five)

    ``SimpleContent`` is a traversable class by default.  Its fallback
    traverser should raise NotFound when traversal fails.  (Note: If
    we return None in __fallback_traverse__, this test passes but for
    the wrong reason: None doesn't have a docstring so BaseRequest
    raises NotFoundError.)

      >>> from Products.Five.tests.testing.simplecontent import manage_addSimpleContent
      >>> manage_addSimpleContent(self.folder, 'testoid', 'Testoid')
      >>> print http(r'''
      ... GET /test_folder_1_/testoid/doesntexist HTTP/1.1
      ... ''')
      HTTP/1.1 404 Not Found
      ...

    Now let's take class which already has a __bobo_traverse__ method.
    Five should correctly use that as a fallback.

      >>> configure_zcml = '''
      ... <configure xmlns="http://namespaces.zope.org/zope"
      ...            xmlns:meta="http://namespaces.zope.org/meta"
      ...            xmlns:browser="http://namespaces.zope.org/browser"
      ...            xmlns:five="http://namespaces.zope.org/five">
      ... 
      ... <!-- make the zope2.Public permission work -->
      ... <meta:redefinePermission from="zope2.Public" to="zope.Public" />
      ... 
      ... <five:traversable
      ...     class="Products.Five.tests.testing.fancycontent.FancyContent"
      ...     />
      ... 
      ... <browser:page
      ...     for="Products.Five.tests.testing.fancycontent.IFancyContent"
      ...     class="Products.Five.browser.tests.pages.FancyView"
      ...     attribute="view"
      ...     name="fancyview"
      ...     permission="zope2.Public"
      ...     />
      ... 
      ... </configure>'''
      >>> zcml.load_string(configure_zcml)

      >>> from Products.Five.tests.testing.fancycontent import manage_addFancyContent
      >>> info = manage_addFancyContent(self.folder, 'fancy', '')

    In the following test we let the original __bobo_traverse__ method
    kick in:

      >>> print http(r'''
      ... GET /test_folder_1_/fancy/something-else HTTP/1.1
      ... ''')
      HTTP/1.1 200 OK
      ...
      something-else

    Of course we also need to make sure that Zope 3 style view lookup
    actually works:

      >>> print http(r'''
      ... GET /test_folder_1_/fancy/fancyview HTTP/1.1
      ... ''')
      HTTP/1.1 200 OK
      ...
      Fancy, fancy


    Clean up:

      >>> from zope.app.testing.placelesssetup import tearDown
      >>> tearDown()
    """

def test_suite():
    from Testing.ZopeTestCase import FunctionalDocTestSuite
    return FunctionalDocTestSuite()

if __name__ == '__main__':
    framework()
