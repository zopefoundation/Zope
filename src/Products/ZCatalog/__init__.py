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

"""ZCatalog product"""

import ZCatalog

def initialize(context):
    context.registerClass(
        ZCatalog.ZCatalog,
        permission='Add ZCatalogs',
        constructors=(ZCatalog.manage_addZCatalogForm,
                      ZCatalog.manage_addZCatalog),
        icon='www/ZCatalog.gif',
        )


    context.registerHelp()
    context.registerHelpTitle('Zope Help')
