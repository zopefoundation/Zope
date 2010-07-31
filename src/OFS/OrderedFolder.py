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

from AccessControl.SecurityManagement import getSecurityManager
from AccessControl.unauthorized import Unauthorized
from AccessControl.Permissions import add_page_templates
from AccessControl.Permissions import add_user_folders
from App.special_dtml import DTMLFile
from zope.interface import implements

from OFS.Folder import Folder
from OFS.interfaces import IOrderedFolder
from OFS.OrderSupport import OrderSupport

manage_addOrderedFolderForm = DTMLFile('dtml/addOrderedFolder', globals())

def manage_addOrderedFolder(self, id, title='', createPublic=0, createUserF=0,
                            REQUEST=None):
    """Add a new ordered Folder object with id *id*.

    If the 'createPublic' and 'createUserF' parameters are set to any true
    value, an 'index_html' and a 'UserFolder' objects are created respectively
    in the new folder.
    """
    ob = OrderedFolder(id)
    ob.title = title
    self._setObject(id, ob)
    ob = self._getOb(id)

    checkPermission = getSecurityManager().checkPermission

    if createUserF:
        if not checkPermission(add_user_folders, ob):
            raise Unauthorized, (
                  'You are not authorized to add User Folders.'
                  )
        ob.manage_addUserFolder()

    if createPublic:
        if not checkPermission(add_page_templates, ob):
            raise Unauthorized, (
                  'You are not authorized to add Page Templates.'
                  )
        ob.manage_addProduct['PageTemplates'].manage_addPageTemplate(
            id='index_html', title='')

    if REQUEST:
        return self.manage_main(self, REQUEST, update_menu=1)


class OrderedFolder(OrderSupport, Folder):

    """ Extends the default Folder by order support.
    """
    implements(IOrderedFolder)
    meta_type='Folder (Ordered)'

    manage_options = ( OrderSupport.manage_options +
                       Folder.manage_options[1:] )
