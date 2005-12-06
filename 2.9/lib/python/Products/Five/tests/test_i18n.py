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

$Id: test_i18n.py 14595 2005-07-12 21:26:12Z philikon $
"""
import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

def test_directive():
    """
    Test the i18n directive

      >>> from zope.app.testing.placelesssetup import setUp, tearDown
      >>> setUp()

    First, we need to register the ZCML directive:

      >>> import zope.app.i18n
      >>> from Products.Five import zcml
      >>> zcml.load_config('meta.zcml', zope.app.i18n)

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


    Clean up:

      >>> tearDown()
    """

def test_suite():
    from Testing.ZopeTestCase import ZopeDocTestSuite
    return ZopeDocTestSuite()

if __name__ == '__main__':
    framework()
