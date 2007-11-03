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
"""Local sites browser views

$Id$
"""
from zope.app.component.interfaces import ISite
from zope.app.component.hooks import clearSite, setSite
from zope.component import getSiteManager, queryMultiAdapter
from zope.interface import Interface, providedBy

from Products.Five.browser import BrowserView
from Products.Five.site.localsite import enableLocalSiteHook, disableLocalSiteHook

class LocalSiteView(BrowserView):
    """View for convering a possible site to a site
    """

    def update(self):
        form = self.request.form
        if form.has_key('UPDATE_MAKESITE'):
            self.makeSite()
        elif form.has_key('UPDATE_UNMAKESITE'):
            self.unmakeSite()
        elif form.has_key('UPDATE_MIGRATE'):
            self.migrateToFive15()

    def isSite(self):
        return ISite.providedBy(self.context)

    def isOldSite(self):
        from Products.Five.site.interfaces import IFiveSiteManager
        return self.isSite() and IFiveSiteManager.providedBy(getSiteManager())

    def makeSite(self):
        """Convert a possible site to a site"""
        if self.isSite():
            raise ValueError('This is already a site')

        enableLocalSiteHook(self.context)
        return "This object is now a site"

    def unmakeSite(self):
        """Convert a site to a possible site"""
        if not self.isSite():
            raise ValueError('This is not a site')

        disableLocalSiteHook(self.context)

        # disableLocalSiteHook circumcised our context so that it's
        # not an ISite anymore.  That can mean that certain things for
        # it can't be found anymore.  So, for the rest of this request
        # (which will be over in about 20 CPU cycles), already clear
        # the local site from the thread local.
        clearSite()

        return "This object is no longer a site"

    def migrateToFive15(self):
        all_utilities = self.context.utilities.objectItems()

        self.unmakeSite()
        self.context.manage_delObjects(['utilities'])
        components_view = queryMultiAdapter((self.context, self.request), 
                                            Interface, 'components.html')
        components_view.makeSite()
        setSite(self.context)

        site_manager = getSiteManager()
        for id, utility in all_utilities:
            info = id.split('-')
            if len(info) == 1:
                name = ''
            else:
                name = info[1]
            interface_name = info[0]

            for iface in providedBy(utility):
                if iface.getName() == interface_name:
                    site_manager.registerUtility(utility, iface, name=name)

        return "Migration done!"
