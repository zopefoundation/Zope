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

$Id: __init__.py,v 1.6 2002/08/14 22:25:13 mj Exp $
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
                      TemporaryFolder.constructTemporaryFolder)
        )

    context.registerHelp()
    context.registerHelpTitle('Zope Help')
