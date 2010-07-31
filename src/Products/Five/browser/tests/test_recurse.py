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
"""Test default view recursion
"""

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

    Now we register a default view name for the class:

      >>> from zope.component import provideAdapter
      >>> from zope.publisher.interfaces.browser import IBrowserRequest
      >>> from zope.publisher.interfaces import IDefaultViewName
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
