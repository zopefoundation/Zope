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
"""Test local sites

$Id$
"""
import os, sys

if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

import pprint
from zope.app import zapi
from Products.Five import BrowserView
from Products.Five.site.interfaces import IFiveUtilityRegistry
from Products.Five.site.localsite import FiveSiteManager
from Products.Five.site.tests.dummy import IDummyUtility

class CheckSiteManagerView(BrowserView):

    def __call__(self):
        sm = zapi.getSiteManager()
        result = {
            'zapi.getSiteManager() is zapi.getGlobalSiteManager()':
            sm is zapi.getGlobalSiteManager(),
            'IFiveUtilityRegistry.providedBy(utility_service)':
            IFiveUtilityRegistry.providedBy(sm.utilities),
            'isinstance(zapi.getSiteManager(), FiveSiteManager)':
            isinstance(sm, FiveSiteManager),
            }
        return pprint.pformat(result)

class LookupUtilitiesView(BrowserView):

    def __call__(self):
        dummy = getattr(self.context.utilities, IDummyUtility.getName())
        return "zapi.getUtility(IDummyUtility) == dummy: %s" % \
               (zapi.getUtility(IDummyUtility) == dummy)

def test_suite():
    from Testing.ZopeTestCase import FunctionalDocFileSuite
    suite = FunctionalDocFileSuite('functional.txt',
                                   package='Products.Five.site.tests')
    suite.level = 2
    return suite

if __name__ == '__main__':
    framework()
