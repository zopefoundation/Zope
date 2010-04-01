##############################################################################
#
# Copyright (c) 2001, 2002 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE
#
##############################################################################
__doc__='''BTreeFolder2 Product Initialization
$Id: __init__.py,v 1.4 2003/08/21 17:03:52 shane Exp $'''
__version__='$Revision: 1.4 $'[11:-2]

import BTreeFolder2

def initialize(context):

    context.registerClass(
        BTreeFolder2.BTreeFolder2,
        constructors=(BTreeFolder2.manage_addBTreeFolderForm,
                      BTreeFolder2.manage_addBTreeFolder),
        icon='btreefolder2.gif',
        )
