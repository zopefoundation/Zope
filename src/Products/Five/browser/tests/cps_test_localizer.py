##############################################################################
#
# Copyright (c) 2005 Zope Corporation and Contributors.
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
"""Test the Localizer language integration for CPS.  This test
requires a full blown CPS installation to run.  It is therefore
prefixed with ``cps_`` so it won't be picked up by the test runner.

$Id$
"""

def test_suite():
    from Testing.ZopeTestCase import installProduct, FunctionalDocFileSuite
    installProduct('Five')
    installProduct('BTreeFolder2')
    installProduct('CMFCalendar')
    installProduct('CMFCore')
    installProduct('CMFDefault')
    installProduct('CMFTopic')
    installProduct('DCWorkflow')
    installProduct('Localizer')
    installProduct('MailHost')
    installProduct('CPSCore')
    installProduct('CPSDefault')
    installProduct('CPSDirectory')
    installProduct('CPSUserFolder')
    installProduct('TranslationService')
    installProduct('SiteAccess')
    # these products should (and used to be) be optional, but they
    # aren't right now.
    installProduct('CPSForum')
    installProduct('CPSSubscriptions')
    installProduct('CPSNewsLetters')
    installProduct('CPSSchemas')
    installProduct('CPSDocument')
    installProduct('PortalTransforms')
    installProduct('Epoz')
    # optional products, but apparently still needed...
    installProduct('CPSRSS')
    installProduct('CPSChat')
    installProduct('CPSCalendar')
    installProduct('CPSCollector')
    installProduct('CPSMailBoxer')

    return FunctionalDocFileSuite('cps_test_localizer.txt',
                                  package='Products.Five.browser.tests')
