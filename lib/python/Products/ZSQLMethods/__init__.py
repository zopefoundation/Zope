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
__doc__='''SQL Method Product


$Id$'''
__version__='$Revision: 1.18 $'[11:-2]
import Shared.DC.ZRDB.Search, Shared.DC.ZRDB.Aqueduct, SQL
import Shared.DC.ZRDB.RDB
import Shared.DC.ZRDB.sqlvar, Shared.DC.ZRDB.sqlgroup, Shared.DC.ZRDB.sqltest


# This is the new way to initialize products.  It is hoped
# that this more direct mechanism will be more understandable.
def initialize(context):

    context.registerClass(
        SQL.SQL,
        permission='Add Database Methods',
        constructors=(SQL.manage_addZSQLMethodForm, SQL.manage_addZSQLMethod),
        icon='sqlmethod.gif',
        )

    context.registerClass(
        meta_type='Z Search Interface',
        permission='Add Documents, Images, and Files',
        constructors=(Shared.DC.ZRDB.Search.addForm,
                      Shared.DC.ZRDB.Search.manage_addZSearch),
        )

    context.registerHelp()
    context.registerHelpTitle('Zope Help')

methods={
    # We still need this one, at least for now, for both editing and
    # adding.  Ugh.
    'SQLConnectionIDs': SQL.SQLConnectionIDs,

    # Oh please!
    'ZQueryIds':             Shared.DC.ZRDB.Search.ZQueryIds,
    }

__ac_permissions__=(
    # Ugh.  We should get rid of this, but we'll have to revisit connections
    ('Open/Close Database Connections',   ()),
    )

__module_aliases__=(
    ('Products.AqueductSQLMethods','Products.ZSQLMethods'),
    ('Aqueduct', Shared.DC.ZRDB),
    ('AqueductDA', Shared.DC.ZRDB),
    ('Products.AqueductSQLMethods.SQL', SQL),
    ('Aqueduct.Aqueduct', Shared.DC.ZRDB.Aqueduct),
    ('AqueductDA.DA',     Shared.DC.ZRDB.DA),
    ('Aqueduct.RDB',     Shared.DC.ZRDB.RDB),
    ('AqueductDA.sqlvar',     Shared.DC.ZRDB.sqlvar),
    ('AqueductDA.sqltest',     Shared.DC.ZRDB.sqltest),
    ('AqueductDA.sqlgroup',     Shared.DC.ZRDB.sqlgroup),
    )
