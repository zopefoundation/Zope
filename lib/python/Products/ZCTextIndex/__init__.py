##############################################################################
#
# Copyright (c) 2001, 2002 Zope Corporation and Contributors.
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

def initialize(context):
    from Products.ZCTextIndex import ZCTextIndex

    context.registerClass(
        ZCTextIndex.ZCTextIndex,
        permission='Add Pluggable Index',
        constructors=(ZCTextIndex.manage_addZCTextIndexForm,
                      ZCTextIndex.manage_addZCTextIndex),
        visibility=None
    )
