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

"""ZCatalog product"""

import ZCatalog, CatalogAwareness, CatalogPathAwareness
from Products.PluginIndexes.TextIndex import Vocabulary
from ZClasses import createZClassForBase

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

    context.registerClass(
        Vocabulary.Vocabulary,
        permission='Add Vocabularies',
        constructors=(Vocabulary.manage_addVocabularyForm,
                      Vocabulary.manage_addVocabulary),
        icon='www/Vocabulary.gif',
        )

    context.registerHelp()
    context.registerHelpTitle('Zope Help')
