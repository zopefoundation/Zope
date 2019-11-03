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
"""Test the basic ZCML directives
"""


def test_directives():
    """
    Test ZCML directives

    There isn't much to test here since the actual directive handlers are
    either tested in other, more specific tests, or they're already tested in
    the original Zope packages. We'll just do a symbolic test of adapters and
    overrides of adapters here as well as registering meta directives.

    But first, we load the configuration file:

      >>> import Products.Five.tests
      >>> from Zope2.App import zcml
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

      >>> from Products.Five.tests.classes import One, IOne, ITwo
      >>> IOne.implementedBy(One)
      True
      >>> ITwo.implementedBy(One)
      True

    Clean up adapter registry and others:

      >>> from zope.testing.cleanup import cleanUp
      >>> cleanUp()
    """


def test_suite():
    from Testing.ZopeTestCase import ZopeDocTestSuite
    return ZopeDocTestSuite()
