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


$Id: __init__.py,v 1.1 1998/01/07 16:29:29 jim Exp $'''
__version__='$Revision: 1.1 $'[11:-2]
from ImageFile import ImageFile
import Aqueduct.Search, SQL

meta_types=(
    {'name':'Aqueduct SQL Database Method',
     'action':'manage_addAqueductSQLMethodForm',
     },
    {'name':'Aqueduct Search Interface',
     'action':'manage_addAqueductSearchForm'
     },
    )

methods={
    'manage_addAqueductSQLMethod': SQL.add,
    'manage_addAqueductSQLMethodForm': SQL.addForm,
    'SQLConnectionIDs': SQL.SQLConnectionIDs,

    
    'manage_addAqueductSearchForm': Aqueduct.Search.addForm,
    'manage_addAqueductSearch':     Aqueduct.Search.add,
    'aqueductQueryIds':             Aqueduct.Search.aqueductQueryIds,
    }

misc_={
    'icon': ImageFile('AqueductDA/www/DBAdapter_icon.gif'),
    }

############################################################################## 
#
# $Log: __init__.py,v $
# Revision 1.1  1998/01/07 16:29:29  jim
# Split out Database Methods
#
#
