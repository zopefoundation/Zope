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
"""Local utility registration

$Id$
"""
from zope.interface import implements
from zope.component import getGlobalSiteManager
from zope.component.exceptions import ComponentLookupError
from zope.app.component import getNextSiteManager

from Acquisition import aq_base
from OFS.Folder import Folder
from Products.Five.site.interfaces import IFiveUtilityRegistry

class SimpleLocalUtilityRegistry(object):
    implements(IFiveUtilityRegistry)

    def __init__(self, context):
        self.context = context
        # make {get|query}NextSiteManager() work without having to
        # resort to Zope 2 acquisition
        self.__parent__ = self.context.getSiteManager()

    @property
    def next(self):
        try:
            return getNextSiteManager(self)
        except ComponentLookupError:
            return getGlobalSiteManager()

    def getUtility(self, interface, name=''):
        """See IFiveUtilityRegistry interface
        """
        c = self.queryUtility(interface, name)
        if c is not None:
            return c
        raise ComponentLookupError(interface, name)

    def queryUtility(self, interface, name='', default=None):
        """See IFiveUtilityRegistry interface
        """
        if name == '':
            # Singletons. Only one per interface allowed, so, let's call it
            # by the interface.
            id = interface.getName()
        else:
            id = interface.getName() + '-' + name

        if getattr(aq_base(self.context), 'utilities', None) is not None:
            utility = self.context.utilities._getOb(id, None)
            if utility is not None:
                return utility
        return self.next.queryUtility(interface, name, default)

    def getUtilitiesFor(self, interface):
        names = []
        prefix = interface.getName() + '-'
        if getattr(aq_base(self.context), 'utilities', None) is not None:
            for name, utility in self.context.utilities.objectItems():
                if name == interface.getName():
                    names.append('')
                    yield '', utility
                elif name.startswith(prefix):
                    name = name[len(prefix):]
                    names.append(name)
                    yield (name, utility)
        for name, utility in self.next.getUtilitiesFor(interface):
            if name not in names:
                yield name, utility

    def getAllUtilitiesRegisteredFor(self, interface):
        # This also supposedly returns "overridden" utilities, but we don't
        # keep them around. It also does not return the name-value pair that
        # getUtilitiesFor returns.
        if getattr(aq_base(self.context), 'utilities', None) is not None:
            for utility in self.context.utilities.objectValues():
                if interface.providedBy(utility):
                    yield utility
        for utility in self.next.getAllUtilitiesRegisteredFor(interface):
            yield utility

    def registerUtility(self, interface, utility, name=''):
        # I think you are *really* supposed to:
        # 1. Check if there is a "registrations" object for utilities.
        # 2. If not create one.
        # 3. Get it.
        # 4. Create a registration object for the utility.
        # 5. Rgister the registration object in the registrations.
        # But that is quite complex, and Jim sais he wants to change that
        # anyway, and in any case the way you would normally do this in Zope3
        # and Five would probably differ anyway, so, here is this new
        # Five-only, easy to use method!

        if getattr(aq_base(self.context), 'utilities', None) is None:
            self.context._setObject('utilities', Folder('utilities'))
        utilities = self.context.utilities

        if name == '':
            # Singletons. Only one per interface allowed, so, let's call it
            # by the interface.
            id = interface.getName()
        else:
            id = interface.getName() + '-' + name

        if id in utilities.objectIds():
            raise ValueError("There is already a utility registered for "
                             "%s with the name '%s'" % (interface.getName(),
                                                        name))
        utilities._setObject(id, utility)

# BBB 2005/11/01 -- gone in Five 1.5.
SimpleLocalUtilityService = SimpleLocalUtilityRegistry
import zope.deprecation
zope.deprecation.deprecated(
    'SimpleLocalUtilityService', "'SimpleLocalUtilityService' has been renamed to "
    "'SimpleLocalUtilityRegistry' and will disappear in Five 1.5."
    )
