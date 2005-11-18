##############################################################################
#
# Copyright (c) 2002 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Write lock interfaces.

$Id$
"""


# create WriteLockInterface
from Interface.bridge import createZope3Bridge
from interfaces import ILockItem
from interfaces import IWriteLock
import WriteLockInterface

createZope3Bridge(ILockItem, WriteLockInterface, 'LockItemInterface')
createZope3Bridge(IWriteLock, WriteLockInterface, 'WriteLockInterface')

del createZope3Bridge
del ILockItem
del IWriteLock
