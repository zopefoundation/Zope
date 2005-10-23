##############################################################################
#
# Copyright (c) 2004, 2005 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Five interfaces

$Id: interfaces.py 14613 2005-07-13 10:39:05Z philikon $
"""
from zope.interface import Interface
from zope.interface.interfaces import IInterface

class IBrowserDefault(Interface):
    """Provide a hook for deciding about the default view for an object"""

    def defaultView(self, request):
        """Return the object to be published
        (usually self) and a sequence of names to traverse to
        find the method to be published.
        """

class IMenuItemType(IInterface):
    """Menu item type

    Menu item types are interfaces that define classes of
    menu items.
    """


#
# BBB: Zope core interfaces
#
# The interfaces here are only provided for backwards compatibility and will
# be removed in Five 1.2. Please import interfaces from the corresponding Zope
# package instead.
#

from persistent.interfaces import IPersistent
from AccessControl.interfaces import *
from Acquisition.interfaces import *
from App.interfaces import *
from OFS.interfaces import *
from webdav.interfaces import *

# BBB: for old names used in Five 1.0
IAcquisition = IAcquirer
IPermissionMapping = IPermissionMappingSupport
