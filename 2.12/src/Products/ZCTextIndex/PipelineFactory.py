##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
from zope.interface import implements

from Products.ZCTextIndex.IPipelineElementFactory \
     import IPipelineElementFactory

class PipelineElementFactory:

    implements(IPipelineElementFactory)

    def __init__(self):
        self._groups = {}

    def registerFactory(self, group, name, factory):
        if self._groups.has_key(group) and \
           self._groups[group].has_key(name):
            raise ValueError('ZCTextIndex lexicon element "%s" '
                             'already registered in group "%s"'
                             % (name, group))

        elements = self._groups.get(group)
        if elements is None:
            elements = self._groups[group] = {}
        elements[name] = factory

    def getFactoryGroups(self):
        groups = self._groups.keys()
        groups.sort()
        return groups

    def getFactoryNames(self, group):
        names = self._groups[group].keys()
        names.sort()
        return names

    def instantiate(self, group, name):
        factory = self._groups[group][name]
        if factory is not None:
            return factory()

element_factory = PipelineElementFactory()
