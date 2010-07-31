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
"""Test Five-traversable classes
"""

class SimpleClass(object):
    """Class with no __bobo_traverse__."""


def test_traversable():
    """
    Test the behaviour of Five-traversable classes.

      >>> import Products.Five
      >>> from Zope2.App import zcml
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
      ... <!-- this view will never be found -->
      ... <browser:page
      ...     for="Products.Five.tests.testing.fancycontent.IFancyContent"
      ...     class="Products.Five.browser.tests.pages.FancyView"
      ...     attribute="view"
      ...     name="fancyview"
      ...     permission="zope2.Public"
      ...     />
      ... <!-- these two will -->
      ... <browser:page
      ...     for="Products.Five.tests.testing.fancycontent.IFancyContent"
      ...     class="Products.Five.browser.tests.pages.FancyView"
      ...     attribute="view"
      ...     name="raise-attributeerror"
      ...     permission="zope2.Public"
      ...     />
      ... <browser:page
      ...     for="Products.Five.tests.testing.fancycontent.IFancyContent"
      ...     class="Products.Five.browser.tests.pages.FancyView"
      ...     attribute="view"
      ...     name="raise-keyerror"
      ...     permission="zope2.Public"
      ...     />
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

    Once we have a custom __bobo_traverse__ method, though, it always
    takes over.  Therefore, unless it raises AttributeError or
    KeyError, it will be the only way traversal is done.

      >>> print http(r'''
      ... GET /test_folder_1_/fancy/fancyview HTTP/1.1
      ... ''')
      HTTP/1.1 200 OK
      ...
      fancyview

    As said, if the original __bobo_traverse__ method *does* raise
    AttributeError or KeyError, we can get normal view look-up.  Other
    exceptions are passed through just fine:

      >>> print http(r'''
      ... GET /test_folder_1_/fancy/raise-attributeerror HTTP/1.1
      ... ''')
      HTTP/1.1 200 OK
      ...
      Fancy, fancy

      >>> print http(r'''
      ... GET /test_folder_1_/fancy/raise-keyerror HTTP/1.1
      ... ''')
      HTTP/1.1 200 OK
      ...
      Fancy, fancy

      >>> print http(r'''
      ... GET /test_folder_1_/fancy/raise-valueerror HTTP/1.1
      ... ''', handle_errors=False)
      Traceback (most recent call last):
        ...
      ValueError: ...

    Five's traversable monkeypatches the __bobo_traverse__ method to do view
    lookup and then delegates back to the original __bobo_traverse__ or direct
    attribute/item lookup to do normal lookup.  In the Zope 2 ZPublisher, an 
    object with a __bobo_traverse__ will not do attribute lookup unless the
    __bobo_traverse__ method itself does it (i.e. the __bobo_traverse__ is the
    only element used for traversal lookup).  Let's demonstrate:

      >>> from Products.Five.tests.testing.fancycontent import manage_addNonTraversableFancyContent
      >>> info = manage_addNonTraversableFancyContent(self.folder, 'fancy_zope2', '')
      >>> self.folder.fancy_zope2.an_attribute = 'This is an attribute'
      >>> print http(r'''
      ... GET /test_folder_1_/fancy_zope2/an_attribute HTTP/1.1
      ... ''')
      HTTP/1.1 200 OK
      ...
      an_attribute

    Without a __bobo_traverse__ method this would have returned the attribute
    value 'This is an attribute'.  Let's make sure the same thing happens for
    an object that has been marked traversable by Five:

      >>> self.folder.fancy.an_attribute = 'This is an attribute'
      >>> print http(r'''
      ... GET /test_folder_1_/fancy/an_attribute HTTP/1.1
      ... ''')
      HTTP/1.1 200 OK
      ...
      an_attribute


    Clean up:

      >>> from zope.component.testing import tearDown
      >>> tearDown()

    Verify that after cleanup, there's no cruft left from five:traversable::

      >>> from Products.Five.browser.tests.test_traversable import SimpleClass
      >>> hasattr(SimpleClass, '__bobo_traverse__')
      False
      >>> hasattr(SimpleClass, '__fallback_traverse__')
      False

      >>> from Products.Five.tests.testing.fancycontent import FancyContent
      >>> hasattr(FancyContent, '__bobo_traverse__')
      True
      >>> hasattr(FancyContent.__bobo_traverse__, '__five_method__')
      False
      >>> hasattr(FancyContent, '__fallback_traverse__')
      False
    """

