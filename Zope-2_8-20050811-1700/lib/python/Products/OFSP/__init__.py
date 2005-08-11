##############################################################################
#
# Copyright (c) 2001 Zope Corporation and Contributors. All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
__doc__='''Object system core
$Id$'''
__version__='$Revision: 1.38 $'[11:-2]

import Version, OFS.Image, OFS.Folder, AccessControl.User
import OFS.DTMLMethod, OFS.DTMLDocument, OFS.PropertySheets
import OFS.OrderedFolder
import ZClasses.ObjectManager

from AccessControl.Permissions import add_documents_images_and_files
from AccessControl.Permissions import add_folders
from ZClasses import createZClassForBase
from ImageFile import ImageFile

createZClassForBase( OFS.DTMLMethod.DTMLMethod, globals()
                   , 'ZDTMLMethod', 'DTML Method' )
createZClassForBase( OFS.DTMLDocument.DTMLDocument, globals()
                   , 'ZDTMLDocument', 'DTML Document' )
createZClassForBase( OFS.Image.Image, globals()
                   , 'ZImage', 'Image' )
createZClassForBase( OFS.Image.File, globals()
                   , 'ZFile', 'File' )
createZClassForBase( OFS.Folder.Folder, globals()
                   , 'ZFolder', 'Folder' )
createZClassForBase( OFS.OrderedFolder.OrderedFolder, globals() )
createZClassForBase( AccessControl.User.UserFolder, globals()
                   , 'ZUserFolder', 'User Folder' )
createZClassForBase( AccessControl.User.User, globals()
                   , 'ZUser', 'User' )

misc_={
    'version.gif':ImageFile('images/version.gif', globals())
    }

# This is the new way to initialize products.  It is hoped
# that this more direct mechanism will be more understandable.
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

    ## Those both classes are relicts. We only withdraw them from the Add menu.
    ## This way people will stop using them. They are undocumented anyway. 
    ## People also have the chance to softly migrate their data and stop using the
    ## versions they still use.

    #context.registerClass(
    #    Version.Version,
    #    constructors=(Version.manage_addVersionForm,
    #                  Version.manage_addVersion),
    #    icon='images/version.gif'
    #    )

    #context.registerClass(
    #    Draft.Draft,
    #    constructors=(Draft.manage_addPrincipiaDraftForm,
    #             Draft.manage_addPrincipiaDraft),
    #    icon='images/draft.gif'
    #    )

    context.registerZClass(ZClasses.ObjectManager.ZObjectManager)

    context.registerHelp()
    context.registerHelpTitle('Zope Help')
