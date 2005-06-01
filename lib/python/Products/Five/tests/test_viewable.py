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

$Id: test_viewable.py 12948 2005-05-31 20:24:58Z philikon $
"""
import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

import Products.Five.tests.fivetest   # starts Zope, loads Five, etc.

def test_defaultView():
    """
    Take a class Foo and an interface I1::

      >>> class Foo:
      ...     pass

      >>> from zope.interface import Interface
      >>> class I1(Interface):
      ...     pass

    Set up a default view for I1::

      >>> from zope.app import zapi
      >>> pres = zapi.getGlobalService('Presentation')
      >>> from zope.publisher.interfaces.browser import IBrowserRequest
      >>> pres.setDefaultViewName(I1, IBrowserRequest, 'foo.html')

    and a BrowserDefault for an instance of Foo::

      >>> foo = Foo()
      >>> from Products.Five.viewable import BrowserDefault
      >>> bd = BrowserDefault(foo)

    You'll see that no default view is returned::

      >>> request = self.app.REQUEST
      >>> obj, path = bd.defaultView(request)
      >>> obj is foo
      True
      >>> path is None
      True

    unless you mark the object with I1::

      >>> from zope.interface import directlyProvides
      >>> directlyProvides(foo, I1)
      >>> obj, path = bd.defaultView(request)
      >>> obj is foo
      True
      >>> path
      ['foo.html']

    """

def test_suite():
    from Testing.ZopeTestCase import ZopeDocTestSuite
    return ZopeDocTestSuite()

if __name__ == '__main__':
    framework()
