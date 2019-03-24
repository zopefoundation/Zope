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
"""Unit tests for the i18n framework
"""

from zope.component.testing import setUp
from zope.component.testing import tearDown


def test_directive():
    """
    Test the i18n directive.  First, we need to register the ZCML
    directive:

      >>> import zope.i18n
      >>> from Zope2.App import zcml
      >>> zcml.load_config('meta.zcml', zope.i18n)

    Let's register the gettext locales using the ZCML directive:

      >>> configure_zcml = '''
      ... <configure xmlns="http://namespaces.zope.org/zope"
      ...            xmlns:i18n="http://namespaces.zope.org/i18n"
      ...            package="Products.Five.tests">
      ...   <i18n:registerTranslations directory="locales" />
      ... </configure>'''
      >>> zcml.load_string(configure_zcml)

    Now, take an arbitrary message id from that domain:

      >>> from zope.i18nmessageid import MessageFactory
      >>> from zope.i18n import translate
      >>> _ = MessageFactory('fivetest')
      >>> msg = _(u'explicit-msg', u'This is an explicit message')

    As you can see, both the default functionality and translation to
    German work:

      >>> translate(msg) == u'This is an explicit message'
      True
      >>> translate(msg, target_language='de') == u'Dies ist eine explizite Nachricht'  # NOQA: E501
      True
    """


def test_suite():
    from doctest import DocTestSuite
    return DocTestSuite(setUp=setUp, tearDown=tearDown)
