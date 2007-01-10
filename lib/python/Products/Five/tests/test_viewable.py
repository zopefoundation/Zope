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

$Id$
"""
import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

def test_defaultView():
    """
    This tests the default view functionality. It also tests the deprecated 
    BrowserDefault class. References to BrowserDefault can be removed in 2.12.

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

      >>> from Products.Five.bbb import BrowserDefault, IBrowserDefault
      >>> from zope.interface import Interface
      >>> provideAdapter(BrowserDefault, (Interface,), IBrowserDefault)
      >>> provideAdapter(u'index.html', (None, IBrowserRequest), IDefaultViewName)
      >>> provideAdapter(u'foo.html', (IFoo, IBrowserRequest), IDefaultViewName)

    Now take a BrowserDefault for an instance of Foo::

      >>> foo = Foo()
      >>> bd = BrowserDefault(foo)

    For now the default view name is index.html, like we set above:

      >>> from zope.publisher.browser import TestRequest
      >>> request = TestRequest()
      >>> from zope.app.publisher.browser import queryDefaultViewName

      >>> queryDefaultViewName(foo, request)
      u'index.html'
      >>> obj, path = bd.defaultView(request)
      >>> obj is foo
      True
      >>> path
      [u'index.html']

    until we mark the object with IFoo:

      >>> from zope.interface import directlyProvides
      >>> directlyProvides(foo, IFoo)
      >>> queryDefaultViewName(foo, request)
      u'foo.html'
      
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
    import unittest
    from zope.testing.doctest import DocTestSuite
    from Testing.ZopeTestCase import FunctionalDocFileSuite
    return unittest.TestSuite((
            DocTestSuite(),
            FunctionalDocFileSuite('viewable.txt',
                                   package="Products.Five.tests",),
            ))

if __name__ == '__main__':
    framework()
