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
$Id: __init__.py,v 1.22 1999/03/10 16:32:38 brian Exp $'''
__version__='$Revision: 1.22 $'[11:-2]

import Version, Draft, ZClasses
import OFS.Image, OFS.Folder, AccessControl.User
import OFS.DTMLMethod, OFS.DTMLDocument
from ImageFile import ImageFile

product_name='Zope built-in objects'

classes=('OFS.DTMLMethod.DTMLMethod', 'OFS.DTMLDocument.DTMLDocument',
         'Version.Version', 'OFS.Image.File', 'OFS.Image.Image',
         )
klasses=('OFS.Folder.Folder', 'AccessControl.User.UserFolder')

meta_types=(
    ZClasses.meta_types+
    (
        {'name': Draft.Draft.meta_type,
         'action':'manage_addPrincipiaDraftForm'},
        {'name': 'User Folder',
         'action':'manage_addUserFolder'},
        {'name': 'Version',
         'action':'manage_addVersionForm'},
        {'name': 'File',
         'action':'manage_addFileForm'},
        {'name': 'Image',
         'action':'manage_addImageForm'},
        {'name': 'Folder',
         'action':'manage_addFolderForm'},
        {'name': 'DTML Method',
         'action':'manage_addDTMLMethodForm'},
        {'name': 'DTML Document',
         'action':'manage_addDTMLDocumentForm'},
        )
    )


methods={
    # for bw compatibility
    'manage_addDocument': OFS.DTMLMethod.add,    
    'manage_addDTMLMethod': OFS.DTMLMethod.add,
    'manage_addDTMLMethodForm': OFS.DTMLMethod.addForm,
    'manage_addDTMLDocument': OFS.DTMLDocument.add,
    'manage_addDTMLDocumentForm': OFS.DTMLDocument.addForm,
    'manage_addFolder': OFS.Folder.manage_addFolder,
    'manage_addFolderForm': OFS.Folder.manage_addFolderForm,
    'manage_addImage': OFS.Image.manage_addImage,
    'manage_addImageForm': OFS.Image.manage_addImageForm,
    'manage_addFile': OFS.Image.manage_addFile,
    'manage_addFileForm': OFS.Image.manage_addFileForm,
    'manage_addVersionForm': Version.manage_addVersionForm,
    'manage_addVersion': Version.manage_addVersion,
    'manage_addUserFolder': AccessControl.User.manage_addUserFolder,
    'manage_addPrincipiaDraftForm': Draft.manage_addPrincipiaDraftForm,
    'manage_addPrincipiaDraft': Draft.manage_addPrincipiaDraft,
    }
methods.update(ZClasses.methods)

misc_={
    'version': ImageFile('images/version.gif', globals()),
    }
misc_.update(ZClasses.misc_)

__ac_permissions__=(
    ZClasses.__ac_permissions__+
    (
        ('Add Versions',('manage_addVersionForm', 'manage_addVersion')),
        ('Add Documents, Images, and Files',
         ('manage_addDTMLDocumentForm', 'manage_addDTMLDocument',
          'manage_addDTMLMethodForm', 'manage_addDTMLMethod',
          'manage_addFileForm', 'manage_addFile',
          'manage_addImageForm', 'manage_addImage')
         ),
        ('Add Folders',('manage_addFolderForm', 'manage_addFolder', 'MKCOL')),
        ('Add User Folders',('manage_addUserFolder',)),
        ('Change DTML Documents', ()),
        ('Change DTML Methods', ()),
        ('Change Images and Files', ()),
        ('Change proxy roles', ()),
        ('Change Versions', ()),
        ('Join/leave Versions', ()),
        ('Save/discard Version changes', ()),
        ('Manage users', ()),
        #('Add DraftFolders',
        # ('manage_addDraftFolderForm', 'manage_addDraftFolder')),
        )
    )
