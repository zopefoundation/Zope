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
"""ZODBMountPoint product.

$Id: __init__.py,v 1.1 2003/07/20 02:56:01 chrism Exp $
"""

def initialize(context):
    # Configure and load databases if not already done.
    import MountedObject
    context.registerClass(
        MountedObject.MountedObject,
        constructors=(MountedObject.manage_addMountsForm,
                      MountedObject.manage_getMountStatus,
                      MountedObject.manage_addMounts,),
        )



