#!/bin/env python
############################################################################## 
#
#     Copyright 
#
#       Copyright 1996 Digital Creations, L.C., 910 Princess Anne
#       Street, Suite 300, Fredericksburg, Virginia 22401 U.S.A. All
#       rights reserved.
#
############################################################################## 
__doc__='''SQL Method Product


$Id: __init__.py,v 1.8 1998/12/16 15:04:42 jim Exp $'''
__version__='$Revision: 1.8 $'[11:-2]
from ImageFile import ImageFile
import Shared.DC.ZRDB.Search, SQL

classes=('SQL.SQL',)

meta_types=(
    {'name':SQL.SQL.meta_type,
     'action':'manage_addZSQLMethodForm',
     },
    {'name':'Z Search Interface',
     'action':'manage_addZSearchForm'
     },
    )

methods={
    'manage_addZSQLMethod': SQL.manage_addZSQLMethod,
    'manage_addZSQLMethodForm': SQL.manage_addZSQLMethodForm,
    'SQLConnectionIDs': SQL.SQLConnectionIDs,

    
    'manage_addZSearchForm': Shared.DC.ZRDB.Search.addForm,
    'manage_addZSearch':     Shared.DC.ZRDB.Search.add,
    'ZQueryIds':             Shared.DC.ZRDB.Search.ZQueryIds,
    }

misc_={
    'icon': ImageFile('Shared/DC/ZRDB/www/DBAdapter_icon.gif'),
    }

__ac_permissions__=(
    ('Add Database Methods',
     ('manage_addZSQLMethodForm', 'manage_addZSQLMethod')),
    ('Open/Close Database Connections',   ()),
    ('Change Database Methods',           ()),
    ('Change Database Connections',           ()),
    ('Use Database Methods', ()),
    )
