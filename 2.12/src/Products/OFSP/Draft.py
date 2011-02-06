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

from AccessControl.SecurityInfo import ClassSecurityInfo
from App.class_init import InitializeClass
from OFS.SimpleItem import Item
from Persistence import Persistent


class Draft(Persistent, Item):
    "Draft objects"

    meta_type = 'Zope Draft'
    security = ClassSecurityInfo()

    def __init__(self, id, baseid, PATH_INFO):
        self.id = id

    def icon(self):
        return 'p_/broken'

InitializeClass(Draft)
