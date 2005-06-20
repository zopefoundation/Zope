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
"""CMFBTreeFolder

$Id: CMFBTreeFolder.py,v 1.2 2002/10/30 14:54:18 shane Exp $
"""

import Globals
from BTreeFolder2 import BTreeFolder2Base
try:
    from Products.CMFCore.PortalFolder import PortalFolderBase as PortalFolder
except ImportError:
    from Products.CMFCore.PortalFolder import PortalFolder
import Products.CMFCore.PortalFolder


_actions = Products.CMFCore.PortalFolder.factory_type_information[0]['actions']

factory_type_information = ( { 'id'             : 'CMF BTree Folder',
                               'meta_type'      : 'CMF BTree Folder',
                               'description'    : """\
CMF folder designed to hold a lot of objects.""",
                               'icon'           : 'folder_icon.gif',
                               'product'        : 'BTreeFolder2',
                               'factory'        : 'manage_addCMFBTreeFolder',
                               'filter_content_types' : 0,
                               'immediate_view' : 'folder_edit_form',
                               'actions'        : _actions,
                               },
                           )


def manage_addCMFBTreeFolder(dispatcher, id, title='', REQUEST=None):
    """Adds a new BTreeFolder object with id *id*.
    """
    id = str(id)
    ob = CMFBTreeFolder(id)
    ob.title = str(title)
    dispatcher._setObject(id, ob)
    ob = dispatcher._getOb(id)
    if REQUEST is not None:
        REQUEST['RESPONSE'].redirect(ob.absolute_url() + '/manage_main' )


class CMFBTreeFolder(BTreeFolder2Base, PortalFolder):
    """BTree folder for CMF sites.
    """
    meta_type = 'CMF BTree Folder'

    def __init__(self, id, title=''):
        PortalFolder.__init__(self, id, title)
        BTreeFolder2Base.__init__(self, id)

    def _checkId(self, id, allow_dup=0):
        PortalFolder._checkId(self, id, allow_dup)
        BTreeFolder2Base._checkId(self, id, allow_dup)


Globals.InitializeClass(CMFBTreeFolder)

