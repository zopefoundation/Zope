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
"""Test the basic ZCML directives

$Id$
"""
import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

def test_directives():
    """
    Test ZCML directives

    There isn't much to test here since the actual directive handlers
    are either tested in other, more specific tests, or they're
    already tested in Zope 3.  We'll just do a symbolic test of
    adapters and overrides of adapters here as well as registering
    meta directives.

    But first, we load the configuration file:

      >>> import Products.Five.tests
      >>> from Products.Five import zcml
      >>> zcml.load_config('meta.zcml', Products.Five)
      >>> zcml.load_config('directives.zcml', Products.Five.tests)

    Now for some testing.  Here we check whether the registered
    adapter works:

      >>> from Products.Five.tests.adapters import IAdapted, IDestination
      >>> from Products.Five.tests.adapters import Adaptable, Origin

      >>> obj = Adaptable()
      >>> adapted = IAdapted(obj)
      >>> adapted.adaptedMethod()
      'Adapted: The method'

    Now let's load some overriding ZCML statements:

      >>> zcml.load_string(
      ...     '''<includeOverrides
      ...              package="Products.Five.tests"
      ...              file="overrides.zcml" />''')

      >>> origin = Origin()
      >>> dest = IDestination(origin)
      >>> dest.method()
      'Overridden'

    Check the result of the <class> directives

      >>> from Products.Five.tests.classes import One, Two, IOne, ITwo
      >>> IOne.implementedBy(One)
      True
      >>> ITwo.implementedBy(One)
      True

    Clean up adapter registry and others:

      >>> from zope.testing.cleanup import cleanUp
      >>> cleanUp()
    """

def test_content_deprecation():
    """
    Test deprecated content directive

    There was a bug in the content directive deprecation code
    which caused all code that use this directive break.
    So we test this to make sure it works. If the content
    directive will have been removed, this test can be removed
    entirely as well.

    First, we load the configuration file:

      >>> import Products.Five.tests
      >>> from Products.Five import zcml
      >>> zcml.load_config('meta.zcml', Products.Five)
      >>> zcml.load_config('directives.zcml', Products.Five.tests)

    Use the <content> directives: this gives a deprecation
    warning but should otherwise be all right. (We embed the block
    to suppress the deprecation warning...)

      >>> import warnings
      >>> warnings.showwarning, _savewarning = lambda *args, **kw: None, warnings.showwarning
      >>> zcml.load_string('''
      ...   <configure xmlns="http://namespaces.zope.org/zope">
      ...      <content class="Products.Five.tests.classes.One">
      ...          <implements interface="Products.Five.tests.classes.IOne" />
      ...      </content>
      ...   </configure>
      ...   ''')

    Check that they are all right.

      >>> from Products.Five.tests.classes import One, Two, IOne, ITwo
      >>> IOne.implementedBy(One)
      True

    Clean up adapter registry and others:

      >>> warnings.showwarning  = _savewarning
      >>> from zope.testing.cleanup import cleanUp
      >>> cleanUp()
    """


def test_suite():
    from Testing.ZopeTestCase import ZopeDocTestSuite
    return ZopeDocTestSuite()

if __name__ == '__main__':
    framework()
