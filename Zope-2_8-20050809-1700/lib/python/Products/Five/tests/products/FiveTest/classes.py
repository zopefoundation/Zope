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
"""Adapter test classes.

$Id: classes.py 12915 2005-05-31 10:23:19Z philikon $
"""
from zope.interface import implements
from interfaces import IAdaptable, IAdapted, IOrigin, IDestination

class Adaptable:
    implements(IAdaptable)

    def method(self):
        return "The method"

class Adapter:
    implements(IAdapted)

    def __init__(self, context):
        self.context = context

    def adaptedMethod(self):
        return "Adapted: %s" % self.context.method()

class Origin:
    implements(IOrigin)

class OriginalAdapter:
    implements(IDestination)

    def __init__(self, context):
        self.context = context

    def method(self):
        return "Original"

class OverrideAdapter:
    implements(IDestination)

    def __init__(self, context):
        self.context = context

    def method(self):
        return "Overridden"
