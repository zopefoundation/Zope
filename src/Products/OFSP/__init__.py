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
__doc__='''Object system core
$Id$'''
__version__='$Revision: 1.38 $'[11:-2]

import OFS.Image, OFS.Folder, AccessControl.User
import OFS.DTMLMethod, OFS.DTMLDocument, OFS.PropertySheets
import OFS.OrderedFolder

from AccessControl.Permissions import add_documents_images_and_files
from AccessControl.Permissions import add_folders

def initialize(context):

    context.registerClass(
        OFS.DTMLMethod.DTMLMethod,
        permission=add_documents_images_and_files,
        constructors=(OFS.DTMLMethod.addForm, OFS.DTMLMethod.addDTMLMethod,),
        icon='images/dtmlmethod.gif',
        legacy=(
            ('manage_addDocument', OFS.DTMLMethod.addDTMLMethod),
            ('manage_addDTMLMethod', OFS.DTMLMethod.addDTMLMethod),
            )
        )

    context.registerClass(
        OFS.DTMLDocument.DTMLDocument,
        permission=add_documents_images_and_files,
        constructors=(OFS.DTMLDocument.addForm,
                      OFS.DTMLDocument.addDTMLDocument),
        icon='images/dtmldoc.gif',
        legacy=(('manage_addDTMLDocument', OFS.DTMLDocument.addDTMLDocument),),
        )

    context.registerClass(
        OFS.Image.Image,
        permission=add_documents_images_and_files,
        constructors=(('imageAdd',OFS.Image.manage_addImageForm),
                      OFS.Image.manage_addImage),
        icon='images/Image_icon.gif',
        legacy=(OFS.Image.manage_addImage,),
        )

    context.registerClass(
        OFS.Image.File,
        permission=add_documents_images_and_files,
        constructors=(('fileAdd',OFS.Image.manage_addFileForm),
                      OFS.Image.manage_addFile),
        icon='images/File_icon.gif',
        legacy=(OFS.Image.manage_addFile,),
        )

    context.registerClass(
        OFS.Folder.Folder,
        constructors=(OFS.Folder.manage_addFolderForm,
                      OFS.Folder.manage_addFolder),
        icon='images/Folder_icon.gif',
        legacy=(OFS.Folder.manage_addFolder,),
        )

    context.registerClass(
        OFS.OrderedFolder.OrderedFolder,
        permission=add_folders,
        constructors=(OFS.OrderedFolder.manage_addOrderedFolderForm,
                      OFS.OrderedFolder.manage_addOrderedFolder),
        icon='images/Folder_icon.gif',
        legacy=(OFS.OrderedFolder.manage_addOrderedFolder,),
        )

    context.registerClass(
        AccessControl.User.UserFolder,
        constructors=(AccessControl.User.manage_addUserFolder,),
        icon='images/UserFolder_icon.gif',
        legacy=(AccessControl.User.manage_addUserFolder,),
        )

    context.registerHelp()
    context.registerHelpTitle('Zope Help')
