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
"""
Temporary Folder initialization routines
"""

import ZODB # for testrunner to be happy

# we import this so that config files can use the shorter name,
# it's not used directly
from TemporaryFolder import SimpleTemporaryContainer as TemporaryContainer

def initialize(context):
    import TemporaryFolder
    context.registerClass(
        TemporaryFolder.MountedTemporaryFolder,
        permission=TemporaryFolder.ADD_TEMPORARY_FOLDER_PERM,
        icon='www/tempfolder.gif',
        meta_type='Temporary Folder',
        constructors=(TemporaryFolder.constructTemporaryFolderForm,
                      TemporaryFolder.constructTemporaryFolder),
        visibility=0 # dont show this in the add list for 2.7+ (use dbtab)
        )

    context.registerHelp()
    context.registerHelpTitle('Zope Help')
