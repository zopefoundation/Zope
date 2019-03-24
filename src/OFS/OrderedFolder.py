##############################################################################
#
# Copyright (c) 2003 Zope Foundation and Contributors.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
""" 'Folder' with order support.
"""

from App.special_dtml import DTMLFile
from OFS.Folder import Folder
from OFS.interfaces import IOrderedFolder
from OFS.OrderSupport import OrderSupport
from zope.interface import implementer


manage_addOrderedFolderForm = DTMLFile('dtml/addOrderedFolder', globals())


def manage_addOrderedFolder(self, id, title='', createPublic=0, createUserF=0,
                            REQUEST=None):
    """Add a new ordered Folder object with id *id*.
    """
    ob = OrderedFolder(id)
    ob.title = title
    self._setObject(id, ob)
    ob = self._getOb(id)
    if REQUEST:
        return self.manage_main(self, REQUEST)


@implementer(IOrderedFolder)
class OrderedFolder(OrderSupport, Folder):

    """ Extends the default Folder by order support.
    """
    meta_type = 'Folder (Ordered)'
    zmi_icon = 'far fa-folder zmi-icon-folder-ordered'

    manage_options = OrderSupport.manage_options + Folder.manage_options[1:]
