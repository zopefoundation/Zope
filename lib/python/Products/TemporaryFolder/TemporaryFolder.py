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
"""Mounted database support

$Id: TemporaryFolder.py,v 1.4 2001/11/28 15:51:08 matt Exp $"""
__version__='$Revision: 1.4 $'[11:-2]

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
