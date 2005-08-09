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
"""Fancy content

$Id: fancycontent.py 12915 2005-05-31 10:23:19Z philikon $
"""
import Acquisition
from AccessControl import ClassSecurityInfo
from OFS.SimpleItem import SimpleItem
from Globals import InitializeClass

from zope.interface import implements
from interfaces import IFancyContent

class FancyAttribute(Acquisition.Explicit):
    """Doc test fanatics"""

    def __init__(self, name):
        self.name = name

    security = ClassSecurityInfo()

    security.declarePublic('index_html')
    def index_html(self, REQUEST):
        """Doc test fanatics"""
        return self.name

InitializeClass(FancyAttribute)

class FancyContent(SimpleItem):
    """A class that already comes with its own __bobo_traverse__ handler.
    Quite fancy indeed.

    It also comes with its own get_size method.
    """
    implements(IFancyContent)

    meta_type = "Fancy Content"
    security = ClassSecurityInfo()

    def __bobo_traverse__(self, REQUEST, name):
        return FancyAttribute(name).__of__(self)

    def get_size(self):
        return 43

InitializeClass(FancyContent)

def manage_addFancyContent(self, id, REQUEST=None):
    """Add the fancy fancy content."""
    id = self._setObject(id, FancyContent(id))
    return ''
