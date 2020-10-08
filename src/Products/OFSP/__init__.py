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

import OFS.DTMLDocument
import OFS.DTMLMethod
import OFS.Folder
import OFS.Image
import OFS.OrderedFolder
import OFS.PropertySheets
import OFS.userfolder
from AccessControl.Permissions import add_documents_images_and_files
from AccessControl.Permissions import add_folders


def initialize(context):
    context.registerClass(
        OFS.DTMLMethod.DTMLMethod,
        permission=add_documents_images_and_files,
        constructors=(OFS.DTMLMethod.addForm, OFS.DTMLMethod.addDTMLMethod,),
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
        legacy=(('manage_addDTMLDocument', OFS.DTMLDocument.addDTMLDocument),),
    )

    context.registerClass(
        OFS.Image.Image,
        permission=add_documents_images_and_files,
        constructors=(('imageAdd', OFS.Image.manage_addImageForm),
                      OFS.Image.manage_addImage),
        legacy=(OFS.Image.manage_addImage,),
    )

    context.registerClass(
        OFS.Image.File,
        permission=add_documents_images_and_files,
        constructors=(('fileAdd', OFS.Image.manage_addFileForm),
                      OFS.Image.manage_addFile),
        legacy=(OFS.Image.manage_addFile,),
    )

    context.registerClass(
        OFS.Folder.Folder,
        constructors=(OFS.Folder.manage_addFolderForm,
                      OFS.Folder.manage_addFolder),
        legacy=(OFS.Folder.manage_addFolder,),
    )

    context.registerClass(
        OFS.OrderedFolder.OrderedFolder,
        permission=add_folders,
        constructors=(OFS.OrderedFolder.manage_addOrderedFolderForm,
                      OFS.OrderedFolder.manage_addOrderedFolder),
        legacy=(OFS.OrderedFolder.manage_addOrderedFolder,),
    )

    context.registerClass(
        OFS.userfolder.UserFolder,
        constructors=(OFS.userfolder.manage_addUserFolder,),
        legacy=(OFS.userfolder.manage_addUserFolder,),
    )