def test_view_doesnt_shadow_attribute():
    """
    Test that views don't shadow attributes, e.g. items in a folder.

    Let's first define a browser page for object managers called
    ``eagle``:

      >>> configure_zcml = '''
      ... <configure xmlns="http://namespaces.zope.org/zope"
      ...            xmlns:meta="http://namespaces.zope.org/meta"
      ...            xmlns:browser="http://namespaces.zope.org/browser"
      ...            xmlns:five="http://namespaces.zope.org/five">
      ...   <!-- make the zope2.Public permission work -->
      ...   <meta:redefinePermission from="zope2.Public" to="zope.Public" />
      ...   <browser:page
      ...       name="eagle"
      ...       for="OFS.interfaces.IObjectManager"
      ...       class="Products.Five.browser.tests.pages.SimpleView"
      ...       attribute="eagle"
      ...       permission="zope2.Public"
      ...       />
      ...   <browser:page
      ...       name="mouse"
      ...       for="OFS.interfaces.IObjectManager"
      ...       class="Products.Five.browser.tests.pages.SimpleView"
      ...       attribute="mouse"
      ...       permission="zope2.Public"
      ...       />
      ... </configure>'''
      >>> import Products.Five
      >>> from Zope2.App import zcml
      >>> zcml.load_config("configure.zcml", Products.Five)
      >>> zcml.load_string(configure_zcml)

    Then we create a traversable folder...

      >>> from Products.Five.tests.testing.folder import manage_addFiveTraversableFolder
      >>> manage_addFiveTraversableFolder(self.folder, 'ftf')

    and add an object called ``eagle`` to it:

      >>> from Products.Five.tests.testing.simplecontent import manage_addIndexSimpleContent
      >>> manage_addIndexSimpleContent(self.folder.ftf, 'eagle', 'Eagle')

    When we publish the ``ftf/eagle`` now, we expect the attribute to
    take precedence over the view during traversal:

      >>> print http(r'''
      ... GET /test_folder_1_/ftf/eagle HTTP/1.1
      ... ''')
      HTTP/1.1 200 OK
      ...
      Default index_html called

    Of course, unless we explicitly want to lookup the view using @@:

      >>> print http(r'''
      ... GET /test_folder_1_/ftf/@@eagle HTTP/1.1
      ... ''')
      HTTP/1.1 200 OK
      ...
      The eagle has landed


    Some weird implementations of __bobo_traverse__, like the one
    found in OFS.Application, raise NotFound.  Five still knows how to
    deal with this, hence views work there too:

      >>> print http(r'''
      ... GET /eagle HTTP/1.1
      ...
      ... ''')
      HTTP/1.1 200 OK
      ...
      The eagle has landed

      >>> print http(r'''
      ... GET /@@eagle HTTP/1.1
      ...
      ... ''')
      HTTP/1.1 200 OK
      ...
      The eagle has landed

    However, acquired attributes *should* be shadowed. See discussion on
    http://codespeak.net/pipermail/z3-five/2006q2/001474.html
    
      >>> manage_addIndexSimpleContent(self.folder, 'mouse', 'Mouse')
      >>> print http(r'''
      ... GET /test_folder_1_/ftf/mouse HTTP/1.1
      ... ''')
      HTTP/1.1 200 OK
      ...
      The mouse has been eaten by the eagle
      
    Clean up:

      >>> from zope.component.testing import tearDown
      >>> tearDown()
    """

def test_suite():
    from Testing.ZopeTestCase import FunctionalDocTestSuite
    return FunctionalDocTestSuite()
