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
"""
Temporary Folder initialization routines

$Id: __init__.py,v 1.7 2003/07/20 16:18:26 chrism Exp $
"""

import ZODB # for testrunner to be happy

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
