##############################################################################
#
# Copyright (c) 2001 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Pluggable Index interfaces.

$Id$
"""


# create PluggableIndexInterface, UniqueValueIndex, SortIndex
from Interface.bridge import createZope3Bridge
from Products.PluginIndexes.interfaces import IPluggableIndex
from Products.PluginIndexes.interfaces import ISortIndex
from Products.PluginIndexes.interfaces import IUniqueValueIndex
import PluggableIndex

createZope3Bridge(IPluggableIndex, PluggableIndex, 'PluggableIndexInterface')
createZope3Bridge(ISortIndex, PluggableIndex, 'SortIndex')
createZope3Bridge(IUniqueValueIndex, PluggableIndex, 'UniqueValueIndex')

del createZope3Bridge
del IPluggableIndex
del ISortIndex
del IUniqueValueIndex
del PluggableIndex
