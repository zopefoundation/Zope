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
"""ZCatalog Text Index

Experimental plugin text index for ZCatalog.
"""

from PipelineFactory import splitter_factory, element_factory
from Products.ZCTextIndex import ZCTextIndex, HTMLSplitter

def initialize(context):

    context.registerClass(
        ZCTextIndex.ZCTextIndex,
        permission = 'Add Pluggable Index',
        constructors = (ZCTextIndex.manage_addZCTextIndexForm,
                        ZCTextIndex.manage_addZCTextIndex,
                        getIndexTypes),
        icon='www/index.gif',
        visibility=None
    )

    context.registerClass(
        ZCTextIndex.PLexicon,
        permission = 'Add Vocabularies',
        constructors = (ZCTextIndex.manage_addLexiconForm,
                        ZCTextIndex.manage_addLexicon,
                        getSplitterNames, getElementNames),
        icon='www/lexicon.gif'
    )
    
## Functions below are for use in the ZMI constructor forms ##
    
def getSplitterNames(self):
    return splitter_factory.getFactoryNames()
    
def getElementNames(self):
    return element_factory.getFactoryNames()
    
def getIndexTypes(self):
    return ZCTextIndex.index_types.keys()
    
