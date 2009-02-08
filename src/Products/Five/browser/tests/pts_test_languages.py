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
"""Test the PTS language integration.

$Id$
"""

def test_suite():
    from Testing.ZopeTestCase import installProduct, FunctionalDocFileSuite
    installProduct('Five')
    installProduct('PlacelessTranslationService')
    return FunctionalDocFileSuite('pts_test_languages.txt',
                                  package='Products.Five.browser.tests')
