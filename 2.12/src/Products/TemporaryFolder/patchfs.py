# Utility program to patch Data.fs.in to include a temporary folder, browser
# id manager, and session data manager
############################################################################
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
############################################################################
import os
import sys

import Globals # for data
from ZODB import DB
from ZODB import FileStorage
import transaction

from Products.Sessions.BrowserIdManager import BrowserIdManager
from Products.Sessions.SessionDataManager import SessionDataManager
from Products.TemporaryFolder.TemporaryFolder import MountedTemporaryFolder

fs = FileStorage.FileStorage(os.path.join(Globals.data_dir,'Data.fs.in'))
db = DB(fs)
conn = db.open()
root = conn.root()
app = root['Application']

print "Patching Data.fs.in"

tf = MountedTemporaryFolder('temp_folder','Temporary Folder')
app._setObject('temp_folder', tf)

bid = BrowserIdManager('browser_id_manager', 'Browser Id Manager')
app._setObject('browser_id_manager', bid)

sdm = r.SessionDataManager('session_data_manager',
                           title='Session Data Manager',
                           path='/temp_folder/transient_container',
                           automatic=0)
app._setObject('session_data_manager', sdm)

app._p_changed = 1

transaction.commit()
