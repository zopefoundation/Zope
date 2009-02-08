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
"""Test forms

$Id$
"""

def test_get_widgets_for_schema_fields():
    """
    Test widget lookup for schema fields

    First, load the configuration files:

      >>> import Products.Five
      >>> from Products.Five import zcml
      >>> zcml.load_config('configure.zcml', Products.Five)

    Now for some actual testing...

      >>> from zope.schema import Choice, TextLine
      >>> salutation = Choice(title=u'Salutation',
      ...                     values=("Mr.", "Mrs.", "Captain", "Don"))
      >>> contactname = TextLine(title=u'Name')

      >>> from zope.publisher.browser import TestRequest
      >>> request = TestRequest()
      >>> salutation = salutation.bind(request)
      >>> contactname = contactname.bind(request)

      >>> from zope.component import getMultiAdapter
      >>> from zope.app.form.interfaces import IInputWidget
      >>> from zope.app.form.browser.textwidgets import TextWidget
      >>> from zope.app.form.browser.itemswidgets import DropdownWidget

      >>> view1 = getMultiAdapter((contactname, request), IInputWidget)
      >>> view1.__class__ == TextWidget
      True

      >>> view2 = getMultiAdapter((salutation, request), IInputWidget)
      >>> view2.__class__ == DropdownWidget
      True

    Clean up:

      >>> from zope.app.testing.placelesssetup import tearDown
      >>> tearDown()
    """

def test_suite():
    import unittest
    from zope.testing.doctest import DocTestSuite
    from Testing.ZopeTestCase import FunctionalDocFileSuite
    return unittest.TestSuite((
            DocTestSuite(),
            FunctionalDocFileSuite('forms.txt',
                                   package="Products.Five.form.tests",),
            ))
