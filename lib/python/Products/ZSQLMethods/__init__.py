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


$Id: __init__.py,v 1.6 1998/12/15 21:10:31 jim Exp $'''
__version__='$Revision: 1.6 $'[11:-2]
from ImageFile import ImageFile
import Shared.DC.ZRDB.Search, SQL

classes=('SQL.SQL',)

meta_types=(
    {'name':SQL.SQL.meta_type,
     'action':'manage_addZSQLMethodForm',
     },
    {'name':'Zope Search Interface',
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

############################################################################## 
#
# $Log: __init__.py,v $
# Revision 1.6  1998/12/15 21:10:31  jim
# first Zope
#
# Revision 1.5  1998/12/02 12:11:49  jim
# new names, esp for Aqueduct
#
# Revision 1.4  1998/05/11 15:00:46  jim
# Updated permissions.
#
# Revision 1.3  1998/02/23 19:00:31  jim
# updated permissions
#
# Revision 1.2  1998/01/29 16:29:47  brian
# Added eval support
#
# Revision 1.1  1998/01/07 16:29:29  jim
# Split out Database Methods
#
#
