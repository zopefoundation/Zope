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
__doc__='''Generic Database Adapter Package Registration

$Id$'''
__version__='$Revision: 1.16 $'[11:-2]

import Globals, os

classes=('DA.Connection',)
database_type='Gadfly'

class GadflyError(Exception):
    pass

class QueryError(GadflyError):
    pass

misc_={'conn':
       Globals.ImageFile('Shared/DC/ZRDB/www/DBAdapterFolder_icon.gif')}

for icon in ('table', 'view', 'stable', 'what',
             'field', 'text','bin','int','float',
             'date','time','datetime'):
    misc_[icon]=Globals.ImageFile('icons/%s.gif' % icon, globals())

meta_types=(
    {'name':'Z %s Database Connection' % database_type,
     'action':'manage_addZ%sConnectionForm' % database_type,
     },
    )

DA=None
def getDA():
    global DA
    if DA is None:
        home=Globals.package_home(globals())
        from gadfly import sqlwhere
        sqlwhere.filename="%s/gadfly/sql.mar" % home
        import DA
    return DA

getDA()

__module_aliases__=(
    ('Products.AqueductGadfly.DA', DA),
    )

def manage_addZGadflyConnectionForm(self, REQUEST, *args, **kw):
    " "
    DA=getDA()
    return DA.addConnectionForm(
        self, self, REQUEST,
        database_type=database_type,
        data_sources=DA.data_sources)

def manage_addZGadflyConnection(
    self, id, title, connection, check=None, REQUEST=None):
    " "
    return getDA().manage_addZGadflyConnection(
        self, id, title, connection, check, REQUEST)

methods={
    'manage_addZGadflyConnection':
    manage_addZGadflyConnection,
    'manage_addZGadflyConnectionForm':
    manage_addZGadflyConnectionForm,
    }

__ac_permissions__=(
    ('Add Z Gadfly Database Connections',
     ('manage_addZGadflyConnectionForm',
      'manage_addZGadflyConnection')),
    )


# from App.config import getConfiguration
# j=os.path.join
# d=j(getConfiguration().clienthome,'gadfly')
# if not os.path.exists(d):
#     os.mkdir(d)
#     os.mkdir(j(d,'demo'))
