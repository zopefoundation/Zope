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
"""Adapter test fixtures
"""

from zope.interface import implements, Interface
from zope.component import adapts


class IAdaptable(Interface):
    """This is a Zope interface.
    """
    def method():
        """This method will be adapted
        """


class IAdapted(Interface):
    """The interface we adapt to.
    """

    def adaptedMethod():
        """A method to adapt.
        """


class IOrigin(Interface):
    """Something we'll adapt"""


class IDestination(Interface):
    """The result of an adaption"""

    def method():
        """Do something"""


class Adaptable(object):
    implements(IAdaptable)

    def method(self):
        return "The method"


class Adapter(object):
    implements(IAdapted)
    adapts(IAdaptable)

    def __init__(self, context):
        self.context = context

    def adaptedMethod(self):
        return "Adapted: %s" % self.context.method()


class Origin(object):
    implements(IOrigin)


class OriginalAdapter(object):
    implements(IDestination)

    def __init__(self, context):
        self.context = context

    def method(self):
        return "Original"


class OverrideAdapter(object):
    implements(IDestination)

    def __init__(self, context):
        self.context = context

    def method(self):
        return "Overridden"
