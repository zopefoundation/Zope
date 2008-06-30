##############################################################################
#
# Copyright (c) 2002 Zope Corporation and Contributors. All Rights Reserved.
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

import ZCatalog, CatalogAwareness, CatalogPathAwareness

# BBB: ZClasses are deprecated but we don't want the warning to appear here
import warnings
warnings.filterwarnings('ignore', message='^ZClasses', append=1)
try:
    from ZClasses import createZClassForBase
finally:
    del warnings.filters[-1]
    try:
        del __warningregistry__
    except NameError:
        pass

createZClassForBase( ZCatalog.ZCatalog , globals()
                   , 'ZCatalogBase', 'ZCatalog' )
createZClassForBase( CatalogAwareness.CatalogAware, globals()
                   , 'CatalogAwareBase', 'CatalogAware' )
createZClassForBase( CatalogPathAwareness.CatalogPathAware, globals()
                   , 'CatalogPathAwareBase', 'CatalogPathAware' )

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
