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

$Id$
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
      >>> import Products
      >>> import Products.Five
      >>> from Products.Five import zcml
      >>> zcml.load_config('meta.zcml', Products.Five)

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
      
      >>> app = Zope2.app()
      >>> install_products(app)
      pythonproduct2 initialized
      
    Test to see if the pythonproduct2 python package actually gets setup
    as a zope2 product in the Control Panel.

      >>> product_listing = []
      >>> try:
      ...    product_listing = app.Control_Panel.Products.objectIds()
      ... finally:
      ...     app._p_jar.close()
      >>> 'pythonproduct2' in product_listing
      True

    Make sure it also shows up in ``Products._registered_packages``.

      >>> [x.__name__ for x in getattr(Products, '_registered_packages', [])]
      ['pythonproduct2']

    Clean up:

      >>> tearDown()
    """


def test_suite():
    # Must use functional because registerPackage commits
    from Testing.ZopeTestCase import FunctionalDocTestSuite
    return FunctionalDocTestSuite()
