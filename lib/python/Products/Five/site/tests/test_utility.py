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

import unittest
import sets
from Testing import ZopeTestCase

from zope.app import zapi
from zope.app.component import getNextUtility
from zope.app.component.hooks import setHooks
from zope.app.testing.placelesssetup import setUp, tearDown
from zope.component import getSiteManager
from zope.component import provideUtility
from zope.interface import directlyProvides

import Products.Five
from Products.Five import zcml
from Products.Five.site.interfaces import IRegisterUtilitySimply
from Products.Five.site.tests.dummy import manage_addDummySite, \
     IDummyUtility, ISuperDummyUtility, DummyUtility
from Products.Five.site.localsite import enableLocalSiteHook

class LocalUtilityServiceTest(ZopeTestCase.ZopeTestCase):

    def afterSetUp(self):
        setUp()
        zcml.load_config("meta.zcml", Products.Five)
        zcml.load_config("permissions.zcml", Products.Five)
        zcml.load_config("configure.zcml", Products.Five.component)
        zcml.load_config("configure.zcml", Products.Five.site)
        zcml_text = """\
        <five:localsite
            xmlns:five="http://namespaces.zope.org/five"
            class="Products.Five.site.tests.dummy.DummySite" />"""

        import warnings
        showwarning = warnings.showwarning
        warnings.showwarning = lambda *a, **k: None

        zcml.load_string(zcml_text)
        manage_addDummySite(self.folder, 'site')
        enableLocalSiteHook(self.folder.site)
        
        warnings.showwarning = showwarning

        # Hook up custom component architecture calls; we need to do
        # this here because zope.app.component.hooks registers a
        # cleanup with the testing cleanup framework, so the hooks get
        # torn down by placelesssetup each time.
        setHooks()

    def beforeTearDown(self):
        tearDown()

    def test_getSiteManagerHook(self):
        from Products.Five.site.localsite import FiveSiteManager
        from Products.Five.site.utility import SimpleLocalUtilityRegistry

        local_sm = getSiteManager(None)
        self.failIf(local_sm is zapi.getGlobalSiteManager())
        self.failUnless(isinstance(local_sm, FiveSiteManager))

        local_sm = getSiteManager(self.folder.site)
        self.failIf(local_sm is zapi.getGlobalSiteManager())
        self.failUnless(isinstance(local_sm, FiveSiteManager))

        sm = getSiteManager()
        self.failUnless(isinstance(sm.utilities, SimpleLocalUtilityRegistry))

    def test_getUtilitiesNoUtilitiesFolder(self):
        sm = getSiteManager()
        
        self.failUnless(sm.queryUtility(IDummyUtility) is None)
        self.assertEquals(list(sm.getUtilitiesFor(IDummyUtility)), [])
        self.assertEquals(list(sm.getAllUtilitiesRegisteredFor(IDummyUtility)), [])

    def test_registerUtilityOnUtilityRegistry(self):
        utils = getSiteManager().utilities
        dummy = DummyUtility()
        utils.registerUtility(IDummyUtility, dummy, 'dummy')

        self.assertEquals(zapi.getUtility(IDummyUtility, name='dummy'), dummy)
        self.assertEquals(list(zapi.getUtilitiesFor(IDummyUtility)), 
                          [('dummy', dummy)])
        self.assertEquals(list(zapi.getAllUtilitiesRegisteredFor(
            IDummyUtility)), [dummy])

    def test_registerUtilityOnSiteManager(self):
        sm = getSiteManager()
        self.failUnless(IRegisterUtilitySimply.providedBy(sm))
        dummy = DummyUtility()
        sm.registerUtility(IDummyUtility, dummy, 'dummy')

        self.assertEquals(zapi.getUtility(IDummyUtility, name='dummy'), dummy)
        self.assertEquals(list(zapi.getUtilitiesFor(IDummyUtility)), 
                          [('dummy', dummy)])
        self.assertEquals(list(zapi.getAllUtilitiesRegisteredFor(
            IDummyUtility)), [dummy])

    def test_registerUtilityWithZopeComponentAPI1(self):
        # With positional arguments
        sm = getSiteManager()
        dummy = DummyUtility()

        sm.registerUtility(dummy, IDummyUtility, 'dummy')

        self.assertEquals(zapi.getUtility(IDummyUtility, name='dummy'), dummy)
        self.assertEquals(list(zapi.getUtilitiesFor(IDummyUtility)), 
                          [('dummy', dummy)])
        self.assertEquals(list(zapi.getAllUtilitiesRegisteredFor(
            IDummyUtility)), [dummy])

    def test_registerUtilityWithZopeComponentAPI1(self):
        # Without name
        sm = getSiteManager()
        dummy = DummyUtility()

        sm.registerUtility(dummy, IDummyUtility)

        self.assertEquals(zapi.getUtility(IDummyUtility), dummy)
        self.assertEquals(list(zapi.getUtilitiesFor(IDummyUtility)), 
                          [('', dummy)])
        self.assertEquals(list(zapi.getAllUtilitiesRegisteredFor(
            IDummyUtility)), [dummy])

    def test_registerUtilityWithZopeComponentAPI3(self):
        # With keyword arguments
        sm = getSiteManager()
        dummy = DummyUtility()

        sm.registerUtility(component=dummy, provided=IDummyUtility, 
                           name='dummy')
        self.assertEquals(zapi.getUtility(IDummyUtility, name='dummy'), dummy)
        self.assertEquals(list(zapi.getUtilitiesFor(IDummyUtility)), 
                          [('dummy', dummy)])
        self.assertEquals(list(zapi.getAllUtilitiesRegisteredFor(
            IDummyUtility)), [dummy])
        
    def test_registerUtilityWithZopeComponentAPI4(self):
        # The Full kabob:
        sm = getSiteManager()
        dummy = DummyUtility()
        
        sm.registerUtility(component=dummy, provided=IDummyUtility, 
                           name='dummy', info=u'The Dummy', event=True)
        self.assertEquals(zapi.getUtility(IDummyUtility, name='dummy'), dummy)
        self.assertEquals(list(zapi.getUtilitiesFor(IDummyUtility)), 
                          [('dummy', dummy)])
        self.assertEquals(list(zapi.getAllUtilitiesRegisteredFor(
            IDummyUtility)), [dummy])

    def test_registerTwoUtilitiesWithSameNameDifferentInterface(self):
        sm = getSiteManager()
        self.failUnless(IRegisterUtilitySimply.providedBy(sm))
        dummy = DummyUtility()
        superdummy = DummyUtility()
        directlyProvides(superdummy, ISuperDummyUtility)
        sm.registerUtility(IDummyUtility, dummy, 'dummy')
        sm.registerUtility(ISuperDummyUtility, superdummy, 'dummy')

        self.assertEquals(zapi.getUtility(IDummyUtility, 'dummy'), dummy)
        self.assertEquals(zapi.getUtility(ISuperDummyUtility, 'dummy'),
                          superdummy)

    def test_derivedInterfaceRegistration(self):
        # Utilities providing a derived interface should be listed
        # when you ask for an interface. So ask for IDummmyInterace, and
        # anything registered for IDummyInterface of ISuperDummyInterface
        # should come back.

        sm = getSiteManager()
        self.failUnless(IRegisterUtilitySimply.providedBy(sm))
        dummy = DummyUtility()
        superdummy = DummyUtility()
        directlyProvides(superdummy, ISuperDummyUtility)
        uts = list(sm.getUtilitiesFor(IDummyUtility))
        self.failUnlessEqual(uts, [])

        sm.registerUtility(ISuperDummyUtility, superdummy)
        
        # We should be able to access this utility both with 
        # IDummyUtility and ISuperDummyUtility interfaces:
        uts = list(sm.getUtilitiesFor(IDummyUtility))
        self.failUnless(uts[0][1].aq_base is superdummy)
        uts = list(sm.getUtilitiesFor(ISuperDummyUtility))
        self.failUnless(uts[0][1].aq_base is superdummy)
        
        # Also try that the standard zapi call works:
        ut = zapi.getUtility(IDummyUtility, context=self.folder.site)
        self.failUnless(ut.aq_base is superdummy)
        ut = zapi.getUtility(ISuperDummyUtility, context=self.folder.site)
        self.failUnless(ut.aq_base is superdummy)
    
        # If we register a second utility we should find both utilities
        # when looking for the base interface
        sm.registerUtility(IDummyUtility, dummy)

        uts = list(sm.getAllUtilitiesRegisteredFor(IDummyUtility))
        self.failUnless(dummy in uts)
        self.failUnless(superdummy in uts)

        # But we should find only one when looking for the derived interface
        uts = list(sm.getAllUtilitiesRegisteredFor(ISuperDummyUtility))
        self.failUnless(dummy not in uts)
        self.failUnless(superdummy in uts)


    def test_nestedSitesDontConflictButStillAcquire(self):
        # let's register a dummy utility in the dummy site
        dummy = DummyUtility()
        sm = getSiteManager()
        sm.registerUtility(IDummyUtility, dummy)

        # let's also create a subsite and make that our site
        manage_addDummySite(self.folder.site, 'subsite')
        import warnings
        showwarning = warnings.showwarning
        warnings.showwarning = lambda *a, **k: None
        enableLocalSiteHook(self.folder.site.subsite)
        warnings.showwarning = showwarning

        # we should still be able to lookup the original utility from
        # the site one level above
        self.assertEqual(zapi.getUtility(IDummyUtility), dummy)

        # now we register a dummy utility in the subsite and see that
        # its registration doesn't conflict
        subdummy = DummyUtility()
        sm = getSiteManager()
        sm.registerUtility(IDummyUtility, subdummy)

        # when we look it up we get the more local one now because the
        # more local one shadows the less local one
        self.assertEqual(zapi.getUtility(IDummyUtility), subdummy)

        # getAllUtilitiesFor gives us both the more local and the less
        # local utility (XXX not sure if this is the right semantics
        # for getAllUtilitiesFor)
        self.assertEqual(sets.Set(zapi.getAllUtilitiesRegisteredFor(IDummyUtility)),
                         sets.Set([subdummy, dummy]))

        # getUtilitiesFor will only find one, because the more local
        # one shadows the less local one
        self.assertEqual(list(zapi.getUtilitiesFor(IDummyUtility)),
                         [('', subdummy)])

    def test_registeringTwiceIsConflict(self):
        dummy1 = DummyUtility()
        dummy2 = DummyUtility()
        sm = getSiteManager()
        sm.registerUtility(IDummyUtility, dummy1)
        self.assertRaises(ValueError, sm.registerUtility,
                          IDummyUtility, dummy2)

        sm.registerUtility(IDummyUtility, dummy1, 'dummy')
        self.assertRaises(ValueError, sm.registerUtility,
                          IDummyUtility, dummy2, 'dummy')

    def test_utilitiesHaveProperAcquisitionContext(self):
        dummy = DummyUtility()
        sm = getSiteManager()
        sm.registerUtility(IDummyUtility, dummy)

        # let's see if we can acquire something all the way from the
        # root (Application) object; we need to be careful to choose
        # something that's only available from the root object
        from Acquisition import aq_acquire
        dummy = zapi.getUtility(IDummyUtility)
        acquired = aq_acquire(dummy, 'ZopeAttributionButton', None)
        self.failUnless(acquired is not None)

        name, dummy = zapi.getUtilitiesFor(IDummyUtility).next()
        acquired = aq_acquire(dummy, 'ZopeAttributionButton', None)
        self.failUnless(acquired is not None)

        dummy = zapi.getAllUtilitiesRegisteredFor(IDummyUtility).next()
        acquired = aq_acquire(dummy, 'ZopeAttributionButton', None)
        self.failUnless(acquired is not None)        

    def test_getNextUtility(self):
        # test local site vs. global site
        global_dummy = DummyUtility()
        provideUtility(global_dummy, IDummyUtility)

        local_dummy = DummyUtility()
        sm = getSiteManager()
        sm.registerUtility(IDummyUtility, local_dummy)

        self.assertEquals(zapi.getUtility(IDummyUtility), local_dummy)
        self.assertEquals(getNextUtility(self.folder.site, IDummyUtility),
                          global_dummy)

        # test local site vs. nested local site
        manage_addDummySite(self.folder.site, 'subsite')
        import warnings
        showwarning = warnings.showwarning
        warnings.showwarning = lambda *a, **k: None
        enableLocalSiteHook(self.folder.site.subsite)
        warnings.showwarning = showwarning

        sublocal_dummy = DummyUtility()
        sm = getSiteManager()
        sm.registerUtility(IDummyUtility, sublocal_dummy)

        self.assertEquals(zapi.getUtility(IDummyUtility), sublocal_dummy)
        self.assertEquals(getNextUtility(self.folder.site.subsite, IDummyUtility),
                          local_dummy)
        self.assertEquals(getNextUtility(self.folder.site, IDummyUtility),
                          global_dummy)


