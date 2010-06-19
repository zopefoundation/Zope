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
'''Zope registerable permissions
'''


from AccessControl.class_init import InitializeClass
from AccessControl.SecurityInfo import ClassSecurityInfo
from Acquisition import Implicit
from OFS.role import RoleManager
from OFS.SimpleItem import Item
from Persistence import Persistent

class Permission(RoleManager,
                 Persistent,
                 Implicit,
                 Item
                ):
    """Model Permission meta-data
    """
    meta_type = 'Zope Permission'
    icon = 'p_/Permission_icon'
    index_html = None
    security = ClassSecurityInfo()

    manage_options=(
        RoleManager.manage_options
        + Item.manage_options
        )

    def __init__(self, id, title, name):
        self.id=id
        self.title=title
        self.name=name

InitializeClass(Permission)
