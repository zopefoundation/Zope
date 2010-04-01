##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
'''
Some standard Zope cache managers from Digital Creations.

$Id$
'''

import RAMCacheManager
import AcceleratedHTTPCacheManager

def initialize(context):
    context.registerClass(
        RAMCacheManager.RAMCacheManager,
        constructors = (RAMCacheManager.manage_addRAMCacheManagerForm,
                        RAMCacheManager.manage_addRAMCacheManager),
        icon="cache.gif"
        )

    context.registerClass(
        AcceleratedHTTPCacheManager.AcceleratedHTTPCacheManager,
        constructors = (
        AcceleratedHTTPCacheManager.manage_addAcceleratedHTTPCacheManagerForm,
        AcceleratedHTTPCacheManager.manage_addAcceleratedHTTPCacheManager),
        icon="cache.gif"
        )

    context.registerHelp()