class LocalUtilityMigrateTest(ZopeTestCase.ZopeTestCase):

    def afterSetUp(self):
        setUp()
        zcml.load_config("meta.zcml", Products.Five)
        zcml.load_config("permissions.zcml", Products.Five)
        zcml.load_config("configure.zcml", Products.Five.component)
        zcml.load_config("configure.zcml", Products.Five.site)
        zcml_text = """\
        <five:localsite
            xmlns:five="http://namespaces.zope.org/five"
            class="OFS.Folder.Folder" />"""

        import warnings
        showwarning = warnings.showwarning
        warnings.showwarning = lambda *a, **k: None

        zcml.load_string(zcml_text)
        enableLocalSiteHook(self.folder)
        
        warnings.showwarning = showwarning

        # Hook up custom component architecture calls; we need to do
        # this here because zope.app.component.hooks registers a
        # cleanup with the testing cleanup framework, so the hooks get
        # torn down by placelesssetup each time.
        setHooks()

    def test_migration(self):
        # Migrate from Five.site to Five.component
        
        # Register utilities
        sm = getSiteManager()
        self.failUnless(IRegisterUtilitySimply.providedBy(sm))
        dummy = DummyUtility()
        superdummy = DummyUtility()
        directlyProvides(superdummy, ISuperDummyUtility)
        sm.registerUtility(IDummyUtility, dummy, 'dummy')
        sm.registerUtility(ISuperDummyUtility, superdummy, 'dummy')

        self.assertEquals(zapi.getUtility(IDummyUtility, 'dummy'), dummy)
        self.assertEquals(zapi.getUtility(ISuperDummyUtility, 'dummy'),
                          superdummy)
        
        siteview = self.folder.unrestrictedTraverse('manage_site.html')
        siteview.migrateToFive15()

        self.assert_('utilities' not in self.folder.objectIds())
        # It should still work
        self.assertEquals(zapi.getUtility(IDummyUtility, 'dummy'), dummy)
        self.assertEquals(zapi.getUtility(ISuperDummyUtility, 'dummy'),
                          superdummy)


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(LocalUtilityServiceTest))
    suite.addTest(unittest.makeSuite(LocalUtilityMigrateTest))
    return suite

if __name__ == '__main__':
    framework()
