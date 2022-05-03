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


def test_zpt_i18n():
    """
    Test i18n functionality in ZPTs

      >>> configure_zcml = '''
      ... <configure
      ...     xmlns="http://namespaces.zope.org/zope"
      ...     xmlns:browser="http://namespaces.zope.org/browser"
      ...     xmlns:i18n="http://namespaces.zope.org/i18n">
      ...   <configure package="Products.Five.tests">
      ...     <i18n:registerTranslations directory="locales" />
      ...   </configure>
      ...   <configure package="Products.Five.browser.tests">
      ...     <browser:page
      ...         for="OFS.interfaces.IFolder"
      ...         class=".i18n.I18nView"
      ...         template="i18n.pt"
      ...         name="i18n.html"
      ...         permission="zope2.View"
      ...         />
      ...   </configure>
      ... </configure>'''

      >>> import Products.Five
      >>> from Zope2.App import zcml
      >>> zcml.load_config("configure.zcml", Products.Five)
      >>> zcml.load_string(configure_zcml)
      >>> folder = self.folder  # NOQA: F821
      >>> http = http  # NOQA: F821

    In order to be able to traverse to the PageTemplate view, we need
    a traversable object:

      >>> from Products.Five.tests.testing import (
      ... manage_addFiveTraversableFolder)
      >>> manage_addFiveTraversableFolder(folder, 'testoid', 'Testoid')

    We tell Zope to translate the messages by passing the
    ``Accept-Language`` header which is processed by the
    ``IUserPreferredLangauges`` adapter:

      >>> print(http(r'''
      ... GET /test_folder_1_/testoid/@@i18n.html HTTP/1.1
      ... Accept-Language: de
      ... '''))
      HTTP/1.1 200 OK
      ...
      <p>Dies ist eine Nachricht</p>
      <p>Dies ist eine explizite Nachricht</p>
      <p>Dies sind 4 Nachrichten</p>
      <p>Dies sind 4 explizite Nachrichten</p>
      <table summary="Dies ist ein Attribut">
      </table>
      <table summary="Explizite Zusammenfassung" title="Expliziter Titel">
      </table>
      <p>Dies ist eine Nachricht</p>
      <p>Dies ist eine Nachricht</p>
      ...


    Clean up:

      >>> from zope.component.testing import tearDown
      >>> tearDown()
    """


def test_suite():
    import doctest

    from Testing.ZopeTestCase import FunctionalDocTestSuite
    return FunctionalDocTestSuite(
        optionflags=doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE)
