##############################################################################
#
# Copyright (c) 2006 Zope Foundation and Contributors.
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
"""Unit tests for the registerPackage directive.
"""

import sys

# need to add the testing package to the pythonpath in order to
# test python-packages-as-products
from Products.Five.tests import testing


sys.path.append(testing.__path__[0])


def test_registerPackage():
    """
    Testing registerPackage

      >>> from zope.component.testing import setUp, tearDown
      >>> setUp()
      >>> import Zope2.App
      >>> from Zope2.App import zcml
      >>> zcml.load_config('meta.zcml', Zope2.App)

    Make sure a python package with a valid initialize gets its
    initialize function called::

      >>> configure_zcml = '''
      ... <configure
      ...     xmlns="http://namespaces.zope.org/zope"
      ...     xmlns:five="http://namespaces.zope.org/five"
      ...     i18n_domain="foo">
      ...   <five:registerPackage
      ...       package="pythonproduct2"
      ...       initialize="pythonproduct2.initialize"
      ...       />
      ... </configure>'''
      >>> zcml.load_string(configure_zcml)

    We need to load the product as well. This would normally happen during
    Zope startup, but in the test, we're already too late.

      >>> import Zope2
      >>> from OFS.Application import install_products
      >>> install_products()
      pythonproduct2 initialized

    Make sure it is registered:

      >>> from OFS.metaconfigure import has_package
      >>> has_package('pythonproduct2')
      True

    Clean up:

      >>> tearDown()
    """


def test_suite():
    # Must use functional because registerPackage commits
    from Testing.ZopeTestCase import FunctionalDocTestSuite
    return FunctionalDocTestSuite()
