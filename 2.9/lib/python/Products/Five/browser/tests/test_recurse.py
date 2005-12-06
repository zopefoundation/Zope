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
"""Test default view recursion

$Id: test_recurse.py 14595 2005-07-12 21:26:12Z philikon $
"""
import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

def test_recursion():
    """
    Test recursion

    This test makes sure that recursion is avoided for view lookup.
    First, we need to set up a stub interface...

      >>> from zope.interface import Interface, implements
      >>> class IRecurse(Interface):
      ...     pass
      ...

    and a class that is callable and has a view method:

      >>> from OFS.Traversable import Traversable
      >>> class Recurse(Traversable):
      ...     implements(IRecurse)
      ...     def view(self):
      ...         return self()
      ...     def __call__(self):
      ...         return 'foo'
      ...

    Now we make the class default viewable and register a default view
    name for it:

      >>> from Products.Five.fiveconfigure import classDefaultViewable
      >>> classDefaultViewable(Recurse)

      >>> from zope.component import provideAdapter
      >>> from zope.publisher.interfaces.browser import IBrowserRequest
      >>> from zope.component.interfaces import IDefaultViewName
      >>> provideAdapter(u'view', (IRecurse, IBrowserRequest), IDefaultViewName)

    Here comes the actual test:

      >>> ob = Recurse()
      >>> ob.view()
      'foo'
      >>> ob()
      'foo'


    Clean up adapter registry and monkey patches to classes:

      >>> from zope.testing.cleanup import cleanUp
      >>> cleanUp()
    """

def test_suite():
    from Testing.ZopeTestCase import ZopeDocTestSuite
    return ZopeDocTestSuite()

if __name__ == '__main__':
    framework()
