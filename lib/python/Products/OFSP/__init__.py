##############################################################################
# 
# Zope Public License (ZPL) Version 1.0
# -------------------------------------
# 
# Copyright (c) Digital Creations.  All rights reserved.
# 
# This license has been certified as Open Source(tm).
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
# 
# 1. Redistributions in source code must retain the above copyright
#    notice, this list of conditions, and the following disclaimer.
# 
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions, and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
# 
# 3. Digital Creations requests that attribution be given to Zope
#    in any manner possible. Zope includes a "Powered by Zope"
#    button that is installed by default. While it is not a license
#    violation to remove this button, it is requested that the
#    attribution remain. A significant investment has been put
#    into Zope, and this effort will continue if the Zope community
#    continues to grow. This is one way to assure that growth.
# 
# 4. All advertising materials and documentation mentioning
#    features derived from or use of this software must display
#    the following acknowledgement:
# 
#      "This product includes software developed by Digital Creations
#      for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
#    In the event that the product being advertised includes an
#    intact Zope distribution (with copyright and license included)
#    then this clause is waived.
# 
# 5. Names associated with Zope or Digital Creations must not be used to
#    endorse or promote products derived from this software without
#    prior written permission from Digital Creations.
# 
# 6. Modified redistributions of any form whatsoever must retain
#    the following acknowledgment:
# 
#      "This product includes software developed by Digital Creations
#      for use in the Z Object Publishing Environment
#      (http://www.zope.org/)."
# 
#    Intact (re-)distributions of any official Zope release do not
#    require an external acknowledgement.
# 
# 7. Modifications are encouraged but must be packaged separately as
#    patches to official Zope releases.  Distributions that do not
#    clearly separate the patches from the original work must be clearly
#    labeled as unofficial distributions.  Modifications which do not
#    carry the name Zope may be packaged in any form, as long as they
#    conform to all of the clauses above.
# 
# 
# Disclaimer
# 
#   THIS SOFTWARE IS PROVIDED BY DIGITAL CREATIONS ``AS IS'' AND ANY
#   EXPRESSED OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
#   IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
#   PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL DIGITAL CREATIONS OR ITS
#   CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
#   SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
#   LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF
#   USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#   ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
#   OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT
#   OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
#   SUCH DAMAGE.
# 
# 
# This software consists of contributions made by Digital Creations and
# many individuals on behalf of Digital Creations.  Specific
# attributions are listed in the accompanying credits file.
# 
##############################################################################
__doc__='''Base Principia
$Id: __init__.py,v 1.31 1999/08/11 13:43:27 jim Exp $'''
__version__='$Revision: 1.31 $'[11:-2]

import Version, OFS.Image, OFS.Folder, AccessControl.User
import OFS.DTMLMethod, OFS.DTMLDocument, ZClasses.ObjectManager

# This is the new way to initialize products.  It is hoped
# that this more direct mechanism will be more understandable.
def initialize(context):

    perm='Add Documents, Images, and Files'

    context.registerClass(
        OFS.DTMLMethod.DTMLMethod,
        permission=perm,
        constructors=(OFS.DTMLMethod.addForm, OFS.DTMLMethod.addDTMLMethod,),
        icon='images/dtmlmethod.gif',
        legacy=(
            ('manage_addDocument', OFS.DTMLMethod.addDTMLMethod),
            ('manage_addDTMLMethod', OFS.DTMLMethod.addDTMLMethod),
            )
        )
    context.registerBaseClass(OFS.DTMLMethod.DTMLMethod, 'DTML Method')


    context.registerClass(
        OFS.DTMLDocument.DTMLDocument,
        permission=perm,
        constructors=(OFS.DTMLDocument.addForm,
                      OFS.DTMLDocument.addDTMLDocument),
        icon='images/dtmldoc.gif',
        legacy=(('manage_addDTMLDocument', OFS.DTMLDocument.addDTMLDocument),),
        )
    context.registerBaseClass(OFS.DTMLDocument.DTMLDocument, 'DTML Document')


    context.registerClass(
        OFS.Image.Image,
        permission=perm,
        constructors=(('imageAdd',OFS.Image.manage_addImageForm),
                      OFS.Image.manage_addImage),
        icon='images/Image_icon.gif',
        legacy=(OFS.Image.manage_addImage,),
        )
    context.registerBaseClass(OFS.Image.Image, 'Image')


    context.registerClass(
        OFS.Image.File,
        permission=perm,
        constructors=(('fileAdd',OFS.Image.manage_addFileForm),
                      OFS.Image.manage_addFile),
        icon='images/File_icon.gif',
        legacy=(OFS.Image.manage_addFile,),
        )
    context.registerBaseClass(OFS.Image.File, 'File')
    
    context.registerClass(
        OFS.Folder.Folder,
        constructors=(OFS.Folder.manage_addFolderForm,
                      OFS.Folder.manage_addFolder),
        icon='images/Folder_icon.gif',
        legacy=(OFS.Folder.manage_addFolder,),
        )
    context.registerBaseClass(OFS.Folder.Folder, 'Folder')
    

    context.registerClass(
        AccessControl.User.UserFolder,
        constructors=(AccessControl.User.manage_addUserFolder,),
        icon='images/UserFolder_icon.gif',
        legacy=(AccessControl.User.manage_addUserFolder,),
        )

    context.registerBaseClass(AccessControl.User.UserFolder, 'User Folder')
    context.registerBaseClass(AccessControl.User.User)



    context.registerClass(
        Version.Version,
        constructors=(Version.manage_addVersionForm,
                      Version.manage_addVersion),
        icon='images/version.gif'
        )

    #context.registerClass(
    #    Draft.Draft,
    #    constructors=(Draft.manage_addPrincipiaDraftForm,
    #             Draft.manage_addPrincipiaDraft),
    #    icon='images/draft.gif'
    #    )

    context.registerZClass(ZClasses.ObjectManager.ZObjectManager)
                           
