##############################################################################
#
# Copyright (c) 2002 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################

from Products.ZCTextIndex.IPipelineElementFactory \
     import IPipelineElementFactory
     
class PipelineElementFactory:
    
    __implements__ = IPipelineElementFactory
    
    def __init__(self):
        self._elements = {}
    
    def registerFactory(self, name, factory):
        if self._elements.has_key(name):
            raise ValueError, 'ZCTextIndex splitter named' + \
                              '"%s" already registered'
        
        self._elements[name] = factory
        
    def getFactoryNames(self):
        names = self._elements.keys()
        names.sort()
        return names
        
    def instantiate(self, name):
        return self._elements[name]()
        

splitter_factory = PipelineElementFactory()

element_factory = PipelineElementFactory()
