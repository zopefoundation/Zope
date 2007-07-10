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

import zope.interface
from zope.component import getGlobalSiteManager, getSiteManager
from zope.component.interfaces import ComponentLookupError
from zope.component.interfaces import IComponentLookup
from zope.traversing.interfaces import IContainmentRoot
from zope.app.component.hooks import setSite, getSite, setHooks
from zope.app.component.interfaces import ISite
from zope.app.testing.placelesssetup import PlacelessSetup

from Acquisition import Implicit
from OFS.ObjectManager import ObjectManager

import Products.Five
from Products.Five import zcml

class SiteManager(Implicit):
    zope.interface.implements(IComponentLookup)

    @property
    def __bases__(self):
        next = getattr(self, 'next', None)
        if next is None:
            return ()
        return (next,)

class Folder(ObjectManager):

    def setSiteManager(self, sm):
        super(Folder, self).setSiteManager(sm)
        zope.interface.alsoProvides(self, ISite)

class Package(Implicit):
    pass

class Root(Folder):
    zope.interface.implements(IContainmentRoot, ISite)

    def getSiteManager(self):
        return getGlobalSiteManager()

class SiteManagerStub(object):
    zope.interface.implements(IComponentLookup)

class SiteManagerTest(PlacelessSetup, unittest.TestCase):

    def setUp(self):
        super(SiteManagerTest, self).setUp()
        self.root = root = Root()

        self.f1 = f1 = Folder().__of__(root)
        self.sm1 = sm1 = SiteManager()
        f1.setSiteManager(sm1)
        self.p1 = p1 = Package().__of__(sm1)

        self.f2 = f2 = Folder().__of__(f1)
        self.sm2 = sm2 = SiteManager()
        f2.setSiteManager(sm2)
        self.p2 = p2 = Package().__of__(sm2)

        sm1.next = getGlobalSiteManager()
        sm2.next = sm1

        self.unparented_folder = Folder()
        self.unrooted_subfolder = Folder().__of__(self.unparented_folder)
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
        
        warnings.showwarning = showwarning

        # Hook up custom component architecture calls; we need to do
        # this here because zope.app.component.hooks registers a
        # cleanup with the testing cleanup framework, so the hooks get
        # torn down by placelesssetup each time.
        setHooks()

    def test_getSiteManager(self):
        self.assertEqual(getSiteManager(None), getGlobalSiteManager())
        self.assertEqual(getSiteManager(self.root), getGlobalSiteManager())
        self.assertEqual(getSiteManager(self.f1), self.sm1)
        self.assertEqual(getSiteManager(self.f2), self.sm2)
        setSite(self.f2)
        self.assertEqual(getSiteManager(None), self.sm2)

    # DEPRECATED in Zope 3.4
    #def test_queryNextSiteManager(self):
    #    from zope.app.component import queryNextSiteManager
    #    marker = object()
    #    self.assert_(queryNextSiteManager(self.root, marker) is marker)
    #    self.assert_(queryNextSiteManager(self.f1, marker) is getGlobalSiteManager())
    #    self.assertEqual(queryNextSiteManager(self.f2, marker), self.sm1)
    #    self.assertEqual(queryNextSiteManager(self.sm1), getGlobalSiteManager())
    #    self.assertEqual(queryNextSiteManager(self.sm2), self.sm1)
    #    self.assert_(queryNextSiteManager(self.p1, marker) is marker)
    #    self.assert_(queryNextSiteManager(self.p2, marker) is marker)
    #
    #    self.assert_(queryNextSiteManager(self.unparented_folder, marker)
    #                 is marker)
    #    self.assert_(queryNextSiteManager(self.unrooted_subfolder, marker)
    #                 is marker)

    # DEPRECATED in Zope 3.4
    #def test_getNextSiteManager(self):
    #    from zope.app.component import getNextSiteManager
    #    self.assertRaises(ComponentLookupError, getNextSiteManager, self.root)
    #    self.assertEqual(getNextSiteManager(self.f1), getGlobalSiteManager())
    #    self.assertEqual(getNextSiteManager(self.f2), self.sm1)
    #    self.assertEqual(getNextSiteManager(self.sm1), getGlobalSiteManager())
    #    self.assertEqual(getNextSiteManager(self.sm2), self.sm1)
    #    self.assertRaises(ComponentLookupError, getNextSiteManager, self.p1)
    #    self.assertRaises(ComponentLookupError, getNextSiteManager, self.p2)
    #
    #    self.assertRaises(ComponentLookupError,
    #                      getNextSiteManager, self.unparented_folder)
    #    self.assertRaises(ComponentLookupError,
    #                      getNextSiteManager, self.unrooted_subfolder)

# XXX Maybe we need to test this with RestrictedPython in the context
# of Zope2? Maybe we just don't care.
#
#     def test_getNextSiteManager_security(self):
#         from zope.app.component import getNextSiteManager
#         from zope.security.checker import ProxyFactory, NamesChecker
#         sm = ProxyFactory(self.sm1, NamesChecker(('next',)))
#         # Check that getGlobalSiteManager() is not proxied
#         self.assert_(getNextSiteManager(sm) is getGlobalSiteManager())

    def test_setThreadSite_clearThreadSite(self):
        from zope.app.component.site import threadSiteSubscriber, clearSite
        from zope.app.publication.zopepublication import BeforeTraverseEvent

        self.assertEqual(getSite(), None)

        # A site is traversed
        sm = SiteManagerStub()
        site = Folder()
        site.setSiteManager(sm)

        ev = BeforeTraverseEvent(site, object())
        threadSiteSubscriber(site, ev)
        self.assertEqual(getSite(), site)

        clearSite()
        self.assertEqual(getSite(), None)

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(SiteManagerTest))
    return suite

if __name__ == '__main__':
    framework()
