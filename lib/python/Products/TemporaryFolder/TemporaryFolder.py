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
"""Mounted database support

$Id: TemporaryFolder.py,v 1.3 2001/11/17 15:46:52 chrism Exp $"""
__version__='$Revision: 1.3 $'[11:-2]

import Globals
from Globals import HTMLFile
from ZODB.Mount import MountPoint
import string
import OFS
import os, os.path

from ZODB.DB import DB
from TemporaryStorage import TemporaryStorage
from LowConflictConnection import LowConflictConnection

ADD_TEMPORARY_FOLDER_PERM="Add Temporary Folder"

    
def constructTemporaryFolder(self, id, title=None, REQUEST=None):
    """ """
    ms = MountedTemporaryFolder(id, title)
    self._setObject(id, ms)
    if REQUEST is not None:
        return self.manage_main(self, REQUEST, update_menu=1)


constructTemporaryFolderForm=HTMLFile('dtml/addTemporaryFolder', globals())


class MountedTemporaryFolder(MountPoint, OFS.SimpleItem.Item):
    """
    A mounted RAM database with a basic interface for displaying the
    reason the database did not connect.
    """
    icon = 'p_/broken'
    manage_options = ({'label':'Traceback', 'action':'manage_traceback'},)
    meta_type = 'Broken Temporary Folder'
    
    def __init__(self, id, title='', params=None):
        self.id = str(id)
        self.title = title
        MountPoint.__init__(self, path='/') # Eep

    manage_traceback = Globals.DTMLFile('dtml/mountfail', globals())

    def _createDB(self, db=None): # huh?  db=db was original
        """ Create a mounted RAM database """
        db = DB(TemporaryStorage())
        db.klass = LowConflictConnection
        return db
    
    def _getMountRoot(self, root):
        sdc = root.get('folder', None)
        if sdc is None:
            sdc = root['folder'] = OFS.Folder.Folder()
            self._populate(sdc, root)

        return sdc
    
    def mount_error_(self):
        return self._v_connect_error

    def _populate(self, folder, root):
        # Set up our folder object
        folder.id = self.id                     # be a chameleon
        folder.title = self.title
        folder.icon = "misc_/TemporaryFolder/tempfolder.gif"
        s=folder.manage_options[1:]
        folder.manage_options = (
            {'label':'Contents', 'action':'manage_main',
             'help':('TemporaryFolder','TemporaryFolder.stx')},
            )+s
