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
"""Dummy test fixtures

$Id$
"""
from zope.interface import implements, implementsOnly, Interface
from OFS.SimpleItem import SimpleItem
from Products.Five.tests.testing import FiveTraversableFolder

class IDummySite(Interface):
    pass

class DummySite(FiveTraversableFolder):
    """A very dummy Site
    """
    # we specifically do not let this site inherit any interfaces from
    # the superclasses so that this class does not implement
    # IPossibleSite under any circumstances
    implementsOnly(IDummySite)

def manage_addDummySite(self, id, REQUEST=None):
    """Add the dummy site."""
    id = self._setObject(id, DummySite(id))
    return ''

class IDummyUtility(Interface):
    pass

class ISuperDummyUtility(IDummyUtility):
    pass

class DummyUtility(SimpleItem):
    implements(IDummyUtility)
