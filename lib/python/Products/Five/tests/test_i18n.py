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
"""Unit tests for the i18n framework

$Id$
"""
import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from zope.component.testing import setUp, tearDown

def test_directive():
    """
    Test the i18n directive.  First, we need to register the ZCML
    directive:

      >>> import zope.i18n
      >>> from Products.Five import zcml
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

      >>> translate(msg)
      u'This is an explicit message'
      >>> translate(msg, target_language='de')
      u'Dies ist eine explizite Nachricht'
    """

def test_FiveTranslationService():
    """
    Test FiveTranslationService. First we need the GlobalTranslationService:

      >>> from Products.PageTemplates import GlobalTranslationService
      >>> GTS = GlobalTranslationService.getGlobalTranslationService()

    Now, take an arbitrary message id from an arbitrary domain:

      >>> from zope.i18nmessageid import MessageFactory
      >>> from zope.i18n import translate
      >>> _ = MessageFactory('random')
      >>> msg = _(u'explicit-msg', u'This is an explicit message')

    By default, the i18n message is translated by the DummyTranslationService:

      >>> GTS.translate('default', msg, target_language='test')
      u'This is an explicit message'

    Now, register the TestMessageFallbackDomain:

      >>> from zope.component import provideUtility
      >>> from zope.i18n.testmessagecatalog import TestMessageFallbackDomain
      >>> provideUtility(TestMessageFallbackDomain)

    The i18n message is now translated by the TestMessageFallbackDomain:

      >>> GTS.translate('default', msg, target_language='test')
      u'[[random][explicit-msg (This is an explicit message)]]'
    """


def test_suite():
    from zope.testing.doctest import DocTestSuite
    return DocTestSuite(setUp=setUp, tearDown=tearDown)

if __name__ == '__main__':
    framework()
