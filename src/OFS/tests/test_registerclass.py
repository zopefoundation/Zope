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
"""Unit tests for the registerClass directive.
"""

from AccessControl.class_init import InitializeClass
from AccessControl.SecurityInfo import ClassSecurityInfo
from OFS.SimpleItem import SimpleItem
from zope.interface import Interface
from zope.interface import implementer


class ISimpleContent(Interface):
    pass


@implementer(ISimpleContent)
class SimpleContent(SimpleItem):

    meta_type = 'SimpleContent'
    security = ClassSecurityInfo()

    def __init__(self, id, title):
        self.id = id
        self.title = title

    @security.public
    def mymethod(self):
        return "Hello world"

    @security.public
    def direct(self):
        """Should be able to traverse directly to this as there is no view.
        """
        return "Direct traversal worked"


InitializeClass(SimpleContent)


def test_registerClass():
    """
    Testing registerClass

      >>> from zope.component.testing import setUp, tearDown
      >>> setUp()
      >>> import Products
      >>> import Zope2.App
      >>> from Zope2.App import zcml
      >>> from persistent.interfaces import IPersistent

    Use the five:registerClass directive::

      >>> configure_zcml = '''
      ... <configure
      ...     xmlns="http://namespaces.zope.org/zope"
      ...     xmlns:five="http://namespaces.zope.org/five"
      ...     i18n_domain="foo">
      ...   <permission id="foo.add" title="Add Foo"/>
      ...   <five:registerClass
      ...       class="OFS.tests.test_registerclass.SimpleContent"
      ...       meta_type="Foo Type"
      ...       permission="foo.add"
      ...       addview="addfoo.html"
      ...       global="false"
      ...       />
      ... </configure>'''
      >>> zcml.load_config('meta.zcml', Zope2.App)
      >>> zcml.load_string(configure_zcml)

    Make sure that the class attributes are set correctly::

      >>> from OFS.tests.test_registerclass import SimpleContent
      >>> SimpleContent.meta_type
      'Foo Type'

    And the meta_type is registered correctly::

      >>> for info in Products.meta_types:
      ...     if info['name'] == 'Foo Type':
      ...         break
      >>> info['product']
      'OFS'
      >>> info['permission']
      'Add Foo'
      >>> from OFS.tests.test_registerclass import ISimpleContent
      >>> ISimpleContent in info['interfaces']
      True
      >>> IPersistent in info['interfaces']
      True
      >>> info['visibility'] is None
      True
      >>> info['instance'] is SimpleContent
      True
      >>> info['action']
      '+/addfoo.html'
      >>> info['container_filter'] is None
      True

    Now reset everything and see what happens without optional parameters::

      >>> tearDown()
      >>> setUp()

    Use the five:registerClass directive again::

      >>> configure_zcml = '''
      ... <configure
      ...     xmlns="http://namespaces.zope.org/zope"
      ...     xmlns:five="http://namespaces.zope.org/five"
      ...     i18n_domain="bar">
      ...   <permission id="bar.add" title="Add Bar"/>
      ...   <five:registerClass
      ...       class="OFS.tests.test_registerclass.SimpleContent"
      ...       meta_type="Bar Type"
      ...       permission="bar.add"
      ...       />
      ... </configure>'''
      >>> import Zope2.App
      >>> zcml.load_config('meta.zcml', Zope2.App)
      >>> zcml.load_string(configure_zcml)

    Make sure that the class attributes are set correctly::

      >>> SimpleContent.meta_type
      'Bar Type'

    And the meta_type is registered correctly::

      >>> for info in Products.meta_types:
      ...     if info['name'] == 'Bar Type':
      ...         break
      >>> info['product']
      'OFS'
      >>> info['permission']
      'Add Bar'
      >>> ISimpleContent in info['interfaces']
      True
      >>> IPersistent in info['interfaces']
      True
      >>> info['visibility']
      'Global'
      >>> info['instance'] is SimpleContent
      True
      >>> info['action']
      ''
      >>> info['container_filter'] is None
      True

    Clean up:

      >>> tearDown()
      >>> SimpleContent.meta_type
      'simple item'
      >>> [info for info in Products.meta_types if info['name'] == 'Bar Type']
      []
    """


def test_suite():
    from Testing.ZopeTestCase import ZopeDocTestSuite
    return ZopeDocTestSuite()
