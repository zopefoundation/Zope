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


$Id: __init__.py,v 1.4 1998/05/11 15:00:46 jim Exp $'''
__version__='$Revision: 1.4 $'[11:-2]
from ImageFile import ImageFile
import Aqueduct.Search, SQL

classes=('SQL.SQL',)

meta_types=(
    {'name':'Aqueduct SQL Database Method',
     'action':'manage_addAqueductSQLMethodForm',
     },
    {'name':'Aqueduct Search Interface',
     'action':'manage_addAqueductSearchForm'
     },
    )

methods={
    'manage_addAqueductSQLMethod': SQL.manage_addAqueductSQLMethod,
    'manage_addAqueductSQLMethodForm': SQL.manage_addAqueductSQLMethodForm,
    'SQLConnectionIDs': SQL.SQLConnectionIDs,

    
    'manage_addAqueductSearchForm': Aqueduct.Search.addForm,
    'manage_addAqueductSearch':     Aqueduct.Search.add,
    'aqueductQueryIds':             Aqueduct.Search.aqueductQueryIds,
    }

misc_={
    'icon': ImageFile('AqueductDA/www/DBAdapter_icon.gif'),
    }

__ac_permissions__=(
    ('Add Database Methods',
     ('manage_addAqueductSQLMethodForm', 'manage_addAqueductSQLMethod')),
    ('Open/Close Database Connections',   ()),
    ('Change Database Methods',           ()),
    ('Change Database Connections',           ()),
    ('Use Database Methods', ()),
    )

############################################################################## 
#
# $Log: __init__.py,v $
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
