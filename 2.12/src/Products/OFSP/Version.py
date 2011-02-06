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
"""Version object"""

__version__='$Revision: 1.55 $'[11:-2]

from AccessControl.SecurityInfo import ClassSecurityInfo
from App.class_init import InitializeClass
from OFS.SimpleItem import Item
from Persistence import Persistent
from OFS.ObjectManager import BeforeDeleteException

class VersionException(BeforeDeleteException):
    pass


class Version(Persistent, Item):
    """ """
    meta_type='Version'
    security = ClassSecurityInfo()
    cookie=''
    index_html=None # Ugh.

    def __init__(self, id, title, REQUEST):
        self.id=id
        self.title=title

    def icon(self):
        return 'p_/broken'

InitializeClass(Version)
