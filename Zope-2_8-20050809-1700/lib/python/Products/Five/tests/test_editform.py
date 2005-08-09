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
import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

import Products.Five.tests.fivetest   # starts Zope, loads Five, etc.
import unittest
from Testing.ZopeTestCase import ZopeDocTestSuite
from Testing.ZopeTestCase import FunctionalDocFileSuite

def test_get_widgets_for_schema_fields():
    """
    >>> from zope.schema import Choice, TextLine
    >>> salutation = Choice(title=u'Salutation',
    ...                     values=("Mr.", "Mrs.", "Captain", "Don"))
    >>> contactname = TextLine(title=u'Name')
    >>> from Products.Five.traversable import FakeRequest
    >>> request = FakeRequest()
    >>> salutation = salutation.bind(request)
    >>> contactname = contactname.bind(request)

    >>> from zope.app import zapi
    >>> from zope.app.form.interfaces import IInputWidget
    >>> from zope.app.form.browser.textwidgets import TextWidget
    >>> from zope.app.form.browser.itemswidgets import DropdownWidget

    >>> view1 = zapi.getViewProviding(contactname, IInputWidget, request)
    >>> view1.__class__ == TextWidget
    True

    >>> view2 = zapi.getViewProviding(salutation, IInputWidget, request)
    >>> view2.__class__ == DropdownWidget
    True
    """

def setUpForms(self):
    uf = self.folder.acl_users
    uf._doAddUser('viewer', 'secret', [], [])
    uf._doAddUser('manager', 'r00t', ['Manager'], [])

def test_suite():
    return unittest.TestSuite((
            ZopeDocTestSuite(),
            FunctionalDocFileSuite(
		'forms.txt',
		package="Products.Five.tests",
		setUp=setUpForms),
            ))

if __name__ == '__main__':
    framework()
