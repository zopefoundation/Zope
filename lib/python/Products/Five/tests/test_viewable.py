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
"""Unit tests for the viewable module.

$Id: test_viewable.py 14595 2005-07-12 21:26:12Z philikon $
"""
import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

def test_defaultView():
    """
    Testing default view functionality

    Take a class Foo and an interface IFoo:

      >>> class Foo:
      ...     pass

      >>> from zope.interface import Interface
      >>> class IFoo(Interface):
      ...     pass

    Set up a default view for IFoo:

      >>> from zope.component import provideAdapter
      >>> from zope.component.interfaces import IDefaultViewName
      >>> from zope.publisher.interfaces.browser import IBrowserRequest

    and default view names for everything and IFoo objects in particular:

      >>> provideAdapter(u'index.html', (None, IBrowserRequest), IDefaultViewName)
      >>> provideAdapter(u'foo.html', (IFoo, IBrowserRequest), IDefaultViewName)

    Now take a BrowserDefault for an instance of Foo::

      >>> foo = Foo()
      >>> from Products.Five.viewable import BrowserDefault
      >>> bd = BrowserDefault(foo)

    For now the default view name is index.html, like we set above:

      >>> from Products.Five.traversable import FakeRequest
      >>> request = FakeRequest()

      >>> obj, path = bd.defaultView(request)
      >>> obj is foo
      True
      >>> path
      [u'index.html']

    until we mark the object with IFoo:

      >>> from zope.interface import directlyProvides
      >>> directlyProvides(foo, IFoo)
      >>> obj, path = bd.defaultView(request)
      >>> obj is foo
      True
      >>> path
      [u'foo.html']

    Clean up adapter registry:

      >>> from zope.testing.cleanup import cleanUp
      >>> cleanUp()
    """

def test_suite():
    from Testing.ZopeTestCase import ZopeDocTestSuite
    return ZopeDocTestSuite()

if __name__ == '__main__':
    framework()
